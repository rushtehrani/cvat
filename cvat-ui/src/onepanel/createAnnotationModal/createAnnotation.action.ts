import { createAction, ThunkAction, ActionUnion } from './interfaces';

import getCore from 'cvat-core-wrapper';

const core = getCore();
const baseURL = core.config.backendAPI.slice(0, -7);

export enum CreateAnnotationActionTypes {
    OPEN_NEW_ANNOTATION_DIALOG = 'SHOW_NEW_ANNOTATION_DIALOG',
    CLOSE_NEW_ANNOTATION_DIALOG = 'CLOSE_NEW_ANNOTATION_DIALOG',
    GET_BASE_MODEL = 'GET_BASE_MODEL',
}
export type CretaeAnnotationActions = ActionUnion<typeof createAnnotationAction>;

export const createAnnotationAction = {
    openNewAnnotationDialog: (taskInstance: any) => createAction(
        CreateAnnotationActionTypes.OPEN_NEW_ANNOTATION_DIALOG, { 
            taskInstance,
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

export type CreateAnnotationAction = ActionUnion<typeof createAnnotationAction>;