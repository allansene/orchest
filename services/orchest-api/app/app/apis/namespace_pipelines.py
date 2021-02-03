"""API endpoint to manage pipelines.

Despite the fact that the orchest api has no model related to a
pipeline, a good amount of other models depend on such a concept.
"""
from flask import abort, request
from flask.globals import current_app
from flask_restx import Namespace, Resource

import app.models as models
from _orchest.internals.two_phase_executor import TwoPhaseExecutor, TwoPhaseFunction
from app import schema
from app.apis.namespace_runs import AbortPipelineRun
from app.apis.namespace_sessions import StopInteractiveSession
from app.connections import db
from app.utils import register_schema

api = Namespace("pipelines", description="Managing pipelines")
api = register_schema(api)


@api.route("/")
class PipelineList(Resource):
    @api.doc("get_pipelines")
    @api.marshal_with(schema.pipelines)
    def get(self):
        """Get all pipelines."""

        pipelines = models.Pipeline.query.all()
        return {"pipelines": [pip.__dict__ for pip in pipelines]}, 200

    @api.doc("create_pipeline")
    @api.expect(schema.pipeline)
    @api.marshal_with(schema.pipeline)
    def post(self):
        """Create a new pipeline."""
        try:
            pipeline = request.get_json()
            pipeline["env_variables"] = pipeline.get("env_variables", {})
            db.session.add(models.Pipeline(**pipeline))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return {"message": "Pipeline creation failed."}, 500
        return pipeline, 201


@api.route("/<string:project_uuid>/<string:pipeline_uuid>")
@api.param("project_uuid", "uuid of the project")
@api.param("pipeline_uuid", "uuid of the pipeline")
class Pipeline(Resource):
    @api.doc("get_pipeline")
    @api.marshal_with(schema.pipeline, code=200)
    def get(self, project_uuid, pipeline_uuid):
        """Fetches a pipeline given the project and pipeline uuid."""
        pipeline = models.Pipeline.query.filter_by(
            project_uuid=project_uuid, uuid=pipeline_uuid
        ).one_or_none()
        if pipeline is None:
            abort(404, "Pipeline not found.")
        return pipeline

    @api.expect(schema.pipeline_update)
    @api.doc("update_pipeline")
    def put(self, project_uuid, pipeline_uuid):
        """Update a pipeline."""

        try:
            models.Pipeline.query.filter_by(
                project_uuid=project_uuid, uuid=pipeline_uuid
            ).update(request.get_json())
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return {"message": "Failed update operation."}, 500

        return {"message": "Pipeline was updated successfully."}, 200

    @api.doc("delete_pipeline")
    @api.response(200, "Pipeline cleaned up")
    def delete(self, project_uuid, pipeline_uuid):
        """Delete a pipeline.

        Any session, run, job related to the pipeline is stopped
        and removed from the db.
        """
        try:
            with TwoPhaseExecutor(db.session) as tpe:
                DeletePipeline(tpe).transaction(project_uuid, pipeline_uuid)

        except Exception as e:
            return {"message": str(e)}, 500

        return {"message": "Pipeline deletion was successful."}, 200


class DeletePipeline(TwoPhaseFunction):
    """Delete a pipeline and all related entities.


    Any session or run related to the pipeline is stopped and removed
    from the db.
    """

    def _transaction(self, project_uuid: str, pipeline_uuid: str):
        # Any interactive run related to the pipeline is stopped if
        # necessary, then deleted.
        interactive_runs = (
            models.InteractivePipelineRun.query.filter_by(
                project_uuid=project_uuid, pipeline_uuid=pipeline_uuid
            )
            .filter(models.InteractivePipelineRun.status.in_(["PENDING", "STARTED"]))
            .all()
        )
        for run in interactive_runs:
            AbortPipelineRun(self.tpe).transaction(run.uuid)

            # Will delete cascade: run pipeline step, interactive run
            # image mapping,
            db.session.delete(run)

        # Stop any interactive session related to the pipeline.
        StopInteractiveSession(self.tpe).transaction(project_uuid, pipeline_uuid)

        # Note that we do not delete the pipeline from the db since we
        # are not deleting jobs related to the pipeline. Deleting the
        # pipeline would delete cascade jobs.

    def _collateral(self):
        pass
