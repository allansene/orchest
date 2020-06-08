import React from 'react';
import PipelineView from "./PipelineView";
import { MDCTabBar } from '@material/tab-bar';
import { MDCTextField } from "@material/textfield";
import { MDCRipple } from '@material/ripple';
import { makeRequest } from "../utils/all";
import MDCButtonReact from '../mdc-components/MDCButtonReact';
import MDCTabBarReact from '../mdc-components/MDCTabBarReact';


class PipelineSettingsView extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            active_tab_index: 0
        };
    }

    initComponent() {
        this.initiateMDCComponents()
    }

    componentDidMount() {

        makeRequest("GET", "/async/pipelines/json/get/" + this.props.pipeline.uuid).then((response) => {
            let result = JSON.parse(response);

            if (result.success) {

                let pipelineJson = JSON.parse(result['pipeline_json']);
                this.setState({ "pipelineJson": pipelineJson });

                this.initComponent();

            } else {
                console.warn("Could not load pipeline.json");
                console.log(result);
            }
        });

    }

    initiateMDCComponents() {
        if (this.refs.pipelineNameField) {
            this.pipelineNameField = new MDCTextField(this.refs.pipelineNameField);
            this.pipelineNameField.value = this.state.pipelineJson.name;
            this.pipelineNameField.focus();
        }
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        this.initiateMDCComponents()
    }

    closeSettings() {
        orchest.loadView(PipelineView, { "pipeline": this.props.pipeline });
    }

    saveGeneralForm(e) {
        e.preventDefault();

        // new name
        let pipelineName = this.pipelineNameField.value;

        let formData = new FormData();
        formData.append("name", pipelineName);

        // perform POST to save
        makeRequest("POST", "/async/pipelines/rename/" + this.props.pipeline.uuid, {type: 'FormData', content: formData}).then((response) => {
            
            let json = JSON.parse(response);
            console.log(json)
            if (json.success === true) {
                // orchest.loadView(PipelineSettingsView, {name: pipelineName, uuid: this.props.uuid});

                // TODO: evaluate: should we close PipelineSettingsView on save?
                orchest.loadView(PipelineView, { "pipeline": this.props.pipeline });
            }
        })
    }

    render() {

        return <div className={"view-page view-pipeline-settings"}>
            <h2>Pipeline settings</h2>

            <MDCTabBarReact items={["General"]} icons={["subject"]} />

            <div className={"tab-content"}>
                {(() => {
                    switch (this.state.active_tab_index) {
                        case 0:
                            return <div>
                                <form>
                                    <div>
                                        <div ref={"pipelineNameField"} className="mdc-text-field">
                                            <input type="text" id="my-text-field" onChange={this.stub} className="mdc-text-field__input" />
                                            <label className="mdc-floating-label" htmlFor="my-text-field">Pipeline name</label>
                                            <div className="mdc-line-ripple"></div>
                                        </div>
                                    </div>

                                    <MDCButtonReact label="save" onClick={this.saveGeneralForm.bind(this)} />

                                </form>
                            </div>;
                    }
                })()}
            </div>


            <MDCButtonReact classNames={['close-button']} icon="close" onClick={this.closeSettings.bind(this)} />
        </div>;
    }
}

export default PipelineSettingsView;