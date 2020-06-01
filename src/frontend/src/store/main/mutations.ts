import { IIspAvailable, IUserProfile } from '@/interfaces';
import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';
import { AppNotification, MainState } from './state';

export const mutations = {
    setToken(state: MainState, payload: string) {
        state.token = payload;
    },
    setTokenType(state: MainState, payload: string) {
        state.tokenType = payload;
    },
    setLoggedIn(state: MainState, payload: boolean) {
        state.isLoggedIn = payload;
    },
    setLogInError(state: MainState, payload: boolean) {
        state.logInError = payload;
    },
    setUserProfile(state: MainState, payload: IUserProfile) {
        state.userProfile = payload;
    },
    setDashboardMiniDrawer(state: MainState, payload: boolean) {
        state.dashboardMiniDrawer = payload;
    },
    setDashboardShowDrawer(state: MainState, payload: boolean) {
        state.dashboardShowDrawer = payload;
    },
    addNotification(state: MainState, payload: AppNotification) {
        state.notifications.push(payload);
    },
    removeNotification(state: MainState, payload: AppNotification) {
        state.notifications = state.notifications.filter(
            (notification) => notification !== payload,
        );
    },
    setAvailableIsp(state: MainState, payload: IIspAvailable) {
        state.availableIsp = payload;
        // if (payload.domain) {
        //     state.availableDomainIsplist = payload.domain;
        // }
        // if (payload.vps) {
        //     state.availableDomainIsplist = payload.vps;
        // }
    },
    setDomainIsp(state: MainState, payload: any) {
        state.domainIsplist = payload;
    },
    setVpsDomainIsp(state: MainState, payload: any) {
        state.vpsIspList = payload;
    },
};

const { commit } = getStoreAccessors<MainState | any, State>('');

export const commitSetDashboardMiniDrawer = commit(mutations.setDashboardMiniDrawer);
export const commitSetDashboardShowDrawer = commit(mutations.setDashboardShowDrawer);
export const commitSetLoggedIn = commit(mutations.setLoggedIn);
export const commitSetLogInError = commit(mutations.setLogInError);
export const commitSetToken = commit(mutations.setToken);
export const commitSetTokenType = commit(mutations.setTokenType);
export const commitSetUserProfile = commit(mutations.setUserProfile);
export const commitAddNotification = commit(mutations.addNotification);
export const commitRemoveNotification = commit(mutations.removeNotification);
export const commitSetAvailableIsp = commit(mutations.setAvailableIsp);
export const commitSetDomainIsp = commit(mutations.setDomainIsp);
export const commitSetVpsIsp = commit(mutations.setVpsDomainIsp);
