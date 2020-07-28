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

interface Props {
    visible: boolean;
    taskInstance: any;
    baseModelList: string[];
    closeDialog(): void;
    getBaseModelList(taskInstance: any, modelType: string): void;
}

interface State {
    selectedModelType: string;
    selectedModel: string;
    showModelsOptions: boolean;
    machineType: {
        label: string;
        value: string;
    };
    argumentS: string;
    selectedBaseModel: string;
    executingAnnotation: boolean;
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

export default class ModelNewAnnotationModalComponent extends React.PureComponent<Props, State> {
    public constructor(props: Props) {
        super(props);
        this.state = {
            selectedModelType: '',
            selectedModel: models[0].label,
            showModelsOptions: false,
            machineType: machines[0],
            argumentS: '',
            selectedBaseModel: '',
            executingAnnotation: false,
        };
    }

    public componentDidUpdate(prevProps: Props, prevState: State): void {
        const {
            visible,
        } = this.props;


        if (!prevProps.visible && visible) {
            this.setState({
                selectedModelType: '',
                selectedModel: models[0].label,
                machineType: machines[0],
                showModelsOptions: false,
                argumentS: '',
                selectedBaseModel: '',
                executingAnnotation: false,
            });
        }
    }

    private async onCreateNewAnnotation(): Promise<Boolean> {
        const {
            taskInstance,
            closeDialog,
        } = this.props;

        let {
            selectedModelType,
            selectedModel,
            machineType: {
                value,
            },
            argumentS,
            selectedBaseModel,
        } = this.state;

        this.setState({
            executingAnnotation: true,
        });

        const baseUrl: string = core.config.backendAPI.slice(0, -7);
        let formData: CreateAnnotationSubmitData = {
            project_uid: taskInstance.id,
            arguments: argumentS,
            dump_format: selectedModelType,
            machine_type: value,
            ref_model: selectedModelType! !== "MASK ZIP 1.0" ? selectedModel : "",
            base_url: baseUrl,
            base_model: selectedBaseModel,
        }

        // try {
        //     let resp = await core.server.request(`${baseUrl}/api/v1/tasks/${taskInstance.id}/dataset?format=cvat_coco`, {
        //         method: 'GET',
        //         // data: formData,
        //         // form: formData,
        //         headers: {
        //             'Content-Type': 'application/x-www-form-urlencoded',
        //         },
        //     })
        //     console.log(resp);
        // } catch (error) {
        //     notification.error({
        //         message: 'data dump  failed.',
        //         description: `Create New Annotation failed (Error code: ${error.code}). Please try again later`,
        //         duration: 5,
        //     });

        try {
            await core.server.request(`${baseUrl}/onepanelio/execute_workflow/${taskInstance.id}`, {
                method: 'POST',
                data: formData,
                // form: formData,
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            notification.info({
                message: 'Create new annotation',
                description: `${selectedModelType} workflow has been executed. Please check the workflow for logs.`,
            });
        } catch (error) {
            notification.error({
                message: 'Create New Annotation failed.',
                description: `Create New Annotation failed (Error code: ${error.code}). Please try again later`,
                duration: 5,
            });
        } finally {
            closeDialog();
            return true;
        }
    }

    private onSubmitNotifications(count: number): Boolean {
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
                        this.onCreateNewAnnotation();
                        notification.close(key);
                    }}
                >
                    Confirm
                </Button>
            </div>
        );
        if (count == 0) {
            notification.error({
                message: 'Could not create new annotation.',
                description: `You don't have any annotated images.
                    Please annotate few images before training your model.`,
            });
            closeDialog();
            return true;
        }
        if (count < 100) {
            notification.open({
                message: 'Are you sure?',
                description: `'Number of annotations is less than 100. 
                    We recommend you annotate at least a few hundred to get good results.`,
                duration: 0,
                btn,
                key,
            });
        } else {
            this.onCreateNewAnnotation();
        }
        return true;
    }

    private async handleSubmit(): Promise<Boolean> {
        const baseUrl: string = core.config.backendAPI.slice(0, -7);
        const {
            taskInstance,
        } = this.props;
        const {
            selectedModelType,
        } = this.state;
        // let resp1 = await core.server.request(`${baseUrl}/api/v1/jobs/${taskInstance.id}/get_object_counts`, {
        //     method: 'GET',
        // });
        let resp = await core.server.request(`${baseUrl}/onepanelio/get_object_counts/${taskInstance.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const requiredShape: String = selectedModelType === "MASK ZIP 1.0" ? "polygon" : "rectangle";
        const {
            shapes,
            tracks,
        } = resp;

        if (tracks.length) {
            this.onCreateNewAnnotation();
            return true;
        }

        let count = shapes.reduce((acc: number, shape: any) => {
            if (shape.type === requiredShape) {
                acc++;
            }
            return acc;
        }, 0)
        return this.onSubmitNotifications(count);
    }

    private onArgumenstChange = (event: any): void => {
        const {
            target: {
                value,
            },
        } = event;
        this.setState({
            argumentS: value,
        })
    };

    private renderModelSelector(): JSX.Element {

        const {
            taskInstance,
            baseModelList,
            getBaseModelList,
        } = this.props

        return (
            <React.Fragment>
                <Row type='flex' align='middle'>
                    <Col span={6}>Select Model Type:</Col>
                    <Col span={17}>
                        <Select
                            placeholder='Select a model type'
                            style={{ width: '100%' }}
                            onChange={(value: string): void => {
                                this.setState({
                                    selectedModelType: value,
                                    showModelsOptions: value === "TFRecord ZIP 1.0",
                                })
                                if (value) {
                                    const modelType = value === "TFRecord ZIP 1.0" ? "tensorflow" : "maskrcnn";
                                    getBaseModelList(taskInstance, modelType);
                                }
                            }
                            }
                        >
                            <Select.Option value="TFRecord ZIP 1.0">
                                Tensorflow OD API
                            </Select.Option>
                            <Select.Option value="MASK ZIP 1.0">
                                MaskRCNN
                            </Select.Option>
                        </Select>
                    </Col>
                </Row>
                {
                    this.state.showModelsOptions &&
                    <Row type='flex' align='middle'>
                        <Col span={6}>Select Model:</Col>
                        <Col span={17}>
                            <Select
                                placeholder='Select a model'
                                style={{ width: '100%' }}
                                onChange={(value: string): void => {
                                    this.setState({
                                        selectedModel: value,
                                    })
                                }
                                }
                                defaultValue={this.state.selectedModel}
                            >
                                {models.map((model): JSX.Element => (
                                    <Select.Option key={model.label} value={model.label}>
                                        {model.label}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Col>
                    </Row>
                }
                {
                    this.state.showModelsOptions &&
                    <Row type='flex'>
                        <Col>
                            <div>
                                (Learn more about this base model by clicking the 'show more' link after clicking here:&nbsp;
                                <a
                                    href={`https://docs.onepanel.ai/docs/getting-started/use-cases/computervision/annotation/cvat/cvat_annotation_model#${this.state.selectedModel}`}
                                    target='_blank'
                                    className="cvat-create-anno-modal-link"
                                >
                                    {this.state.selectedModel}
                                </a>
                                )
                            </div>
                        </Col>
                    </Row>
                }
                <Row type='flex' align='middle'>
                    <Col span={6}>Select Machine Type:</Col>
                    <Col span={17}>
                        <Select
                            placeholder='Select a machine type'
                            style={{ width: '100%' }}
                            onChange={(value: string): void => {
                                let machine = machines.find(machine => machine.value === value)
                                this.setState({
                                    machineType: machine ? machine : machines[0]
                                })
                            }
                            }
                            defaultValue={this.state.machineType.label}
                        >
                            {machines.map((machine): JSX.Element => (
                                <Select.Option value={machine.value} key={machine.value}>
                                    {machine.label}
                                </Select.Option>
                            ))}
                        </Select>
                    </Col>
                </Row>
                <Row type='flex' align='middle'>
                    <Col span={6}>Select Base Model:</Col>
                    <Col span={17}>
                        <Select
                            placeholder='Select a base model'
                            style={{ width: '100%' }}
                            onChange={(value: string): void => {
                                this.setState({
                                    selectedBaseModel: value,
                                });
                            }}
                        >
                            {
                                baseModelList.map((baseModel: string, index: number): JSX.Element => (
                                    <Select.Option value={baseModel} key={index}>
                                        {baseModel}
                                    </Select.Option>
                                ))
                            }
                        </Select>
                    </Col>
                </Row>
                <Row type='flex'>
                    <Col span={6}> Arguments: </Col>
                    <Col span={17}>
                        <TextArea
                            autoSize={{ minRows: 1, maxRows: 4 }}
                            onChange={this.onArgumenstChange}
                        />
                    </Col>
                </Row>
                <Row type='flex'>
                    <Col>
                        <div>
                            (Learn how to add model &nbsp;
                            <a
                                href={`https://docs.onepanel.ai/docs/getting-started/use-cases/computervision/annotation/cvat/cvat_annotation_model#arguments-optional`}
                                target='_blank'
                                className="cvat-create-anno-modal-link"
                            >
                                training
                            </a>
                            )
                        </div>
                    </Col>
                </Row>
            </React.Fragment>
        );
    }

    private renderContent(): JSX.Element {
        return (
            <div className='cvat-run-model-dialog'>
                <div className="cvat-create-anno-modal-link cvat-create-anno-text-align" >
                    <a
                        href={`https://docs.onepanel.ai/docs/getting-started/use-cases/computervision/annotation/cvat/cvat_annotation_model#training-object-detection-model-through-cvat`}
                        target='_blank'>
                        How to use
                    </a>
                </div>
                {this.renderModelSelector()}
            </div>
        );
    }

    private footerComponent(): JSX.Element[] {
        const {
            closeDialog,
        } = this.props;

        let footerElements = [];
        if (this.state.executingAnnotation) {
            footerElements.push(
                <span key={"message"} style={{ float: 'left', paddingTop: '5px', color: '#1890ff', }}>
                    <Spin /> &nbsp; &nbsp;
                    {`Executing ${this.state.selectedModelType} workflow...`}
                </span>
            )
        }
        const footerButtons = [
            <Button key="back" onClick={(): void => {
                this.setState({
                    selectedModelType: '',
                    selectedModel: models[0].label,
                    machineType: machines[0],
                    showModelsOptions: false,
                    argumentS: ''
                });
                closeDialog();
            }}>
                Cancel
            </Button>,
            <Button key="submit" type="primary" disabled={!!!this.state.selectedModelType} onClick={(): void => {
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
                    title='Create new annotation'
                    visible
                    width="50%"
                >
                    {this.renderContent()}
                </Modal>
            )
        );
    }
}
