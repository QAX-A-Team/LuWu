import { actions } from './actions';
import { getters } from './getters';
import { mutations } from './mutations';
import { AdminState } from './state';

const defaultState: AdminState = {
    users: [],
};

export const adminModule = {
    state: defaultState,
    mutations,
    actions,
    getters,
};
