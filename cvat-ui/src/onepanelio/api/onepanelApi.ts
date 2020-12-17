import getCore from 'cvat-core-wrapper';
import {
    DumpFormats,
    NodePoolResponse,
    WorkflowParameters,
    WorkflowTemplates,
} from '../createAnnotationModal/interfaces';

const core = getCore();
const baseUrl = core.config.backendAPI.slice(0, -7);

export default class OnepanelApi {
    static getNodePool = async (): Promise<{nodePool: NodePoolResponse[]}> => core.server.request(
        `${baseUrl}/onepanelio/get_node_pool`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getWorkflowParameters = async (data: WorkflowTemplates):
    Promise<{parameters: WorkflowParameters[]}> => core.server.request(
        `${baseUrl}/onepanelio/get_workflow_parameters`, {
            method: 'POST',
            data,
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getBaseModel = async (workflowTemplateUid: string, sysRefModel = ''): Promise<string> => core.server.request(
        `${baseUrl}/onepanelio/get_base_model`, {
            method: 'POST',
            data: {
                uid: workflowTemplateUid,
                sysRefModel,
            },
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getOutputPath = async (id: string, workflowTemplateUid: string):
    Promise<WorkflowParameters> => core.server.request(
        `${baseUrl}/onepanelio/get_output_path/${id}`, {
            method: 'POST',
            data: { uid: workflowTemplateUid },
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getAnnotationPath = async (id: string, workflowTemplateUid: string):
    Promise<WorkflowParameters> => core.server.request(
        `${baseUrl}/onepanelio/get_annotation_path/${id}`, {
            method: 'POST',
            data: { uid: workflowTemplateUid },
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getAvailableDumpFormats = async (): Promise<{'dumpFormats': DumpFormats[]}> => core.server.request(
        `${baseUrl}/onepanelio/get_available_dump_formats`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );

    static getObjectCounts = async (id: string): Promise<{ shapes: string[], tracks: number[] }> => core.server.request(
        `${baseUrl}/onepanelio/get_object_counts/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        },
    );
}
