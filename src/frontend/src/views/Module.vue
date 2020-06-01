<template>
    <v-card>
        <v-tabs background-color="transparent" grow v-model="tab">
            <v-tab :key="tabKey" v-for="(tabValue, tabKey) in tabChoices">{{ tabValue }}</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
            <v-tab-item key="manage">
                <v-col>
                    <v-data-table @update:page="updateTeamServerPaginationPageNum" @update:items-per-page="updateTeamServerPaginationPageSize" :headers="teamServerHeaders" :items="teamServerItems" :page.sync="teamServerTableParam.pageNum" :server-items-length="teamServerTableParam.total">
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                TeamServer
                            </v-toolbar>
                        </template>
                        <template v-slot:item.index="{ item }">
                            <span>{{ teamServerItems.indexOf(item)+1 }}</span>
                        </template>
                        <template v-slot:item.action="{ item }">
                            <v-btn class="ma-2" color="warning" @click="handleDeleteTeamServer(item)" :loading="teamServerActionLoading">
                                删除
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="teamServerDeleteDialog" persistent max-width="650">
                        <v-card>
                            <v-card-title class="headline lighten-2">
                                删除Team Server
                            </v-card-title>
                            <v-card-text>
                                <p>确定要删除吗，该操作会销毁服务器:</p>
                                <p>主机名: {{teamServerActionData.hostname}}</p>
                                <p v-if="teamServerActionData.ip">IP： {{ teamServerActionData.ip }}</p>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="info" text :loading="teamServerActionLoading" @click="deleteTeamServer">
                                    删除
                                </v-btn>
                                <v-btn color="blue-grey" text @click="teamServerDeleteDialog=false">
                                    关闭
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-col>
                <v-col>
                    <v-data-table @update:page="updateRedirectorPaginationPageNum" @update:items-per-page="updateRedirectorPaginationPageSize" :headers="redirectorHeaders" :items="redirectorItems" :page.sync="redirectorTableParam.pageNum" :server-items-length="redirectorTableParam.total">
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                Redirector
                            </v-toolbar>
                        </template>
                        <template v-slot:item.index="{ item }">
                            <span>{{ redirectorItems.indexOf(item)+1 }}</span>
                        </template>
                        <template v-slot:item.action="{ item }">
                            <v-btn class="ma-2" color="warning" @click="handleDeleteRedirector(item)" :loading="redirectorActionLoading">
                                删除
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="redirectorDeleteDialog" persistent max-width="650">
                        <v-card>
                            <v-card-title class="headline lighten-2">
                                删除 redirector
                            </v-card-title>
                            <v-card-text>
                                <p>确定要删除吗，该操作会销毁服务器:</p>
                                <p>主机名: {{redirectorActionData.hostname}}</p>
                                <p v-if="redirectorActionData.ip">IP： {{ redirectorActionData.ip }}</p>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="info" text :loading="redirectorActionLoading" @click="deleteRedirector">
                                    删除
                                </v-btn>
                                <v-btn color="blue-grey" text @click="redirectorDeleteDialog=false">
                                    关闭
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-col>
            </v-tab-item>
            <v-tab-item key="teamServer">
                <v-card>
                    <v-card-title>TeamServer配置</v-card-title>
                    <v-card-text>
                        <v-container>
                            <ValidationObserver ref="teamServerForm">
                                <v-row align="center">
                                    <v-col cols="6">
                                        <ValidationProvider name="端口" v-slot="{ errors }">
                                            <v-text-field persistent-hint hint="连接端口" :error-messages="errors" label="端口" v-model="teamServerCreateData.port"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="连接密码" :rules="validateRules.requiredData" v-slot="{ errors }">
                                            <v-text-field class="required" :error-messages="errors" label="连接密码" v-model="teamServerCreateData.password"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="C2profile" v-slot="{ errors }">
                                            <v-select :items="c2Selections" label="C2profile" :error-messages="errors" v-model="teamServerCreateData.c2ProfileId"></v-select>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="终止时间" v-slot="{ errors }">
                                            <v-text-field persistent-hint hint="Beacon kill date: YYYY-MM-DD" :error-messages="errors" label="终止时间" v-model="teamServerCreateData.killDate"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="CS下载链接" :rules="validateRules.url" v-slot="{ errors }">
                                            <v-text-field class="required" persistent-hint hint="CobaltStrike zip压缩包下载链接" :error-messages="errors" label="CS下载链接" v-model="teamServerCreateData.csDownloadUrl"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="解压密码" v-slot="{ errors }">
                                            <v-text-field persistent-hint hint="CobaltStrike压缩包解压密码" :error-messages="errors" label="解压密码" v-model="teamServerCreateData.zipPassword"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="备注" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" label="备注" v-model="teamServerCreateData.remark"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                </v-row>
                            </ValidationObserver>
                        </v-container>
                    </v-card-text>
                    <v-divider></v-divider>
                    <v-card>
                        <v-card-title>VPS选择</v-card-title>
                        <v-card-text>
                            <v-container>
                                <ValidationObserver ref="teamServerVpsForm">
                                    <v-row align="center">
                                        <v-col cols="3">
                                        </v-col>
                                        <v-col cols="6">
                                            <ValidationProvider name="server" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                <v-select :items="vpsSelections" label="server" :error-messages="errors" v-model="teamServerCreateData.vpsId"></v-select>
                                            </ValidationProvider>
                                        </v-col>
                                    </v-row>
                                </ValidationObserver>
                            </v-container>
                        </v-card-text>
                    </v-card>
                    <v-divider></v-divider>
                    <v-card-actions class="justify-center">
                        <v-btn large color="info" :loading="teamServerCreateLoading" @click="createTeamServer">开始部署</v-btn>
                    </v-card-actions>
                </v-card>
            </v-tab-item>
            <v-tab-item key="redirector">
                <v-card>
                    <v-card-title>Redirector配置</v-card-title>
                    <v-card-text>
                        <v-container>
                            <ValidationObserver ref="teamServerForm">
                                <v-row align="center">
                                    <v-col cols="4">
                                        <ValidationProvider name="Beacon" :rules="validateRules.requiredData" v-slot="{ errors }">
                                            <v-select :items="beaconSelections" v-model="redirectorCreateData.beaconType" label="Beacon Type" :error-messages="errors"></v-select>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="4">
                                        <ValidationProvider name="TS服务器" :rules="validateRules.requiredData" v-slot="{ errors }">
                                            <v-select :items="teamServerSelections" v-model="redirectorCreateData.teamServerId" label="TS服务器" :error-messages="errors"></v-select>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="4">
                                        <ValidationProvider name="监听端口" :rules="validateRules.port" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" v-model="redirectorCreateData.listenerPort" label="监听端口"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="跳转域名" :rules="validateRules.requiredData" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" v-model="redirectorCreateData.redirectDomain" label="跳转域名"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                    <v-col cols="6">
                                        <ValidationProvider name="备注" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" v-model="redirectorCreateData.remark" label="备注"></v-text-field>
                                        </ValidationProvider>
                                    </v-col>
                                </v-row>
                            </ValidationObserver>
                        </v-container>
                    </v-card-text>
                    <v-divider></v-divider>
                    <v-card>
                        <v-card-title>VPS选择</v-card-title>
                        <v-card-text>
                            <v-container>
                                <ValidationObserver ref="teamServerVpsForm">
                                    <v-row align="center">
                                        <v-col cols="3">
                                        </v-col>
                                        <v-col cols="6">
                                            <ValidationProvider name="server" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                <v-select :items="vpsSelections" v-model="redirectorCreateData.vpsId" label="server" :error-messages="errors"></v-select>
                                            </ValidationProvider>
                                        </v-col>
                                    </v-row>
                                </ValidationObserver>
                            </v-container>
                        </v-card-text>
                    </v-card>
                    <v-card>
                        <v-card-title>域名选择</v-card-title>
                        <v-card-text>
                            <v-container>
                                <ValidationObserver ref="teamServerVpsForm">
                                    <v-row align="center">
                                        <v-col cols="3">
                                        </v-col>
                                        <v-col cols="6">
                                            <ValidationProvider name="domain" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                <v-select :items="domainSelections" v-model="redirectorCreateData.domainId" label="domain" :error-messages="errors"></v-select>
                                            </ValidationProvider>
                                        </v-col>
                                    </v-row>
                                </ValidationObserver>
                            </v-container>
                        </v-card-text>
                    </v-card>
                    <v-divider></v-divider>
                    <v-card-actions class="justify-center">
                        <v-btn large color="info" :loading="redirectorCreateLoading" @click="createRedirector">开始部署</v-btn>
                    </v-card-actions>
                </v-card>
            </v-tab-item>
        </v-tabs-items>
    </v-card>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import { DataTableHeader } from 'vuetify/types';

import { api } from '@/api';
import {
    ISelectionItem,
    ITableParam,
    IVuetifySelectItem,
    IVForm,
    IPaginationQuery,
} from '@/interfaces/index';
import {
    ITeamServerCreate,
    IRedirectorCreateData,
    ITeamServerItemData,
} from '@/interfaces/module';
import { validateRules } from '@/plugins/vee-validate';
import {
    dispatchGetRedirectorList,
    dispatchGetTeamServerList,
    dispatchCreateTeamServer,
    dispatchCreateRedirector,
    dispatchDestroyRedirector,
    dispatchDestroyTeamServer,
} from '@/store/main/actions';
import { readAvailableIsp } from '@/store/main/getters';
import { formReset, formValidate } from '@/utils';
import { validate } from 'vee-validate';
import { IRedirectorItemData } from '../interfaces/module';


@Component
export default class ModuleManage extends Vue {
    public pageName = '组件管理';
    public tab = null;
    public tabChoices = {
        manage: '管理',
        teamServer: 'TeamServer部署',
        redirector: 'Redirector部署',
    };

    public teamServerHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: 'hostname', value: 'hostname', sortable: false },
        { text: 'IP', value: 'ip', sortable: false },
        { text: 'Port', value: 'port', sortable: false },
        { text: 'Password', value: 'password', sortable: false },
        { text: 'C2Profile', value: 'c2ProfileName', sortable: false },
        { text: 'Kill Date', value: 'killDate', sortable: false },
        { text: 'ISP', value: 'ispProviderName', sortable: false },
        { text: 'Remark', value: 'remark', sortable: false },
        { text: '操作', value: 'action', sortable: false },
    ];
    public teamServerItems: any = [];
    public teamServerTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public teamServerCreateData = {} as ITeamServerCreate;
    public teamServerCreateLoading = false;
    public teamServerDeleteDialog = false;
    public teamServerActionLoading = false;
    public teamServerActionData = {} as ITeamServerItemData;
    public redirectorHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: 'Beacon Type', value: 'beaconTypeName', sortable: false },
        { text: '监听端口', value: 'listenerPort', sortable: false },
        { text: '跳转域名', value: 'redirectDomain', sortable: false },
        { text: 'VPS IP', value: 'ip', sortable: false },
        { text: 'VPS Hostname', value: 'hostname', sortable: false },
        { text: '域名', value: 'domainName', sortable: false },
        { text: 'Remark', value: 'remark', sortable: false },
        { text: '操作', value: 'action', sortable: false },
    ];
    public redirectorItems: any = [];
    public redirectorTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public redirectorCreateData = {} as IRedirectorCreateData;
    public redirectorCreateLoading = false;
    public redirectorActionData = {} as IRedirectorItemData;
    public redirectorActionLoading = false;
    public redirectorDeleteDialog = false;
    public vpsSelections: ISelectionItem[] = [];
    public c2Selections: ISelectionItem[] = [];
    public domainSelections: ISelectionItem[] = [];
    public beaconSelections: ISelectionItem[] = [];
    public teamServerSelections: ISelectionItem[] = [];

    public get validateRules() {
        return validateRules;
    }
    public get teamServerPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.teamServerTableParam.pageNum,
            perPage: this.teamServerTableParam.pageSize,
        };
        return queryData;
    }
    public get redirectorPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.redirectorTableParam.pageNum,
            perPage: this.redirectorTableParam.pageSize,
        };
        return queryData;
    }
    public updateTeamServerPaginationPageNum(pageNum: number) {
        this.teamServerTableParam.pageNum = pageNum;
    }
    public updateTeamServerPaginationPageSize(pageSize: number) {
        this.teamServerTableParam.pageSize = pageSize;
    }
    public updateRedirectorPaginationPageNum(pageNum: number) {
        this.redirectorTableParam.pageNum = pageNum;
    }
    public updateRedirectorPaginationPageSize(pageSize: number) {
        this.redirectorTableParam.pageSize = pageSize;
    }
    @Watch('teamServerTableParam', { immediate: true, deep: true })
    public async onTeamServerPaginationChanged() {
        await this.getTeamServerList();
    }
    @Watch('redirectorTableParam', { immediate: true, deep: true })
    public async onRedirectorPaginationChanged() {
        await this.getRedirectorList();
    }

    public async getVpsSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const vpsListData = await api.getVpsList(queryParam);

        this.vpsSelections = vpsListData.items.map((item) => {
            return {
                text: item.hostname,
                value: item.id,
            };
        });
    }
    public async getC2Selections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const c2Data = await api.getC2ProfileList(queryParam);

        this.c2Selections = c2Data.items.map((item) => {
            return {
                text: item.profileName,
                value: item.id,
            };
        });
    }
    public async getTeamServerSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const teamServerData = await api.getTeamServerList(queryParam);

        this.teamServerSelections = teamServerData.items.map((item) => {
            return {
                text: item.hostname,
                value: item.id,
            };
        });
    }
    public async getDomainSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const domainData = await api.getDomainList(queryParam);

        this.domainSelections = domainData.items.map((item) => {
            return {
                text: item.domain,
                value: item.id,
            };
        });
    }
    public async getRedirectorBeaconTypeSelections() {
        const beaconData = await api.getRedirectorBeaconTypeSelections();
        this.beaconSelections = beaconData.map((item) => {
            return {
                text: item.name,
                value: item.code,
            };
        });
    }
    public async getTeamServerList() {
        const teamServerListData = await dispatchGetTeamServerList(this.$store, this.teamServerPaginationQueryParam);

        this.teamServerTableParam.total = teamServerListData.total;
        this.teamServerItems = teamServerListData.items;
    }
    public async getRedirectorList() {
        const redirectorListData = await dispatchGetRedirectorList(this.$store, this.redirectorPaginationQueryParam);
        this.redirectorTableParam.total = redirectorListData.total;
        this.redirectorItems = redirectorListData.items;
    }
    public createTeamServer() {
        dispatchCreateTeamServer(this.$store, this.teamServerCreateData);
    }
    public createRedirector() {
        dispatchCreateRedirector(this.$store, this.redirectorCreateData);
    }
    public handleDeleteTeamServer(item) {
        this.teamServerDeleteDialog = true;
        this.teamServerActionData = item;
    }
    public handleDeleteRedirector(item) {
        this.redirectorActionData = item;
        this.redirectorDeleteDialog = true;
    }
    public deleteTeamServer() {
        this.teamServerActionLoading = true;
        dispatchDestroyTeamServer(this.$store, this.teamServerActionData.id).then(() => {
            this.teamServerDeleteDialog = false;
            this.getTeamServerList();
        }).finally(() => {
            this.teamServerActionLoading = false;
        });
    }
    public deleteRedirector() {
        this.redirectorActionLoading = true;

        dispatchDestroyRedirector(this.$store, this.redirectorActionData.id).then(() => {
            this.redirectorDeleteDialog = false;
            this.getRedirectorList();
        }).finally(() => {
            this.redirectorActionLoading = false;
        });
    }
    public created() {
        this.getVpsSelections();
        this.getC2Selections();
        this.getDomainSelections();
        this.getTeamServerSelections();
        this.getRedirectorBeaconTypeSelections();
    }
}
</script>
