<template>
    <v-card>
        <v-tabs background-color="transparent" grow v-model="tab">
            <v-tab :key="tabKey" v-for="(tabValue, tabKey) in tabChoices">{{ tabValue }}</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
            <v-tab-item key="isp">
                <v-card>
                    <v-data-table @update:page="updateIspPaginationPageNum" @update:items-per-page="updateIspPaginationPageSize" :headers="ispHeaders" :items="ispItems" :page.sync="ispTableParam.pageNum" :server-items-length="ispTableParam.total" :footer-props="tableFooterProps">
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                <v-toolbar-title>
                                    <v-tabs v-model="ispTabIndex">
                                        <v-tab v-for="tabItem in ispTabItems" :key="tabItem.value">
                                            {{ tabItem.label }}
                                        </v-tab>
                                    </v-tabs>
                                </v-toolbar-title>
                                <v-divider class="mx-4" inset vertical></v-divider>
                                <v-dialog v-model="ispCreateDialog" width="500">
                                    <template v-slot:activator="{ on }">
                                        <v-btn color="primary lighten-2" v-on="on">
                                            添加
                                        </v-btn>
                                    </template>

                                    <v-card>
                                        <v-card-title class="headline  lighten-2">
                                            {{ ispCreateDialogTitle }}
                                        </v-card-title>
                                        <v-card-text>
                                            <ValidationObserver ref="ispCreateForm">
                                                <v-form>
                                                    <ValidationProvider name="提供商" :rules="validateRules.ispType" v-slot="{ errors }">
                                                        <v-select v-model="ispCreateData.provider" :items="availableIspItems" label="提供商" :error-messages="errors"></v-select>
                                                    </ValidationProvider>
                                                    <ValidationProvider name="API Key" :rules="validateRules.ispApiKey" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" label="API KEY" v-model.trim="ispCreateData.apiKey"></v-text-field>
                                                    </ValidationProvider>
                                                    <ValidationProvider name="备注" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" v-model="ispCreateData.remark" label="备注"></v-text-field>
                                                    </ValidationProvider>
                                                    <ValidationProvider name="测试用KEY" v-slot="{ errors }">
                                                        <v-checkbox :error-messages="errors" v-model="ispCreateData.isTest" label="属于测试专用KEY（比如Namesilo的sandbox api key）" type="checkbox"></v-checkbox>
                                                    </ValidationProvider>
                                                </v-form>
                                            </ValidationObserver>
                                        </v-card-text>
                                        <v-divider></v-divider>

                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="info" text @click="createIspProfile">
                                                提交
                                            </v-btn>
                                            <v-btn color="blue-grey" text @click="closeIspCreateDialog">
                                                关闭
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                                <v-col v-if="activedIspTabValue === 'vps'">
                                    <v-btn color="primary lighten-2" :loading="ispReloadButtonLoading" @click="handleReloadIspConfig">
                                        {{ispReloadButtonText}}
                                        <template v-slot:loader>
                                            <span>{{ispReloadButtonLoadingText}}</span>
                                        </template>
                                    </v-btn>
                                </v-col>

                                <v-spacer></v-spacer>
                            </v-toolbar>
                        </template>
                        <template v-slot:item.index="{ item }">
                            <span>{{ ispItems.indexOf(item)+1 }}</span>
                        </template>
                        <template v-slot:item.isTest="{ item }">
                            <v-switch v-model="item.isTest" disabled></v-switch>
                        </template>
                        <template v-slot:item.actions="{ item }">
                            <v-btn class="mx-2" fab small color="primary" @click="editIspItem(item)">
                                <v-icon dark>edit</v-icon>
                            </v-btn>
                            <v-btn class="mx-2" fab small color="warning" @click="deleteIspItem(item)">
                                <v-icon dark>delete</v-icon>
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="ispEditDialog" max-width="600">
                        <v-card>
                            <v-card-title class="headline">修改 ISP</v-card-title>
                            <v-card-text>
                                <ValidationObserver ref="ispUpdateForm">
                                    <v-form>
                                        <ValidationProvider name="提供商" :rules="validateRules.ispType" v-slot="{ errors }">
                                            <v-select disabled v-model="ispActionData.provider" :items="availableIspItems" label="提供商" :error-messages="errors"></v-select>
                                        </ValidationProvider>
                                        <v-text-field disabled label="API URL" v-model="ispActionData.ispApiUrl"></v-text-field>
                                        <ValidationProvider name="API Key" :rules="validateRules.ispApiKey" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" label="API KEY" v-model.trim="ispActionData.apiKey"></v-text-field>
                                        </ValidationProvider>
                                        <ValidationProvider name="备注" v-slot="{ errors }">
                                            <v-text-field :error-messages="errors" v-model.trim="ispActionData.remark" label="备注"></v-text-field>
                                        </ValidationProvider>
                                        <ValidationProvider name="测试用KEY" v-slot="{ errors }">
                                            <v-checkbox :error-messages="errors" v-model="ispActionData.isTest" label="属于测试专用KEY（比如Namesilo的sandbox api key）" type="checkbox"></v-checkbox>
                                        </ValidationProvider>
                                    </v-form>
                                </ValidationObserver>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="green darken-1" text @click="handleUpdateIsp">
                                    提交
                                </v-btn>
                                <v-btn color="darken-1" text @click="ispEditDialog=false">
                                    取消
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="ispDeleteDialog" max-width="500">
                        <v-card>
                            <v-card-title class="headline">操作确认</v-card-title>
                            <v-card-text>
                                确定要删除 {{ispActionData.providerName}} 的KEY「{{ ispActionData.apiKey }}」吗？
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="warning darken-1" text @click="handleDeleteIsp">
                                    提交
                                </v-btn>
                                <v-btn color="green darken-1" text @click="ispDeleteDialog=false">
                                    取消
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-card>
            </v-tab-item>
            <v-tab-item key="c2">
                <v-row>
                    <v-col>
                        <v-card>
                            <v-card-text>
                                <v-container>
                                    <ValidationObserver ref="c2CreateForm">
                                        <v-row align="center">
                                            <v-col cols="3">
                                                <ValidationProvider name="名称" :rules="validateRules.c2ProfileName" v-slot="{ errors }">
                                                    <v-text-field :error-messages="errors" label="名称" v-model="c2CreateData.name"></v-text-field>
                                                </ValidationProvider>
                                            </v-col>
                                            <v-col cols="3">
                                                <ValidationProvider name="备注" v-slot="{ errors }">
                                                    <v-text-field :error-messages="errors" label="备注" v-model="c2CreateData.remark"></v-text-field>
                                                </ValidationProvider>
                                            </v-col>
                                            <v-col cols="3">
                                                <ValidationProvider name="profile" :rules="validateRules.c2ProfileFile" v-slot="{ errors }">
                                                    <v-file-input :error-messages="errors" accept=".profile" label="C2 Profile" v-model="c2CreateData.profile" show-size></v-file-input>
                                                </ValidationProvider>
                                            </v-col>
                                            <v-col cols="3">
                                                <v-btn bottom @click="createC2Profile" color="success">添加</v-btn>
                                            </v-col>
                                        </v-row>
                                    </ValidationObserver>
                                </v-container>
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>
                <v-row>
                    <v-col>
                        <v-card>
                            <v-dialog v-model="c2EditDialog" width="500">
                                <v-card>
                                    <v-card-title class="headline  lighten-2">C2 Profile 编辑</v-card-title>
                                    <v-card-text>
                                        <ValidationObserver ref="c2EditedForm">
                                            <v-row align="center">
                                                <v-col cols="6">
                                                    <ValidationProvider name="名称" :rules="validateRules.c2ProfileName" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" label="名称" v-model="c2ActionData.name"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="6">
                                                    <ValidationProvider name="备注" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" label="备注" v-model="c2ActionData.remark"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="12">
                                                    <v-text-field label="文件名" v-model="c2ActionData.profileName" outlined readonly></v-text-field>
                                                </v-col>
                                                <v-col cols="12">
                                                    <v-textarea v-model="c2ActionData.profileContent" label="profile" outlined readonly></v-textarea>
                                                </v-col>
                                            </v-row>
                                        </ValidationObserver>
                                    </v-card-text>
                                    <v-divider></v-divider>

                                    <v-card-actions>
                                        <v-spacer></v-spacer>
                                        <v-btn color="info" text @click="handleUpdateC2Profile">
                                            提交
                                        </v-btn>
                                        <v-btn color="blue-grey" text @click="c2EditDialog=false">
                                            关闭
                                        </v-btn>
                                    </v-card-actions>
                                </v-card>
                            </v-dialog>
                            <v-dialog v-model="c2DeleteDialog" max-width="500">
                                <v-card>
                                    <v-card-title class="headline">操作确认</v-card-title>
                                    <v-card-text>
                                        确定要删除 {{c2ActionData.name}} 及其profile 「{{c2ActionData.profileName}}」吗？
                                    </v-card-text>
                                    <v-card-actions>
                                        <v-spacer></v-spacer>
                                        <v-btn color="warning darken-1" text @click="handleDeleteC2Profile">
                                            确定
                                        </v-btn>
                                        <v-btn color="green darken-1" text @click="c2DeleteDialog=false">
                                            取消
                                        </v-btn>
                                    </v-card-actions>
                                </v-card>
                            </v-dialog>
                            <v-data-table @update:page="updateC2PaginationPageNum" @update:items-per-page="updateC2PaginationPageSize" :headers="c2Headers" :items="c2Items" :page.sync="c2TableParam.c2PageNum" :server-items-length="c2TableParam.total" :footer-props="tableFooterProps">
                                <template v-slot:item.index="{ item }">
                                    <span>{{ c2Items.indexOf(item)+1 }}</span>
                                </template>
                                <template v-slot:item.isTest="{ item }">
                                    <v-switch v-model="item.isTest" disabled></v-switch>
                                </template>
                                <template v-slot:item.actions="{ item }">
                                    <v-btn class="mx-2" fab small color="primary" @click="editC2Item(item)">
                                        <v-icon dark>edit</v-icon>
                                    </v-btn>
                                    <v-btn class="mx-2" fab small color="warning" @click="deleteC2Item(item)">
                                        <v-icon dark>delete</v-icon>
                                    </v-btn>
                                </template>
                            </v-data-table>
                        </v-card>
                    </v-col>
                </v-row>
            </v-tab-item>
            <v-tab-item key="sshKey">
                <v-card>
                    <v-card-title>SSH Key 配置</v-card-title>
                    <v-card-text>
                        <v-alert outlined color="teal" dismissible>
                            <div>该 SSH Key 用于系统跟外界（VPS 等）进行 SSH 通讯， 若不存在请先创建</div>
                        </v-alert>
                        <v-container fluid v-if="sshPrivateKey">
                            <v-row>
                                <v-col cols="2">
                                    <v-subheader>Private Key</v-subheader>
                                </v-col>
                                <v-col cols="8">
                                    <v-textarea readonly solo v-model="sshPrivateKey"></v-textarea>
                                </v-col>
                            </v-row>

                            <v-row>
                                <v-col cols="2">
                                    <v-subheader>Public Key</v-subheader>
                                </v-col>
                                <v-col cols="8">
                                    <v-textarea readonly solo v-model="sshPublicKey"></v-textarea>
                                </v-col>
                            </v-row>
                        </v-container>
                        <v-container fluid v-else>
                            <v-layout align-center justify-center>
                                <v-col cols="6">
                                    <v-btn block color="info" :loading="sshConfigLoading" @click="createSshConfig">创建SSH Key</v-btn>
                                </v-col>
                            </v-layout>
                        </v-container>
                    </v-card-text>
                </v-card>
            </v-tab-item>
            <v-tab-item key="siteTemplate">
                <v-card>
                    <v-card-title>网站模板配置</v-card-title>
                    <v-card-text>
                        <v-alert outlined color="blue">
                            <div>用于培养域名，由Nginx+静态网站两部分构成，请上传打包静态网站文件（zip）</div>
                        </v-alert>
                        <v-row>
                            <v-col>
                                <v-card>
                                    <v-card-text>
                                        <v-container>
                                            <ValidationObserver ref="siteTemplateCreateForm">
                                                <v-row align="center">
                                                    <v-col cols="3">
                                                        <ValidationProvider name="name" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-text-field :error-messages="errors" label="名称" v-model="siteTemplateCreateData.name"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="3">
                                                        <ValidationProvider name="remark" :rules="validateRules.remark" v-slot="{ errors }">
                                                            <v-text-field :error-messages="errors" label="备注" v-model="siteTemplateCreateData.remark"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="3">
                                                        <ValidationProvider name="zipFile" :rules="validateRules.zipFile" v-slot="{ errors }">
                                                            <v-file-input :error-messages="errors" accept=".zip" label="打包文件" v-model="siteTemplateCreateData.zipFile" show-size></v-file-input>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="3">
                                                        <v-btn bottom class="ma-2" @click="createSiteTemplate" color="success">添加</v-btn>
                                                        <v-btn bottom class="ma-2" @click="clearSiteTemplateForm" color="info">清空</v-btn>
                                                    </v-col>
                                                </v-row>
                                            </ValidationObserver>
                                        </v-container>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                        <v-row>
                            <v-col>
                                <v-card>
                                    <v-data-table @update:page="updateSiteTemplatePaginationPageNum" @update:items-per-page="updateSiteTemplatePaginationPageSize" :headers="siteTemplateHeaders" :items="siteTemplateItems" :page.sync="siteTemplateTableParam.pageNum" :server-items-length="siteTemplateTableParam.total" :footer-props="tableFooterProps">
                                        <template v-slot:item.index="{ item }">
                                            <span>{{ siteTemplateItems.indexOf(item)+1 }}</span>
                                        </template>
                                        <template v-slot:item.actions="{ item }">
                                            <v-btn class="ma-2" color="info" @click="handleUpdateSiteTemplate(item)">
                                                编辑
                                            </v-btn>
                                            <v-btn class="ma-2" color="warning" @click="handleDeleteSiteTemplate(item)">
                                                删除
                                            </v-btn>
                                        </template>
                                    </v-data-table>
                                </v-card>
                            </v-col>
                        </v-row>
                    </v-card-text>
                    <v-dialog v-model="siteTemplateDeleteDialog" max-width="500">
                        <v-card>
                            <v-card-title class="headline">操作确认</v-card-title>
                            <v-card-text>
                                确定要删除模板 {{ siteTemplateActionData.name}} 吗？
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="warning darken-1" text @click="deleteSiteTemplate">
                                    确定
                                </v-btn>
                                <v-btn color="green darken-1" text @click="siteTemplateDeleteDialog=false">
                                    取消
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="siteTemplateUpdateDialog" max-width="500">
                        <v-card>
                            <v-card-title class="headline">更新模板</v-card-title>
                            <v-card-text>
                                <v-container>
                                    <ValidationObserver ref="siteTemplateUpdateForm">
                                        <v-row align="center">
                                            <v-col cols="12">
                                                <ValidationProvider name="name" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                    <v-text-field :error-messages="errors" label="名称" v-model="siteTemplateActionData.name"></v-text-field>
                                                </ValidationProvider>
                                            </v-col>
                                            <v-col cols="12">
                                                <ValidationProvider name="remark" :rules="validateRules.remark" v-slot="{ errors }">
                                                    <v-text-field :error-messages="errors" label="备注" v-model="siteTemplateActionData.remark"></v-text-field>
                                                </ValidationProvider>
                                            </v-col>
                                            <v-col cols="12" v-if="!updateSiteTemplateZipFile">
                                                <v-btn block color="info" @click="updateSiteTemplateZipFile = true">上传新模板文件</v-btn>
                                            </v-col>
                                            <v-col cols="12" v-if="updateSiteTemplateZipFile">
                                                <ValidationProvider name="zipFile" :rules="validateRules.zipFile" v-slot="{ errors }">
                                                    <v-file-input :error-messages="errors" accept=".zip" label="打包文件" v-model="siteTemplateActionData.zipFile" show-size></v-file-input>
                                                </ValidationProvider>
                                            </v-col>
                                        </v-row>
                                    </ValidationObserver>
                                </v-container>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="warning darken-1" text @click="updateSiteTemplate">
                                    确定
                                </v-btn>
                                <v-btn color="green darken-1" text @click="handleCancleUpdateSiteTemplate">
                                    取消
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-card>
            </v-tab-item>
        </v-tabs-items>
    </v-card>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import { DataOptions } from 'vuetify/types';

import { api } from '@/api';
import {
    IC2ProfileCreate,
    IPaginationQuery,
    IC2PaginationItemData,
    IIspPaginationItemData,
    IIspPaginationQuery,
    IIspProfileCreate,
    ITableParam,
    IVuetifySelectItem,
    IVForm,
    IC2PaginationQuery,
} from '@/interfaces';
import { ISiteTemplateCreate, ISiteTemplateUpdate, ISiteTemplatePaginationItemData } from '@/interfaces/config';
import { ISshConfigData } from '@/interfaces/config';
import { validateRules } from '@/plugins/vee-validate';
import {
    dispatchCreateC2Profile,
    dispatchGetC2Profile,
    dispatchGetC2ProfileList,
    dispatchGetSshConfig,
    dispatchCreateIspProfile,
    dispatchCreateSshConfig,
    dispatchGetAvailableIsp,
    dispatchGetIspProfileList,
    dispatchCreateSiteTemplate,
    dispatchGetSiteTemplateList,
} from '@/store/main/actions';
import { readAvailableIsp } from '@/store/main/getters';
import { formReset, formValidate } from '@/utils';
import { validate } from 'vee-validate';


@Component
export default class ConfigManage extends Vue {
    public pageName = '配置管理';
    public tab = null;
    public tabChoices = {
        isp: 'ISP',
        c2: 'C2 PROFILE',
        sshKey: 'SSH Key',
        siteTemplate: 'Site Template',
    };

    // isp data
    public ispTabIndex = 0;
    public ispTabItems = [
        { label: '域名', value: 'domain' },
        { label: 'VPS', value: 'vps' },
    ];
    public ispHeaders = [
        { text: '#', value: 'index' },
        { text: 'ISP', value: 'providerName', sortable: false },
        { text: 'Key', value: 'apiKey', sortable: false },
        { text: '测试模式', value: 'isTest', sortable: false },
        { text: '更新时间', value: 'updatedOn', sortable: false, width: '15%' },
        { text: '备注', value: 'remark', sortable: false },
        { text: '操作', value: 'actions', sortable: false },
    ];
    public ispItems: IIspPaginationItemData[] = [];
    public ispTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public ispCreateDialog = false;
    public ispEditDialog = false;
    public ispDeleteDialog = false;
    public ispCreateData = {} as IIspProfileCreate;
    public ispActionData = {} as IIspPaginationItemData;
    public ispReloadButtonLoading = false;

    // c2 profile data
    public c2Headers = [
        { text: '#', value: 'index', sortable: false },
        { text: 'name', value: 'name', sortable: false },
        { text: '文件名', value: 'profileName', sortable: false },
        { text: '更新时间', value: 'updatedOn', sortable: false, width: '15%' },
        { text: '备注', value: 'remark', sortable: false },
        { text: '操作', value: 'actions', sortable: false },
    ];
    public c2Items: IC2PaginationItemData[] = [];
    public c2TableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public c2EditDialog = false;
    public c2DeleteDialog = false;
    public c2CreateData = {} as IC2ProfileCreate;
    public c2ActionData = {} as IC2PaginationItemData;

    // ssh config data
    public sshConfig = {} as ISshConfigData;
    public sshConfigLoading = false;

    // site template data
    public siteTemplateCreateData = {} as ISiteTemplateCreate;
    public siteTemplateHeaders = [
        { text: '#', value: 'index', sortable: false },
        { text: '模版名称', value: 'name', sortable: false },
        { text: '压缩包名称', value: 'zipFileName', sortable: false },
        { text: '压缩包大小', value: 'zipFileSize', sortable: false },
        { text: '更新时间', value: 'updatedOn', sortable: false },
        { text: '备注', value: 'remark', sortable: false },
        { text: '操作', value: 'actions', sortable: false },
    ];
    public siteTemplateItems: ISiteTemplatePaginationItemData[] = [];
    public siteTemplateActionData = {} as ISiteTemplatePaginationItemData;
    public siteTemplateDeleteDialog = false;
    public siteTemplateUpdateDialog = false;
    public updateSiteTemplateZipFile = false;
    public siteTemplateTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };

    // public data
    public tableFooterProps = {
        itemsPerPageOptions: [10, 20, 50, 100],
    };

    public async updateIspPaginationPageNum(pageNum) {
        this.ispTableParam.pageNum = pageNum;
    }
    public async updateIspPaginationPageSize(pageSize) {
        this.ispTableParam.pageSize = pageSize;
    }

    public closeIspCreateDialog() {
        this.ispCreateDialog = false;
    }
    public editIspItem(ispItem: IIspPaginationItemData) {
        this.ispActionData = Object.assign({}, ispItem);
        this.ispEditDialog = true;
    }
    public deleteIspItem(ispItem: IIspPaginationItemData) {
        this.ispActionData = Object.assign({}, ispItem);
        this.ispDeleteDialog = true;
    }
    public handleReloadIspConfig() {
        this.ispReloadButtonLoading = true;
        api.reloadIspConfig(this.activedIspTabValue).then(
        ).finally(() => {
            this.ispReloadButtonLoading = false;
        });
    }
    public handleUpdateIsp() {
        api.updateIspProfile(this.ispActionData).then((res) => {
            this.ispEditDialog = false;
            this.getIspProfileList();
        });
    }
    public handleDeleteIsp() {
        api.deleteIspProfile(Number(this.ispActionData.id)).then((res) => {
            this.ispDeleteDialog = false;
            this.getIspProfileList();
        });
    }
    public createIspProfile() {
        this.ispCreateForm.validate().then(async (validated) => {
            if (validated) {
                const paylaod = {
                    type: this.ispTabItems[this.ispTabIndex].value,
                    profile: this.ispCreateData,
                };
                await dispatchCreateIspProfile(this.$store, paylaod);
                this.ispCreateData = {} as IIspProfileCreate;
                await this.ispCreateForm.reset();
                await this.getIspProfileList();
                this.closeIspCreateDialog();
            }
        });
    }
    public async getIspProfileList() {
        const payload = {
            query: this.ispPaginationQueryParam,
            type: this.activedIspTabValue,
        };
        const profileList = await dispatchGetIspProfileList(this.$store, payload);
        this.ispTableParam.total = profileList.total !== null ? profileList.total : 0;
        this.ispItems = profileList.items;
    }

    public get c2CreateForm(): IVForm {
        return this.$refs.c2CreateForm as IVForm;
    }
    public createC2Profile() {
        this.c2CreateForm.validate().then(async (validated) => {
            if (validated) {
                await dispatchCreateC2Profile(this.$store, this.c2CreateData);
                this.c2CreateData = {} as IC2ProfileCreate;
                this.c2CreateForm.reset();
                this.getC2ProfileList();
            }
        });
    }
    public editC2Item(c2Item: IC2PaginationItemData) {
        this.c2ActionData = Object.assign({}, c2Item);
        this.c2EditDialog = true;
    }
    public handleUpdateC2Profile() {
        api.updateC2Profile(this.c2ActionData).then((res) => {
            this.c2EditDialog = false;
            this.getC2ProfileList();
        });
    }
    public deleteC2Item(c2Item: IC2PaginationItemData) {
        this.c2ActionData = Object.assign({}, c2Item);
        this.c2DeleteDialog = true;
    }
    public handleDeleteC2Profile() {
        api.deleteC2Profile(this.c2ActionData.id).then(() => {
            this.c2DeleteDialog = false;
            this.getC2ProfileList();
        });
    }
    public updateC2PaginationPageNum(pageNum: number) {
        this.c2TableParam.pageNum = pageNum;
    }
    public updateC2PaginationPageSize(pageSize: number) {
        this.c2TableParam.pageSize = pageSize;
    }
    public async getC2ProfileList() {
        const profileList = await dispatchGetC2ProfileList(this.$store, this.c2PaginationQueryParam);
        this.c2TableParam.total = profileList.total !== null ? profileList.total : 0;
        this.c2Items = profileList.items;
    }

    public get validateRules() {
        return validateRules;
    }
    public get activedIspTabLable() {
        return this.ispTabItems[this.ispTabIndex].label;
    }
    public get activedIspTabValue() {
        return this.ispTabItems[this.ispTabIndex].value;
    }

    public get ispCreateDialogTitle() {
        return `${this.ispTabItems[this.ispTabIndex].label} 添加`;
    }
    public get ispReloadButtonText() {
        return `刷新${this.ispTabItems[this.ispTabIndex].label}配置`;
    }
    public get ispReloadButtonLoadingText() {
        return `读取${this.ispTabItems[this.ispTabIndex].label}配置中...`;
    }
    public get availableIspItems() {
        const ispData = readAvailableIsp(this.$store);
        const ispType = this.ispTabItems[this.ispTabIndex].value;

        const availableIpsList: IVuetifySelectItem[] = [];

        if (ispType && ispData) {
            for (const isp of ispData[ispType]) {
                availableIpsList.push({
                    text: isp.name,
                    value: isp.code,
                });
            }
        }
        return availableIpsList;
    }
    public get ispCreateForm(): IVForm {
        return this.$refs.ispCreateForm as IVForm;
    }
    public get ispPaginationQueryParam() {
        const queryData: IIspPaginationQuery = {
            page: this.ispTableParam.pageNum,
            perPage: this.ispTableParam.pageSize,
        };
        return queryData;
    }
    public get c2PaginationQueryParam() {
        const queryData: IC2PaginationQuery = {
            page: this.c2TableParam.pageNum,
            perPage: this.c2TableParam.pageSize,
        };
        return queryData;
    }

    public get sshPrivateKey() {
        return this.sshConfig.privateKey ? this.sshConfig.privateKey : null;
    }
    public get sshPublicKey() {
        return this.sshConfig.publicKey ? this.sshConfig.publicKey : null;
    }
    public async getSshKeyConfig() {
        const sshKeyConfig = await dispatchGetSshConfig(this.$store);
        this.sshConfig = sshKeyConfig;
    }
    public async createSshConfig() {
        this.sshConfigLoading = true;
        dispatchCreateSshConfig(this.$store).then((config) => {
            this.sshConfig = config;
        }).finally(() => {
            this.sshConfigLoading = false;
        });
    }

    public async updateSiteTemplatePaginationPageNum(pageNum) {
        this.siteTemplateTableParam.pageNum = pageNum;
    }
    public async updateSiteTemplatePaginationPageSize(pageSize) {
        this.siteTemplateTableParam.pageSize = pageSize;
    }
    public get siteTemplatePaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.siteTemplateTableParam.pageNum,
            perPage: this.siteTemplateTableParam.pageSize,
        };
        return queryData;
    }
    public get siteTemplateCreateForm(): IVForm {
        return this.$refs.siteTemplateCreateForm as IVForm;
    }
    public async getSiteTemplateList() {
        const siteTemplateList = await dispatchGetSiteTemplateList(
            this.$store, this.siteTemplatePaginationQueryParam,
        );

        this.siteTemplateTableParam.total = siteTemplateList.total;
        this.siteTemplateItems = siteTemplateList.items;
    }
    public async createSiteTemplate() {
        this.siteTemplateCreateForm.validate().then(async (validated) => {
            if (validated) {
                await dispatchCreateSiteTemplate(this.$store, this.siteTemplateCreateData);
                this.clearSiteTemplateForm();
                this.getSiteTemplateList();
            }
        });
    }
    public clearSiteTemplateForm() {
        this.siteTemplateCreateData = {} as ISiteTemplateCreate;
        this.siteTemplateCreateForm.reset();
    }
    public handleDeleteSiteTemplate(item: ISiteTemplatePaginationItemData) {
        this.siteTemplateActionData = Object.assign({}, item);
        this.siteTemplateDeleteDialog = true;
    }
    public handleUpdateSiteTemplate(item: ISiteTemplatePaginationItemData) {
        this.siteTemplateActionData = Object.assign({}, item);
        this.siteTemplateUpdateDialog = true;
    }
    public handleCancleUpdateSiteTemplate() {
        this.siteTemplateUpdateDialog = false;
        this.updateSiteTemplateZipFile = false;
    }
    public deleteSiteTemplate() {
        api.deleteSiteTemplate(this.siteTemplateActionData.id).then((res) => {
            this.siteTemplateDeleteDialog = false;
            this.getSiteTemplateList();
        });
    }
    public updateSiteTemplate() {
        const updateData = {
            id: this.siteTemplateActionData.id,
            name: this.siteTemplateActionData.name,
            remark: this.siteTemplateActionData.remark,
        };
        api.updateSiteTemplate(updateData).then((res) => {
            this.siteTemplateUpdateDialog = false;
            this.getSiteTemplateList();
        });
    }

    @Watch('ispTabIndex')
    public async onIspTabChanged(val: number) {
        await this.getIspProfileList();
    }
    @Watch('ispPaginationQueryParam', { immediate: true, deep: true })
    public async onIspPaginationChanged(val: number) {
        await this.getIspProfileList();
    }
    @Watch('c2PaginationQueryParam', { immediate: true, deep: true })
    public async onC2PaginationChanged(val: number) {
        await this.getC2ProfileList();
    }
    @Watch('siteTemplatePaginationQueryParam', { immediate: true, deep: true })
    public async onSiteTemplatePaginationChanged(val: number) {
        await this.getSiteTemplateList();
    }

    public async created() {
        await dispatchGetAvailableIsp(this.$store);
        await this.getSshKeyConfig();
    }
}
</script>
