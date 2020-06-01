import axios, { AxiosRequestConfig } from 'axios';

import store from '@/store';
import router from '@/router';

import { apiUrl } from '@/env';
import { commitAddNotification } from '@/store/main/mutations';
import {
    IC2ProfileCreate,
    IC2PaginationData,
    IC2PaginationItemData,
    IIspAvailable,
    IIspPaginationData,
    IIspPaginationQuery,
    IIspProfileCreate,
    IUserProfile,
    IUserProfileCreate,
    IUserProfileUpdate,
    IPaginationQuery,
    IIspPaginationItemData,
    IPaginationData,
    IEnumItem,
} from './interfaces/index';
import {
    IPurchasableDomainSearchParam,
    IDomainPaginationData,
    IDomainPaginationItemData,
    IPurchaseDomainData,
    IDomainVerifyParam,
    IDomainMonitorData,
    IDomainMonitorPaginationData,
    IDomainMonitorPaginationItemData,
    IDomainGrowPaginationData,
    IDomainGrowCreateData,
    IDomainVerifyData,
    IPurchasableDomainItem,
} from '@/interfaces/domain';
import { readToken, readTokenType } from '@/store/main/getters';
import { getLocalToken } from '@/utils';
import { IVpsPaginationData, IVpsCreateData, IVpsSpecQuery, IVpsSpec } from './interfaces/vps';
import { ISiteTemplatePaginationData, ISshConfigData, ISiteTemplateCreate, ISiteTemplateUpdate } from './interfaces/config';
import { ITeamServerPaginationData, IRedirectorPaginationData, ITeamServerCreate, IRedirectorCreate } from './interfaces/module';
import { IToken } from './interfaces/user';


const instance = axios.create({
    baseURL: `${apiUrl}/api/v1/`,
    timeout: 300000,
    headers: { 'Content-Type': 'application/json' },
});

instance.interceptors.request.use(
    (config) => {
        if (!config.headers.Authorization) {
            const token = readToken(store) || getLocalToken();
            const tokenType = readTokenType(store);

            if (token) {
                config.headers.Authorization = `${tokenType} ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    },
);

instance.interceptors.response.use(
    (response) => {
        return Promise.resolve(response.data.result);
    },
    (error) => {
        if (error.response.status === 401) {
            router.push('login');
        }
        let errorContent;
        if (error.response) {
            errorContent = error.response.data.errors ? error.response.data.errors : error.response;
        } else {
            errorContent = error.message;
        }

        const errorResponseData = {
            content: `请求发生错误：${JSON.stringify(errorContent)}`,
            color: 'error',
            timeout: 10000,
        };
        commitAddNotification(store, errorResponseData);
        return Promise.reject(errorContent);
    },
);


export const api = {
    async logInGetToken(username: string, password: string): Promise<IToken> {
        const data = { username, password };
        return instance.post(`${apiUrl}/api/v1/login/access-token`, data);
    },
    async getMe(): Promise<IUserProfile> {
        return instance.get(`${apiUrl}/api/v1/users/me`);
    },
    async updateMe(token: string, data: IUserProfileUpdate): Promise<IUserProfile> {
        return instance.put(`${apiUrl}/api/v1/users/me`, data);
    },
    async getUsers(token: string): Promise<IUserProfile[]> {
        return instance.get(`${apiUrl}/api/v1/users/`);
    },
    async updateUser(token: string, userId: number, data: IUserProfileUpdate): Promise<IUserProfile> {
        return instance.put(`${apiUrl}/api/v1/users/${userId}`, data);
    },
    async createUser(token: string, data: IUserProfileCreate): Promise<IUserProfile> {
        return instance.post(`${apiUrl}/api/v1/users/`, data);
    },

    // config api
    async getIspProfileList(queryParams: IIspPaginationQuery, type: string): Promise<IIspPaginationData> {
        return instance.get(`config/isp/${type}`, { params: queryParams });
    },
    async getAvailableIsp(): Promise<IIspAvailable> {
        return instance.get(`config/isp/available`);
    },
    async getDomainIspList(): Promise<IPaginationData> {
        return instance.get(`config/isp/domain`);
    },
    async getVpsIspList(): Promise<IPaginationData> {
        return instance.get(`config/isp/vps`);
    },
    async createIspProfile(data: IIspProfileCreate, type: string) {
        return instance.post(`config/isp/${type}`, data);
    },
    async createC2Profile(data: IC2ProfileCreate) {
        const uploadConfig: AxiosRequestConfig = {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            transformRequest: [(profileData: IC2ProfileCreate) => {
                const formData = new FormData();
                formData.append('name', profileData.name);
                if (profileData.profile) {
                    formData.append('profile', profileData.profile, profileData.profile.name);
                }
                if (profileData.remark) {
                    formData.append('remark', profileData.remark);
                }
                return formData;
            }],
        };
        return instance.post('config/c2', data, uploadConfig);
    },
    async getC2ProfileList(queryParams: IIspPaginationQuery): Promise<IC2PaginationData> {
        return instance.get('config/c2', { params: queryParams });
    },
    async getC2Profile(profileId: number) {
        return instance.get<IC2PaginationItemData>(`config/c2/${profileId}`);
    },
    async updateIspProfile(data: IIspPaginationItemData) {
        return instance.put(`config/isp/${data.id}`, data);
    },
    async updateC2Profile(data: IC2PaginationItemData) {
        return instance.put(`config/c2/${data.id}`, data);
    },
    async deleteIspProfile(profileId: number) {
        return instance.delete(`config/isp/${profileId}`);
    },
    async deleteC2Profile(profileId: number) {
        return instance.delete(`config/c2/${profileId}`);
    },
    async reloadIspConfig(type: string) {
        return instance.get(`config/isp/${type}/reload`);
    },
    async createSiteTemplate(data: ISiteTemplateCreate) {
        const uploadConfig: AxiosRequestConfig = {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            transformRequest: [(siteTemplateData: ISiteTemplateCreate) => {
                const formData = new FormData();
                formData.append('name', siteTemplateData.name);
                if (siteTemplateData.zipFile) {
                    formData.append('zipFile', siteTemplateData.zipFile, siteTemplateData.zipFile.name);
                }
                if (siteTemplateData.remark) {
                    formData.append('remark', siteTemplateData.remark);
                }
                return formData;
            }],
        };
        return instance.post('config/template/site', data, uploadConfig);
    },
    async updateSiteTemplate(templateData: ISiteTemplateUpdate) {
        return instance.put(`config/template/site/${templateData.id}`, templateData);
    },
    async deleteSiteTemplate(templateId: number) {
        return instance.delete(`config/template/site/${templateId}`);
    },
    async getSiteTemplateList(queryParams: IPaginationQuery): Promise<ISiteTemplatePaginationData> {
        return instance.get('config/template/site', { params: queryParams });
    },
    async getSshConfig(): Promise<ISshConfigData> {
        return instance.get('config/ssh');
    },
    async createSshConfig(): Promise<ISshConfigData> {
        return instance.post('config/ssh');
    },
    async getIspSshKeyList(ispId: number): Promise<any[]> {
        return instance.get(`vps/isp/${ispId}/ssh_keys`);
    },
    // vps api
    async getVpsList(queryParams: IPaginationQuery): Promise<IVpsPaginationData> {
        return instance.get('vps/', { params: queryParams });
    },
    async createVps(data: IVpsCreateData) {
        return instance.post('vps/', data);
    },
    async getVpsSpecs(queryParams: IVpsSpecQuery): Promise<IVpsSpec> {
        return instance.get('vps/specs', { params: queryParams });
    },
    async destroyVps(vpsId: number) {
        return instance.delete(`vps/${vpsId}`);
    },
    async reinstallVps(vpsId: number) {
        return instance.get(`vps/${vpsId}/reinstall`);
    },
    async rebootVps(vpsId: number) {
        return instance.get(`vps/${vpsId}/reboot`);
    },

    // domain api
    async getDomainList(queryParams: IPaginationQuery): Promise<IDomainPaginationData> {
        return instance.get('domains/', { params: queryParams });
    },
    async createDomain(data: IDomainPaginationItemData) {
        return instance.post(`domains/`, data);
    },
    async reloadDomainDnsRecord() {
        return instance.get('domains/reload');
    },
    async deleteDomain(profileId: number) {
        return instance.delete(`domains/${profileId}`);
    },
    async searchPurchasableDomain(data: IPurchasableDomainSearchParam): Promise<IPurchasableDomainItem[]> {
        return instance.post(`domains/purchasable`, data);
    },
    async purchaseDomain(data: IPurchaseDomainData) {
        return instance.post('domains/purchase', data);
    },
    async verifyDomain(data: IDomainVerifyParam): Promise<IDomainVerifyData> {
        return instance.post('domains/verify', data);
    },
    async monitorDomain(data: IDomainMonitorData) {
        return instance.post('domains/monitor', data);
    },
    async getDomainMonitorList(queryParams: IPaginationQuery): Promise<IDomainMonitorPaginationData> {
        return instance.get('domains/monitor', { params: queryParams });
    },
    async updateDomainMonitor(data: IDomainMonitorPaginationItemData) {
        return instance.put(`domains/monitor/${data.id}`, data);
    },
    async deleteDomainMonitor(monitorId: number) {
        return instance.delete(`domains/monitor/${monitorId}`);
    },
    async getDomainGrowList(queryParams: IPaginationQuery): Promise<IDomainGrowPaginationData> {
        return instance.get('domains/grow', { params: queryParams });
    },
    async createDomainGrow(data: IDomainGrowCreateData) {
        return instance.post(`domains/grow`, data);
    },
    async deleteDomainGrow(domainGrowId: number) {
        return instance.delete(`domains/grow/${domainGrowId}`);
    },
    // module api
    async getTeamServerList(queryParams: IPaginationQuery): Promise<ITeamServerPaginationData> {
        return instance.get('modules/team_servers/', { params: queryParams });
    },
    async getRedirectorList(queryParams: IPaginationQuery): Promise<IRedirectorPaginationData> {
        return instance.get('modules/redirectors/', { params: queryParams });
    },
    async createTeamServer(data: ITeamServerCreate) {
        return instance.post('modules/team_servers/', data);
    },
    async deleteTeamServer(teamServerId: number) {
        return instance.delete(`modules/team_servers/${teamServerId}`);
    },
    async createRedirector(data: IRedirectorCreate) {
        return instance.post('modules/redirectors/', data);
    },
    async deleteRedirector(redirectorId: number) {
        return instance.delete(`modules/redirectors/${redirectorId}`);
    },
    async getRedirectorBeaconTypeSelections(): Promise<IEnumItem[]>  {
        return instance.get('modules/beacon_types');
    },
};
