import { createAction, ThunkAction, ActionUnion } from './interfaces';

import getCore from 'cvat-core-wrapper';

const core = getCore();
const baseURL = core.config.backendAPI.slice(0, -7);

export enum ModelsActionTypes {
    OPEN_NEW_ANNOTATION_DIALOG = 'SHOW_NEW_ANNOTATION_DIALOG',
    CLOSE_NEW_ANNOTATION_DIALOG = 'CLOSE_NEW_ANNOTATION_DIALOG',
    GET_BASE_MODEL = 'GET_BASE_MODEL',
}

export const createAnnotationAction = {
    openNewAnnotationDialog: (taskInstance: any) => createAction(
        ModelsActionTypes.OPEN_NEW_ANNOTATION_DIALOG, { 
            taskInstance,
         },
    ),
    closeNewAnnotationDialog: () => createAction(ModelsActionTypes.CLOSE_NEW_ANNOTATION_DIALOG),
    getBaseModelList: (baseModelList: string[]) => createAction(
        ModelsActionTypes.GET_BASE_MODEL, {
            baseModelList,
        },
    ),
}

export function getBaseModelsAsync(taskInstance: any, modelType: string) : ThunkAction {
    return async(dispatch, getState): Promise<void> => {
        try {
            const {keys} = await core.server.request(
                `${baseURL}/api/v1/tasks/${taskInstance.id}/get_base_model`, {
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

export type CreateAnnotationAction = ActionUnion<typeof createAnnotationAction>;