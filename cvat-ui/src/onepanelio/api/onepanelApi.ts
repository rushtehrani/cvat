import getCore from 'cvat-core-wrapper';
import { WorkflowTemplates } from "../createAnnotationModal/interfaces";

const core = getCore();
const baseUrl = core.config.backendAPI.slice(0, -7);

export const OnepanelApi = {
    async getNodePool() {
        return core.server.request(`${baseUrl}/onepanelio/get_node_pool`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
    },

    async getWorkflowParameters(data: WorkflowTemplates) {
        return core.server.request(`${baseUrl}/onepanelio/get_workflow_parameters`, {
            method: 'POST',
            data,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    },

    async getBaseModel(workflowTemplateUid: string) {
        return await core.server.request(`${baseUrl}/onepanelio/get_base_model`, {
            method: 'POST',
            data: { uid: workflowTemplateUid },
            headers: {
                'Content-Type': 'application/json',
            },
        });
    },

    async getOutputPath(id: string, workflowTemplateUid: string) {
        return core.server.request(`${baseUrl}/onepanelio/get_output_path/${id}`, {
            method: 'POST',
            data: { uid: workflowTemplateUid },
            headers: {
                'Content-Type': 'application/json',
            },
        });
    },

    async getAnnotationPath(id: string, workflowTemplateUid: string) {
        return core.server.request(`${baseUrl}/onepanelio/get_annotation_path/${id}`, {
            method: 'POST',
            data: { uid: workflowTemplateUid },
            headers: {
                'Content-Type': 'application/json',
            },
        });
    },

    async getAvailableDumpFormats() {
        return core.server.request(`${baseUrl}/onepanelio/get_available_dump_formats`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }
};
