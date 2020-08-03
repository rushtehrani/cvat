import { Action, AnyAction, ActionCreatorsMapObject } from 'redux';
import { ThunkAction as _ThunkAction } from 'redux-thunk';
import { CombinedState } from 'reducers/interfaces';

export interface ActionWithPayload<T, P> extends Action<T> {
    payload: P;
}

export function createAction<T extends string>(type: T): Action<T>;
export function createAction<T extends string, P>(type: T, payload: P): ActionWithPayload<T, P>;
export function createAction<T extends string, P>(
    type: T, payload?: P,
): Action<T> | ActionWithPayload<T, P> {
    return typeof payload === 'undefined' ? { type } : { type, payload };
}

export type ActionUnion<A extends ActionCreatorsMapObject> = ReturnType<A[keyof A]>;

export type ThunkAction<R = void, A extends Action = AnyAction>
    = _ThunkAction<R, CombinedState, {}, A>;

export interface WorkflowTemplates {
    uid: string;
    version: string;
}

export interface WorkflowParameters {
    type: string;
    name: string;
    value: string;
    required: boolean | null;
    options: [];
    hint: string | null;
    display_name: string | null;
}

export interface NodePoolResponse {
    label: string;
    options: NodePoolParameters[];
}

export interface NodePoolParameters {
    name: string;
    value: string;
}

export interface DumpFormats {
    name: string;
    tag: string;
}

export interface ExecuteWorkflowPayload {
    workflow_template: string;
    parameters: any;
    dump_format: DumpFormats | null;
}