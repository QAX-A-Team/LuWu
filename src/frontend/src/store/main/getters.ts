import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';
import { MainState } from './state';

export const getters = {
    hasAdminAccess: (state: MainState) => {
        return state.userProfile && state.userProfile.isSuperuser && state.userProfile.isActive;
    },
    loginError: (state: MainState) => state.logInError,
    dashboardShowDrawer: (state: MainState) => state.dashboardShowDrawer,
    dashboardMiniDrawer: (state: MainState) => state.dashboardMiniDrawer,
    userProfile: (state: MainState) => state.userProfile,
    token: (state: MainState) => state.token,
    tokenType: (state: MainState) => state.tokenType,
    isLoggedIn: (state: MainState) => state.isLoggedIn,
    firstNotification: (state: MainState) => {
        return state.notifications.length > 0 && state.notifications[0];
    },

    availableIsp: (state: MainState) => state.availableIsp,
    domainIsplist: (state: MainState) => state.domainIsplist,
    vpsIspList: (state: MainState) => state.vpsIspList,
};

const { read } = getStoreAccessors<MainState, State>('');

export const readDashboardMiniDrawer = read(getters.dashboardMiniDrawer);
export const readDashboardShowDrawer = read(getters.dashboardShowDrawer);
export const readHasAdminAccess = read(getters.hasAdminAccess);
export const readIsLoggedIn = read(getters.isLoggedIn);
export const readAvailableIsp = read(getters.availableIsp);
export const readDomainIspList = read(getters.domainIsplist);
export const readVpsIspList = read(getters.vpsIspList);
export const readLoginError = read(getters.loginError);
export const readToken = read(getters.token);
export const readTokenType = read(getters.tokenType);
export const readUserProfile = read(getters.userProfile);
export const readFirstNotification = read(getters.firstNotification);

