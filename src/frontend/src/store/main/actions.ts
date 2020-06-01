import { api } from '@/api';
import {
    IC2ProfileCreate,
    IIspPaginationQuery,
    IIspProfileCreate,
    IC2PaginationQuery,
    IPaginationQuery,
    IIspPaginationData,
} from '@/interfaces';
import router from '@/router';
import { getLocalToken, removeLocalToken, saveLocalToken } from '@/utils';
import { AxiosError } from 'axios';
import { getStoreAccessors } from 'typesafe-vuex';
import { ActionContext } from 'vuex';
import { State } from '../state';
import {
    commitAddNotification,
    commitRemoveNotification,
    commitSetAvailableIsp,
    commitSetLoggedIn,
    commitSetLogInError,
    commitSetToken,
    commitSetUserProfile,
    commitSetDomainIsp,
    commitSetVpsIsp,
    commitSetTokenType,
} from './mutations';
import { AppNotification, MainState } from './state';
import { readDomainIspList, readVpsIspList, readAvailableIsp } from './getters';
import {
    IPurchaseDomainData,
    IPurchasableDomainSearchParam,
    IDomainMonitorData,
    IDomainMonitorPaginationItemData,
    IDomainGrowCreateData,
} from '@/interfaces/domain';
import { IVpsSpecQuery, IVpsCreateData, IVpsPaginationData } from '@/interfaces/vps';
import { ITeamServerCreate, IRedirectorCreate, ITeamServerPaginationData } from '@/interfaces/module';
import { ISshConfigData, ISiteTemplateCreate } from '@/interfaces/config';

type MainContext = ActionContext<MainState, State>;

export const actions = {
    async actionLogIn(context: MainContext, payload: { username: string; password: string; }) {
        try {
            const response = await api.logInGetToken(payload.username, payload.password);

            const token = response.accessToken;
            const tokenType = response.tokenType;
            if (token) {
                saveLocalToken(token);
                commitSetToken(context, token);
                commitSetTokenType(context, tokenType);
                commitSetLoggedIn(context, true);
                commitSetLogInError(context, false);
                await dispatchGetUserProfile(context);
                await dispatchRouteLoggedIn(context);
                commitAddNotification(context, { content: 'Logged in', color: 'success' });
            } else {
                await dispatchLogOut(context);
            }
        } catch (err) {
            commitSetLogInError(context, true);
            await dispatchLogOut(context);
        }
    },
    async actionGetUserProfile(context: MainContext) {
        try {
            const response = await api.getMe();

            if (response) {
                commitSetUserProfile(context, response);
            }
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionUpdateUserProfile(context: MainContext, payload) {
        try {
            const loadingNotification = { content: 'saving', showProgress: true };
            commitAddNotification(context, loadingNotification);
            const response = (
                await Promise.all([
                    api.updateMe(context.state.token, payload),
                    await new Promise((resolve, reject) => setTimeout(() => resolve(), 500)),
                ])
            )[0];
            commitSetUserProfile(context, response);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, {
                content: 'Profile successfully updated',
                color: 'success',
            });
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionCheckLoggedIn(context: MainContext) {
        if (!context.state.isLoggedIn) {
            let token = context.state.token;
            if (!token) {
                const localToken = getLocalToken();
                if (localToken) {
                    commitSetToken(context, localToken);
                    token = localToken;
                }
            }
            if (token) {
                try {
                    const response = await api.getMe();
                    commitSetLoggedIn(context, true);
                    commitSetUserProfile(context, response);
                } catch (error) {
                    await dispatchRemoveLogIn(context);
                }
            } else {
                await dispatchRemoveLogIn(context);
            }
        }
    },
    async actionRemoveLogIn(context: MainContext) {
        removeLocalToken();
        commitSetToken(context, '');
        commitSetLoggedIn(context, false);
    },
    async actionLogOut(context: MainContext) {
        await dispatchRemoveLogIn(context);
        await dispatchRouteLogOut(context);
    },
    async actionUserLogOut(context: MainContext) {
        await dispatchLogOut(context);
        commitAddNotification(context, { content: 'Logged out', color: 'success' });
    },
    actionRouteLogOut(context: MainContext) {
        if (router.currentRoute.path !== '/login') {
            router.push('/login');
        }
    },
    async actionCheckApiError(context: MainContext, payload: AxiosError) {
        if (payload.response!.status === 401) {
            await dispatchLogOut(context);
        }
    },
    actionRouteLoggedIn(context: MainContext) {
        if (router.currentRoute.path === '/login' || router.currentRoute.path === '/') {
            router.push('/domain');
        }
    },
    async removeNotification(
        context: MainContext,
        payload: { notification: AppNotification; timeout: number; },
    ) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                commitRemoveNotification(context, payload.notification);
                resolve(true);
            }, payload.timeout);
        });
    },

    async getAvailableIsp(context: MainContext) {
        if (!context.state.availableIsp) {
            const response = await api.getAvailableIsp();
            commitSetAvailableIsp(context, response);
        }
        return readAvailableIsp(context);
    },
    async getDomainIspList(context: MainContext) {
        const domainIspList = await api.getDomainIspList();
        commitSetDomainIsp(context, domainIspList.items);
        return readDomainIspList(context);
    },
    async getVpsIspList(context: MainContext) {
        const VpsIspList = await api.getVpsIspList();
        commitSetVpsIsp(context, VpsIspList.items);
        return readVpsIspList(context);
    },
    async createIspProfile(context: MainContext, payload: { profile: IIspProfileCreate; type: string; }) {
        try {
            await api.createIspProfile(payload.profile, payload.type);
            commitAddNotification(context, { content: '创建成功', color: 'success' });
        } catch (error) {
            commitAddNotification(context, { color: 'error', content: '添加ISP配置失败' });
        }
    },
    async getIspProfileList(
        context: MainContext, payload: { query: IIspPaginationQuery; type: string; },
    ): Promise<IIspPaginationData> {
        const profileList = await api.getIspProfileList(payload.query, payload.type);
        return profileList;
    },
    async createC2Profile(context: MainContext, payload: IC2ProfileCreate) {
        await api.createC2Profile(payload);
        commitAddNotification(context, { content: '创建成功', color: 'success' });
    },
    async getC2ProfileList(context: MainContext, payload: IC2PaginationQuery) {
        const profileList = await api.getC2ProfileList(payload);
        return profileList;
    },
    async getC2Profile(context: MainContext, profileId: number) {
        const C2ProfileData = await api.getC2Profile(profileId);
        return C2ProfileData;
    },
    async createSiteTemplate(context: MainContext, payload: ISiteTemplateCreate) {
        await api.createSiteTemplate(payload);
        commitAddNotification(context, { content: '创建成功', color: 'success' });
    },
    async getSiteTemplateList(context: MainContext, payload: IPaginationQuery) {
        const tplListData = await api.getSiteTemplateList(payload);
        return tplListData;
    },
    async getSshConfig(context: MainContext): Promise<ISshConfigData> {
        const sshConfig = await api.getSshConfig();
        return sshConfig;
    },
    async createSshConfig(context: MainContext): Promise<ISshConfigData> {
        const sshConfig = await api.createSshConfig();
        return sshConfig;
    },
    async getVpsList(context: MainContext, payload: IPaginationQuery): Promise<IVpsPaginationData> {
        const vpsListData = await api.getVpsList(payload);
        return vpsListData;
    },
    async getDomainList(context: MainContext, payload: IPaginationQuery) {
        const domainListData = await api.getDomainList(payload);
        return domainListData;
    },
    async createDomain(context: MainContext, payload) {
        await api.createDomain(payload);
        commitAddNotification(context, { content: '创建成功', color: 'success' });
    },
    async reloadDomainDnsRecord(context: MainContext) {
        await api.reloadDomainDnsRecord();
        commitAddNotification(context, { content: '刷新成功', color: 'success' });
    },
    async searchPurchasableDomain(context: MainContext, payload: IPurchasableDomainSearchParam) {
        const purchasableDomainResponse = await api.searchPurchasableDomain(payload);
        return purchasableDomainResponse;
    },
    async purchaseDomain(context: MainContext, payload: IPurchaseDomainData) {
        const purchaseDomainResponse = await api.purchaseDomain(payload);
        commitAddNotification(context, { content: '购买域名成功', color: 'success' });
        return purchaseDomainResponse;
    },
    async createDomainMonitorTask(context: MainContext, payload: IDomainMonitorData) {
        const domainMonitorTaskResponse = await api.monitorDomain(payload);
        commitAddNotification(context, { content: '添加域名监控成功', color: 'success' });
        return domainMonitorTaskResponse;
    },
    async getDomainMonitorList(context: MainContext, payload: IPaginationQuery) {
        const domainMonitorListData = await api.getDomainMonitorList(payload);
        return domainMonitorListData;
    },
    async updateDomainMonitor(context: MainContext, payload: IDomainMonitorPaginationItemData) {
        const updateResult = await api.updateDomainMonitor(payload);
        commitAddNotification(context, { content: '更新监控成功', color: 'success' });
        return updateResult;
    },
    async deleteDomainMonitor(context: MainContext, monitorId: number) {
        return api.deleteDomainMonitor(monitorId);
    },
    async createDomainGrow(context: MainContext, payload: IDomainGrowCreateData) {
        const domainGrowResult = await api.createDomainGrow(payload);
        commitAddNotification(context, { content: '创建培养网站成功', color: 'success' });
        return domainGrowResult;
    },
    async deleteDomainGrow(context: MainContext, domainGrowId: number) {
        const deleteResult = await api.deleteDomainGrow(domainGrowId);
        commitAddNotification(context, { content: '清除培养网站成功', color: 'success' });
        return deleteResult;
    },
    async getDomainGrowList(context: MainContext, payload: IPaginationQuery) {
        const domainGrowListData = await api.getDomainGrowList(payload);
        return domainGrowListData;
    },
    async createVps(context: MainContext, payload: IVpsCreateData) {
        const createVpsResponse = await api.createVps(payload);
        commitAddNotification(context, { content: '创建VPS成功', color: 'success' });
        return createVpsResponse;
    },
    async getVpsSpecs(context: MainContext, payload: IVpsSpecQuery) {
        const vpsIspSpecsResponse = await api.getVpsSpecs(payload);
        return vpsIspSpecsResponse;
    },
    async getIspSshKeyList(context: MainContext, ispId: number): Promise<any[]> {
        const ispSshKeyListResponse = await api.getIspSshKeyList(ispId);
        return ispSshKeyListResponse;
    },
    async destroyVps(context: MainContext, vpsId: number) {
        const destroyResult = await api.destroyVps(vpsId);
        commitAddNotification(context, { content: '销毁VPS成功', color: 'success' });
        return destroyResult;
    },
    async reinstallVps(context: MainContext, vpsId: number) {
        const reinstallResult = await api.reinstallVps(vpsId);
        commitAddNotification(context, { content: '重装VPS成功', color: 'success' });
        return reinstallResult;
    },
    async rebootVps(context: MainContext, vpsId: number) {
        const rebootResult = await api.rebootVps(vpsId);
        commitAddNotification(context, { content: '重启VPS成功', color: 'success' });
        return rebootResult;
    },
    async getTeamServerList(context: MainContext, payload: IPaginationQuery): Promise<ITeamServerPaginationData> {
        const teamServerListData = await api.getTeamServerList(payload);
        return teamServerListData;
    },
    async getRedirectorList(context: MainContext, payload: IPaginationQuery) {
        const redirectorListData = await api.getRedirectorList(payload);
        return redirectorListData;
    },
    async createTeamServer(context: MainContext, payload: ITeamServerCreate) {
        const destroyResult = await api.createTeamServer(payload);
        commitAddNotification(context, { content: '创建 team server 成功', color: 'success' });
        return destroyResult;
    },
    async createRedirector(context: MainContext, payload: IRedirectorCreate) {
        const destroyResult = await api.createRedirector(payload);
        commitAddNotification(context, { content: '创建 redirector 成功', color: 'success' });
        return destroyResult;
    },
    async destroyRedirector(context: MainContext, id: number) {
        const destroyResult = await api.deleteRedirector(id);
        commitAddNotification(context, { content: '销毁Redirector成功', color: 'success' });
        return destroyResult;
    },
    async destroyTeamServer(context: MainContext, id: number) {
        const destroyResult = await api.deleteTeamServer(id);
        commitAddNotification(context, { content: '销毁TeamServer成功', color: 'success' });
        return destroyResult;
    },
};

const { dispatch } = getStoreAccessors<MainState | any, State>('');

export const dispatchCheckApiError = dispatch(actions.actionCheckApiError);
export const dispatchCheckLoggedIn = dispatch(actions.actionCheckLoggedIn);
export const dispatchGetUserProfile = dispatch(actions.actionGetUserProfile);
export const dispatchLogIn = dispatch(actions.actionLogIn);
export const dispatchLogOut = dispatch(actions.actionLogOut);
export const dispatchUserLogOut = dispatch(actions.actionUserLogOut);
export const dispatchRemoveLogIn = dispatch(actions.actionRemoveLogIn);
export const dispatchRouteLoggedIn = dispatch(actions.actionRouteLoggedIn);
export const dispatchRouteLogOut = dispatch(actions.actionRouteLogOut);
export const dispatchUpdateUserProfile = dispatch(actions.actionUpdateUserProfile);
export const dispatchRemoveNotification = dispatch(actions.removeNotification);
export const dispatchGetAvailableIsp = dispatch(actions.getAvailableIsp);
export const dispatchGetDomainIsp = dispatch(actions.getDomainIspList);
export const dispatchGetVpsIsp = dispatch(actions.getVpsIspList);
export const dispatchCreateIspProfile = dispatch(actions.createIspProfile);
export const dispatchGetIspProfileList = dispatch(actions.getIspProfileList);
export const dispatchCreateC2Profile = dispatch(actions.createC2Profile);
export const dispatchCreateSiteTemplate = dispatch(actions.createSiteTemplate);
export const dispatchGetC2Profile = dispatch(actions.getC2Profile);
export const dispatchGetC2ProfileList = dispatch(actions.getC2ProfileList);
export const dispatchGetVpsList = dispatch(actions.getVpsList);
export const dispatchGetDomainList = dispatch(actions.getDomainList);
export const dispatchCreateDomain = dispatch(actions.createDomain);
export const dispatchSearhPurchasableDomain = dispatch(actions.searchPurchasableDomain);
export const dispatchReloadDomainDnsRecord = dispatch(actions.reloadDomainDnsRecord);
export const dispatchPurchaseDomain = dispatch(actions.purchaseDomain);
export const dispatchCreateVps = dispatch(actions.createVps);
export const dispatchGetVpsSpecs = dispatch(actions.getVpsSpecs);
export const dispatchDestroyVps = dispatch(actions.destroyVps);
export const dispatchRebootVps = dispatch(actions.rebootVps);
export const dispatchReinstallVps = dispatch(actions.reinstallVps);
export const dispatchCreateDomainMonitorTask = dispatch(actions.createDomainMonitorTask);
export const dispatchGetDomainMonitorList = dispatch(actions.getDomainMonitorList);
export const dispatchUpdateDomainMonitor = dispatch(actions.updateDomainMonitor);
export const dispatchDeleteDomainMonitor = dispatch(actions.deleteDomainMonitor);
export const dispatchCreateDomainGrow = dispatch(actions.createDomainGrow);
export const dispatchDeleteDomainGrow = dispatch(actions.deleteDomainGrow);
export const dispatchGetDomainGrowList = dispatch(actions.getDomainGrowList);
export const dispatchGetSiteTemplateList = dispatch(actions.getSiteTemplateList);
export const dispatchGetTeamServerList = dispatch(actions.getTeamServerList);
export const dispatchGetRedirectorList = dispatch(actions.getRedirectorList);
export const dispatchCreateTeamServer = dispatch(actions.createTeamServer);
export const dispatchCreateRedirector = dispatch(actions.createRedirector);
export const dispatchGetIspSshKeyList = dispatch(actions.getIspSshKeyList);
export const dispatchGetSshConfig = dispatch(actions.getSshConfig);
export const dispatchCreateSshConfig = dispatch(actions.createSshConfig);
export const dispatchDestroyRedirector = dispatch(actions.destroyRedirector);
export const dispatchDestroyTeamServer = dispatch(actions.destroyTeamServer);
