import { createAction, ThunkAction, ActionUnion, WorkflowTemplates } from './interfaces';

import getCore from 'cvat-core-wrapper';

const core = getCore();
const baseURL = core.config.backendAPI.slice(0, -7);

export enum CreateAnnotationActionTypes {
    OPEN_NEW_ANNOTATION_DIALOG = 'SHOW_NEW_ANNOTATION_DIALOG',
    CLOSE_NEW_ANNOTATION_DIALOG = 'CLOSE_NEW_ANNOTATION_DIALOG',
    GET_BASE_MODEL = 'GET_BASE_MODEL',
}
export type CreateAnnotationActions = ActionUnion<typeof createAnnotationAction>;

export const createAnnotationAction = {
    openNewAnnotationDialog: (taskInstance: any, workflowTemplate: WorkflowTemplates[]) => createAction(
        CreateAnnotationActionTypes.OPEN_NEW_ANNOTATION_DIALOG, { 
            taskInstance,
            workflowTemplate
         },
    ),
    closeNewAnnotationDialog: () => createAction(CreateAnnotationActionTypes.CLOSE_NEW_ANNOTATION_DIALOG),
    getBaseModelList: (baseModelList: string[]) => createAction(
        CreateAnnotationActionTypes.GET_BASE_MODEL, {
            baseModelList,
        },
    ),
}

export function getBaseModelsAsync(taskInstance: any, modelType: string) : ThunkAction {
    return async(dispatch, getState): Promise<void> => {
        try {
            const {keys} = await core.server.request(
                `${baseURL}/onepanelio/get_base_model`, {
                    method: 'POST',
                    data: {model_type: modelType},
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            )

            dispatch(createAnnotationAction.getBaseModelList(keys || []));
        } catch (e) {

        }
    }
}

export function getWorkflowTemplateAsync(taskInstance: any) : ThunkAction {
    return async(dispatch, getState): Promise<void> => {
        try {
            const response =  await core.server.request(
                `${baseURL}/onepanelio/get_workflow_templates`, {
                    method: 'POST',
                }
            )
            if(response.count) {
                const workflowTemplates: WorkflowTemplates[] = response.workflow_templates.map((workflow: any) => (
                    {
                        uid: workflow.uid, 
                        version: workflow.version == "none" || workflow.version == null ? "0" : workflow.version
                    }
                ))
                dispatch(createAnnotationAction.openNewAnnotationDialog(taskInstance, workflowTemplates));
            }
        } catch (e) {
            console.log("error getting workflow template");
        }
    }
}

export type CreateAnnotationAction = ActionUnion<typeof createAnnotationAction>;