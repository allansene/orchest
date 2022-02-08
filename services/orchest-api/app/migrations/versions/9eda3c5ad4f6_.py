"""empty message

Revision ID: 9eda3c5ad4f6
Revises: 0fd04e9ab2c3
Create Date: 2022-01-13 12:05:33.145001

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9eda3c5ad4f6"
down_revision = "0fd04e9ab2c3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pipeline_runs",
        sa.Column(
            "parameters_text_search_values",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("pipeline_runs", "parameters_text_search_values")
    # ### end Alembic commands ###