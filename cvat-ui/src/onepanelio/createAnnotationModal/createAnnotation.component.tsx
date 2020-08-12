// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';
import React from 'react';

import {
    Row,
    Col,
    Modal,
    Select,
    notification,
    Input,
    Button,
    Spin
} from 'antd';

const { TextArea } = Input;

import getCore from 'cvat-core-wrapper';
import { getMachineNames, getModelNames } from './createAnnotation.constant';
import {
    WorkflowTemplates, WorkflowParameters, NodePoolParameters,
    DumpFormats, NodePoolResponse, ExecuteWorkflowPayload, DefaultSysParams
} from './interfaces';

interface Props {
    visible: boolean;
    taskInstance: any;
    baseModelList: string[];
    workflowTemplates: WorkflowTemplates[];
    fetchingWorkflowTemplates: boolean;
    closeDialog(): void;
    getBaseModelList(taskInstance: any, modelType: string): void;
}

interface State {
    isLoading: boolean,
    executingAnnotation: boolean;
    getingParameters: boolean;
    workflowTemplate: WorkflowTemplates | undefined;
    allWorkflowParameters: WorkflowParameters[];
    selectedWorkflowParam: any;
    allSysNodePools: NodePoolResponse;
    selectedNodePool: NodePoolParameters | undefined;
    allDumpFormats: DumpFormats[];
    selectedDumpFormat: DumpFormats | undefined;
    defaultSysNodePoolVal: string;
    sysOutputPath: DefaultSysParams;
    sysAnnotationPath: DefaultSysParams;
    allSysFinetuneCheckpoint: DefaultSysParams;
    selectedFinetuneCheckpoint: string | null;
    showDumpFormatHint: boolean;
}

interface CreateAnnotationSubmitData {
    project_uid: string;
    machine_type: string;
    arguments: string;
    ref_model: string;
    dump_format: string;
    base_url: string;
    base_model: string;
}

const core = getCore();

const models = getModelNames()

const machines = getMachineNames();

const InitialState = {
    isLoading: true,
    executingAnnotation: false,
    getingParameters: false,
    workflowTemplate: {
        uid: "",
        version: ""
    },
    allWorkflowParameters: [],
    selectedWorkflowParam: {},
    allSysNodePools: {
        label: "",
        options: [],
        hint: null,
        display_name: ""
    },
    selectedNodePool: undefined,
    allDumpFormats: [],
    selectedDumpFormat: undefined,
    defaultSysNodePoolVal: "",
    sysOutputPath: {
        hint: null,
        display_name: "",
        value: ""
    },
    sysAnnotationPath: {
        hint: null,
        display_name: "",
        value: ""
    },
    allSysFinetuneCheckpoint: {
        options: [],
        hint: null,
        display_name: ""
    },
    selectedFinetuneCheckpoint: null,
    showDumpFormatHint: false,
}

export default class ModelNewAnnotationModalComponent extends React.PureComponent<Props, State> {
    public constructor(props: Props) {
        super(props);
        this.state = InitialState;
    }

    public componentDidUpdate(prevProps: Props, prevState: State): void {
        const {
            visible,
        } = this.props;


        if (!prevProps.visible && visible) {
            this.setState(InitialState);
        }
    }

    private showErrorNotification = (error: any): void => {
        notification.error({
            message: 'Execute Workflow failed.',
            description: `Execute workflow failed (Error code: ${error.code}). Please try again later`,
            duration: 5,
        });
    }

    private async handleSubmit(): Promise<void> {
        const {
            taskInstance,
            closeDialog
        } = this.props;

        const baseUrl: string = core.config.backendAPI.slice(0, -7);

        let countResp = await core.server.request(`${baseUrl}/onepanelio/get_object_counts/${taskInstance.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const {
            shapes,
            tracks,
        } = countResp;

        if (tracks.length) {
            return this.onExecuteWorkflow();
        }

        this.onSubmitNotifications(shapes.length);
    }

    private onSubmitNotifications(count: number): void {
        const {
            closeDialog,
        } = this.props;
        const key = `open${Date.now()}`;
        const btn = (
            <div className="cvat-new-anno-modal-submit-notification-btn">
                <Button
                    type="primary"
                    size="small"
                    onClick={() => {
                        notification.close(key);
                        closeDialog();
                    }}
                >
                    cancel
                </Button>
                <Button
                    type="primary"
                    size="small"
                    onClick={() => {
                        this.onExecuteWorkflow();
                        notification.close(key);
                    }}
                >
                    Confirm
                </Button>
            </div>
        );
        if (count == 0) {
            notification.open({
                message: 'Are you sure?',
                description: `There aren’t any annotations in this task.
                If you workflow depends on this data it may throw an error. Do you want to continue?`,
                duration: 0,
                btn,
                key,
            });
        } else if (count < 100) {
            notification.open({
                message: 'Are you sure?',
                description: `Number of annotations is less than 100.
                Deep learning models work better with large datasets. Are you sure you want to continue?`,
                duration: 0,
                btn,
                key,
            });
        } else {
            this.onExecuteWorkflow();
        }
    }

    private ExecuteSuccessMessage(name: string, url: string): JSX.Element {
        return (
            <div>
                {name} workflow has been executed. Please check the workflow for logs.
                <br />
                Visit this url for more information: <a href={url} target='_blank'>{url}</a>
            </div>
        )
    }

    private async onExecuteWorkflow(): Promise<void> {
        const {
            taskInstance,
            closeDialog,
        } = this.props;
        const {
            workflowTemplate,
            selectedWorkflowParam,
            selectedNodePool,
            selectedDumpFormat,
            sysOutputPath,
            sysAnnotationPath,
            selectedFinetuneCheckpoint,
            allSysFinetuneCheckpoint,
        } = this.state;

        this.setState({
            executingAnnotation: true,
        })

        let finalPayload: ExecuteWorkflowPayload = {
            workflow_template: workflowTemplate!.uid || "",
            parameters: selectedWorkflowParam,
            dump_format: selectedDumpFormat!.tag || null,
        }
        if (selectedNodePool) {
            finalPayload.parameters["sys-node-pool"] = selectedNodePool.value;
        }
        if (sysOutputPath) {
            finalPayload.parameters["sys-output-path"] = sysOutputPath.value;
        }
        if (sysAnnotationPath) {
            finalPayload.parameters["sys-annotation-path"] = sysAnnotationPath.value;
        }
        if(selectedFinetuneCheckpoint || allSysFinetuneCheckpoint.value) {
            finalPayload.parameters["sys-finetune-checkpoint"] = selectedFinetuneCheckpoint ? selectedFinetuneCheckpoint : allSysFinetuneCheckpoint.value;
        }

        const baseUrl: string = core.config.backendAPI.slice(0, -7);
        let successResp = await core.server.request(`${baseUrl}/onepanelio/execute_workflow/${taskInstance.id}`, {
            method: 'POST',
            data: finalPayload,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        notification.open({
            message: 'Execute Workflow',
            duration: 0,
            description: this.ExecuteSuccessMessage(workflowTemplate!.uid, successResp.url)
        });

        closeDialog();
    }

    private onWorkflowTemplateChange = async (value: string) => {

        const {
            taskInstance,
            workflowTemplates,
        } = this.props;

        const data = workflowTemplates.find(workflow => workflow.uid === value)
        this.setState({
            workflowTemplate: data,
            getingParameters: true,
        })
        if (value) {
            const baseUrl: string = core.config.backendAPI.slice(0, -7);
            try {
                const response = await core.server.request(`${baseUrl}/onepanelio/get_workflow_parameters`, {
                    method: 'POST',
                    data,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                const { parameters } = response;
                let workflowParamsArr = parameters, workflowParamNameValue = {};
                const sysNodePoolParam = parameters.find((param: WorkflowParameters) => param.name === "sys-node-pool");
                const sysFinetuneCheckpoint = parameters.find((param: WorkflowParameters) => param.name === "sys-finetune-checkpoint");
                const sysOutputPath = parameters.find((param: WorkflowParameters) => param.name === "sys-output-path");
                const sysAnnotationPath = parameters.find((param: WorkflowParameters) => param.name === "sys-annotation-path");

                try {
                    if (sysNodePoolParam) {
                        const nodePoolResp = await core.server.request(`${baseUrl}/onepanelio/get_node_pool`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        });
                        let { node_pool } = nodePoolResp;
                        this.setState({
                            allSysNodePools: {
                                ...node_pool,
                                hint: sysNodePoolParam.hint,
                                display_name: sysNodePoolParam.display_name ? sysNodePoolParam.display_name : sysNodePoolParam.name
                            },
                            defaultSysNodePoolVal: sysNodePoolParam.value,
                            selectedNodePool: node_pool.options.find((node: NodePoolParameters) => node.value === sysNodePoolParam.value)
                        });
                    }

                if (sysFinetuneCheckpoint) {
                    const specificModelsResp = await core.server.request(`${baseUrl}/onepanelio/get_base_model`, {
                        method: 'POST',
                        data: { uid: data!.uid },
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                    let { keys } = specificModelsResp;
                    if (keys.length > 0){
                        this.setState({
                            allSysFinetuneCheckpoint: {
                                options: keys,
                                hint: sysFinetuneCheckpoint.hint,
                                display_name: sysFinetuneCheckpoint.display_name ? sysFinetuneCheckpoint.display_name : sysFinetuneCheckpoint.name
                            },
                        });
                    }
                    else{
                        this.setState({
                            allSysFinetuneCheckpoint: {
                                value: "",
                                hint: sysFinetuneCheckpoint.hint,
                                display_name: sysFinetuneCheckpoint.display_name ? sysFinetuneCheckpoint.display_name : sysFinetuneCheckpoint.name
                            },
                        });
                    }
                }

                    if (sysOutputPath) {
                        const sysOutputPathResp = await core.server.request(`${baseUrl}/onepanelio/get_output_path/${taskInstance.id}`, {
                            method: 'POST',
                            data: { uid: data!.uid },
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        });
                        this.setState({
                            sysOutputPath: {
                                display_name: sysOutputPath.display_name ? sysOutputPath.display_name : sysOutputPath.name,
                                hint: sysOutputPath.hint,
                                value: sysOutputPathResp.name
                            }
                        });
                    }

                    if (sysAnnotationPath) {
                        const sysAnnotationPathResp = await core.server.request(`${baseUrl}/onepanelio/get_annotation_path/${taskInstance.id}`, {
                            method: 'POST',
                            data: { uid: data!.uid },
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        });
                        this.setState({
                            sysAnnotationPath: {
                                display_name: sysAnnotationPath.display_name ? sysAnnotationPath.display_name : sysAnnotationPath.name,
                                hint: sysAnnotationPath.hint,
                                value: sysAnnotationPathResp.name
                            }
                        });
                    }
                } catch (e) {
                    throw new Error();
                }

                workflowParamsArr = parameters.filter((param: WorkflowParameters) => {
                    if (param.name !== "sys-node-pool" && param.name !== "sys-output-path" &&
                        param.name !== "sys-annotation-path" && param.name !== "sys-finetune-checkpoint" && param.name !== "dump-format") {
                        workflowParamNameValue = {
                            ...workflowParamNameValue,
                            [param.name]: param.value
                        }
                        return true;
                    }
                    return false;
                })

                const { dump_formats } = await core.server.request(`${baseUrl}/onepanelio/get_available_dump_formats`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                const dumpFormat = parameters.find((param: WorkflowParameters) => param.name === "dump-format");
                if (!dumpFormat || !dumpFormat.value) {
                    this.setState({
                        allDumpFormats: dump_formats,
                    });
                } else {
                    let dumpFormatInParams = dump_formats.find((dump: DumpFormats) => dump.tag === dumpFormat.value);
                    if (dumpFormatInParams) {
                        this.setState({
                            selectedDumpFormat: dumpFormatInParams
                        })
                    } else {
                        this.setState({
                            allDumpFormats: dump_formats,
                            showDumpFormatHint: true,
                        })
                    }
                }


                this.setState({
                    getingParameters: false,
                    allWorkflowParameters: workflowParamsArr,
                    selectedWorkflowParam: { ...workflowParamNameValue }
                });
            } catch (error) {
                // this.showErrorNotification(error);
                this.setState({
                    isLoading: false,
                    executingAnnotation: false,
                    getingParameters: false,
                });
            }
        }
    }

    private renderModelSelector(): JSX.Element {

        const {
            workflowTemplates,
        } = this.props

        return (
            <React.Fragment>
                <Row type='flex' align='middle'>
                    <Col span={24}>
                        <label className='cvat-text-color ant-form-item-label'>Select Workflow template:</label>
                        <Select
                            placeholder='Select a Workflow template'
                            style={{ width: '100%' }}
                            onChange={this.onWorkflowTemplateChange.bind(this)}
                        >
                            {
                                workflowTemplates.map((workflow: WorkflowTemplates) =>
                                    <Select.Option value={workflow.uid} key={workflow.uid}>
                                        {workflow.uid}
                                    </Select.Option>
                                )
                            }
                        </Select>
                    </Col>
                </Row>

                {
                    this.state.allWorkflowParameters.map((workflowParams, index) => {
                        return (
                            <Row type='flex' align='middle' key={index}>
                                <Col span={24}>
                                    <label className='cvat-text-color ant-form-item-label'>{ workflowParams.display_name ? workflowParams.display_name : workflowParams.name }:</label>
                                    {
                                        workflowParams.type && workflowParams.type.toLowerCase() === "select.select" ?
                                            <Select
                                                placeholder='Select a Workflow parameter'
                                                style={{ width: '100%' }}
                                                defaultValue={
                                                    this.state.selectedWorkflowParam[workflowParams.name]
                                                }
                                                onChange={(value: any) => this.setState({
                                                    selectedWorkflowParam: {
                                                        ...this.state.selectedWorkflowParam,
                                                        [workflowParams.name]: value
                                                    }
                                                })}
                                            >
                                                {
                                                    workflowParams.options.map((param: any) =>
                                                        <Select.Option value={param.value} key={param.value}>
                                                            {param.name}
                                                        </Select.Option>
                                                    )
                                                }
                                            </Select> : null
                                    }
                                    {
                                        (!workflowParams.type || workflowParams.type.toLowerCase() === "textarea.textarea") ?
                                            <TextArea
                                                autoSize={{ minRows: 1, maxRows: 4 }}
                                                name={workflowParams.name}
                                                value={this.state.selectedWorkflowParam[workflowParams.name]}
                                                onChange={(event) => this.setState({
                                                    selectedWorkflowParam: {
                                                        ...this.state.selectedWorkflowParam,
                                                        [event.target.name]: event.target.value
                                                    }
                                                })}
                                            /> : null
                                    }
                                    {
                                        workflowParams.hint ?
                                            <div
                                                style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                                dangerouslySetInnerHTML={{__html: workflowParams.hint}}
                                            ></div> :
                                            null
                                    }
                                </Col>
                            </Row>
                        )
                    })
                }

                {
                    this.state.allSysNodePools.options.length ?
                        <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'>
                                    {this.state.allSysNodePools.display_name}:
                                </label>
                                <Select
                                    placeholder='Select a system node pool'
                                    style={{ width: '100%' }}
                                    defaultValue={this.state.defaultSysNodePoolVal}
                                    onChange={(value: any) => {
                                        const selectedNode = this.state.allSysNodePools.options.find(node => node.value === value);
                                        this.setState({
                                            selectedNodePool: selectedNode
                                        })
                                    }}
                                >
                                    {
                                        this.state.allSysNodePools.options.map((nodePool: NodePoolParameters) =>
                                            <Select.Option key={nodePool.value} value={nodePool.value}>
                                                {nodePool.name}
                                            </Select.Option>
                                        )
                                    }
                                </Select>
                                {
                                    this.state.allSysNodePools.hint ?
                                        <div
                                            style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                            dangerouslySetInnerHTML={{__html: this.state.allSysNodePools.hint}}
                                        ></div> :
                                        null
                                }
                            </Col>
                        </Row> : null
                }

                {
                    this.state.allSysFinetuneCheckpoint.options ? this.state.allSysFinetuneCheckpoint.options.length ?
                        <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'>{this.state.allSysFinetuneCheckpoint.display_name}:</label>
                                <Select
                                    placeholder='Select a checkpoint path'
                                    style={{ width: '100%' }}
                                    onChange={(value: any) => {
                                        this.setState({
                                            selectedFinetuneCheckpoint: value
                                        })
                                    }}
                                >
                                    {
                                        this.state.allSysFinetuneCheckpoint.options.map((checkpoint: string) =>
                                            <Select.Option key={checkpoint} value={checkpoint}>
                                                {checkpoint}
                                            </Select.Option>
                                        )
                                    }
                                </Select>
                                {
                                    this.state.allSysFinetuneCheckpoint.hint ?
                                        <div
                                            style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                            dangerouslySetInnerHTML={{__html: this.state.allSysFinetuneCheckpoint.hint}}
                                        ></div> :
                                        null
                                }
                            </Col>
                        </Row> : null :                         <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'><Col span={6}>{this.state.allSysFinetuneCheckpoint.display_name}:</Col></label>
                                <TextArea
                                    autoSize={{ minRows: 1, maxRows: 4 }}
                                    value={this.state.allSysFinetuneCheckpoint.value || ""}
                                    onChange={(event) => this.setState({
                                        allSysFinetuneCheckpoint: {
                                            ...this.state.allSysFinetuneCheckpoint,
                                            value: event.target.value
                                        }
                                    })}
                                />
                                {
                                    this.state.allSysFinetuneCheckpoint.hint ?
                                        <div
                                            style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                            dangerouslySetInnerHTML={{__html: this.state.allSysFinetuneCheckpoint.hint}}
                                        ></div> :
                                        null
                                }
                            </Col>
                        </Row>
                }

                {
                    this.state.sysOutputPath.value ?
                        <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'>{this.state.sysOutputPath.display_name}:</label>
                                <TextArea
                                    autoSize={{ minRows: 1, maxRows: 4 }}
                                    value={this.state.sysOutputPath.value || ""}
                                    onChange={(event) => this.setState({
                                        sysOutputPath: {
                                            ...this.state.sysOutputPath,
                                            value: event.target.value
                                        }
                                    })}
                                />
                                {
                                    this.state.sysOutputPath.hint ?
                                        <div
                                            style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                            dangerouslySetInnerHTML={{__html: this.state.sysOutputPath.hint}}
                                        ></div> :
                                        null
                                }
                            </Col>
                        </Row> : null
                }

                {
                    this.state.sysAnnotationPath.value ?
                        <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'>{this.state.sysAnnotationPath.display_name}:</label>
                                <TextArea
                                    autoSize={{ minRows: 1, maxRows: 4 }}
                                    value={this.state.sysAnnotationPath.value || ""}
                                    onChange={(event) => this.setState({
                                        sysAnnotationPath: {
                                            ...this.state.sysAnnotationPath,
                                            value: event.target.value
                                        }
                                    })}
                                />
                                {
                                    this.state.sysAnnotationPath.hint ?
                                        <div
                                            style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}
                                            dangerouslySetInnerHTML={{__html: this.state.sysAnnotationPath.hint}}
                                        ></div> :
                                        null
                                }
                            </Col>
                        </Row> : null
                }

                {
                    this.state.allDumpFormats.length ?
                        <Row type='flex' align='middle'>
                            <Col span={24}>
                                <label className='cvat-text-color ant-form-item-label'>Select dump format: &nbsp;<span style={{ color: "red" }}>*</span></label>
                                <Select
                                    placeholder='Select a dump format'
                                    style={{ width: '100%' }}
                                    defaultValue={this.state.selectedDumpFormat ? this.state.selectedDumpFormat.tag : ""}
                                    onChange={(value: any) => {
                                        const selectedFormat = this.state.allDumpFormats.find(format => format.tag === value);
                                        this.setState({
                                            selectedDumpFormat: selectedFormat,
                                            showDumpFormatHint: false,
                                        })
                                    }}
                                >
                                    {
                                        this.state.allDumpFormats.map((format: DumpFormats) =>
                                            <Select.Option key={format.tag} value={format.tag}>
                                                {format.name}
                                            </Select.Option>
                                        )
                                    }
                                </Select>
                                {
                                    this.state.showDumpFormatHint ?
                                        <div style={{ fontSize: "12px", marginLeft: "10px", color: "#716f6f" }}>
                                            Dump format provided in Workflow is not supported. Please select one from above list.
                                        </div> :
                                        null
                                }
                            </Col>
                        </Row> : null
                }
            </React.Fragment>
        );
    }

    private renderContent(): JSX.Element {
        return (
            <div className='cvat-run-model-dialog'>
                {this.renderModelSelector()}
            </div>
        );
    }

    private footerComponent(): JSX.Element[] {
        const {
            closeDialog,
            fetchingWorkflowTemplates
        } = this.props;

        let footerElements = [];
        if (this.state.executingAnnotation) {
            footerElements.push(
                <span key={"message"} style={{ float: 'left', paddingTop: '5px', color: '#1890ff', }}>
                    <Spin /> &nbsp; &nbsp;
                    {`Executing ${this.state.workflowTemplate!.uid} workflow...`}
                </span>
            )
        }

        if (this.state.getingParameters) {
            footerElements.push(
                <span key={"paramMessage"} style={{ float: 'left', paddingTop: '5px', color: '#1890ff', }}>
                    <Spin /> &nbsp; &nbsp;
                    {`Getting workflow parameters...`}
                </span>
            )
        }

        if (fetchingWorkflowTemplates) {
            footerElements.push(
                <span key={"fetchMessage"} style={{ float: 'left', paddingTop: '5px', color: '#1890ff', }}>
                    <Spin /> &nbsp; &nbsp;
                    {`Getting workflow templates...`}
                </span>
            )
        }

        const checkSubmitEnable = () => {
            if (this.state.workflowTemplate!.uid && this.state.selectedDumpFormat) {
                if ((this.state.allSysNodePools.options.length && this.state.selectedNodePool) || !this.state.allSysNodePools.options.length) {
                    return false;
                }
                return true;
            }
            return true;
        }

        const footerButtons = [
            <Button key="back" onClick={(): void => {
                this.setState(InitialState);
                closeDialog();
            }}>
                Cancel
            </Button>,
            <Button key="submit" type="primary" disabled={checkSubmitEnable()} onClick={(): void => {
                this.handleSubmit();
            }}>
                Submit
            </Button>,
        ]
        return footerElements = [
            ...footerElements,
            ...footerButtons
        ]

    }

    public render(): JSX.Element | false {
        const {
            visible,
        } = this.props;

        return (
            visible && (
                <Modal
                    closable={false}
                    footer={this.footerComponent()}
                    title={'Execute training Workflow'}
                    visible
                    width="50%"
                >
                    {this.renderContent()}
                </Modal>
            )
        );
    }
}
