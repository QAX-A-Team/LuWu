import { actions } from './actions';
import { getters } from './getters';
import { mutations } from './mutations';
import { MainState } from './state';

const defaultState: MainState = {
    // user
    isLoggedIn: null,
    token: '',
    tokenType: 'Bearer',
    logInError: false,
    userProfile: null,

    // common
    dashboardMiniDrawer: false,
    dashboardShowDrawer: true,
    notifications: [],

    // isp
    availableIsp: null,
    domainIsplist: [],
    vpsIspList: [],
};

export const mainModule = {
    state: defaultState,
    mutations,
    actions,
    getters,
};
