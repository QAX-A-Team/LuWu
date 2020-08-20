<template>
    <v-card>
        <v-tabs background-color="transparent" v-model="tab">
            <v-tab :key="tabKey" v-for="(tabValue, tabKey) in tabChoices">{{ tabValue }}</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
            <v-tab-item key="server">
                <v-card>
                    <v-data-table @update:page="updatePaginationPageNum" @update:items-per-page="updatePaginationPageSize" :headers="vpsHeaders" :items="vpsItems" :page.sync="vpsTableParam.pageNum" :server-items-length="vpsTableParam.total" :footer-props="tableFooterProps">
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                服务器列表
                                <v-divider class="mx-4" inset vertical></v-divider>
                                <v-dialog v-model="vpsCreateDialog" persistent max-width="680">
                                    <template v-slot:activator="{ on }">
                                        <v-btn color="primary lighten-2" dark v-on="on">
                                            添加
                                        </v-btn>
                                    </template>
                                    <v-card>
                                        <v-card-title class="headline lighten-2">
                                            创建VPS
                                        </v-card-title>
                                        <v-card-text>
                                            <ValidationObserver ref="vpsCreateForm">
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>提供商</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="提供商" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select dense :items="availableVpsIspItems" :error-messages="errors" v-model="vpsCreateData.ispId" outlined></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>主机名</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="主机名" :rules="validateRules.vpsHostname" v-slot="{ errors }">
                                                            <v-text-field dense :error-messages="errors" v-model="vpsCreateData.hostname"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>备注</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="备注" :rules="validateRules.remark" v-slot="{ errors }">
                                                            <v-text-field dense :error-messages="errors" v-model="vpsCreateData.remark"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>地区</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="地区选择" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select dense :items="availableVpsRegionItems" :error-messages="errors" v-model="vpsCreateData.regionCode" outlined>
                                                            </v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>配置</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="配置选择" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select dense :items="availableVpsPlanItems" :error-messages="errors" v-model="vpsCreateData.planCode" outlined></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>系统</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="系统选择" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select dense :items="availableVpsOsItems" :error-messages="errors" v-model="vpsCreateData.osCode" outlined></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                                <v-row>
                                                    <v-col cols="2">
                                                        <v-subheader>SSH KEY</v-subheader>
                                                    </v-col>
                                                    <v-col cols="8">
                                                        <ValidationProvider name="SSH KEY" v-slot="{ errors }">
                                                            <v-select multiple dense :items="vpsSshKeyItems" :error-messages="errors" v-model="vpsCreateData.sshKeys" outlined></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                            </ValidationObserver>
                                        </v-card-text>
                                        <v-divider></v-divider>

                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="info" text @click="createVps">
                                                提交
                                            </v-btn>
                                            <v-btn color="blue-grey" text @click="vpsCreateDialog=false">
                                                关闭
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                                <v-spacer></v-spacer>
                            </v-toolbar>
                        </template>
                        <template v-slot:item.index="{ item }">
                            <span>{{ vpsItems.indexOf(item)+1 }}</span>
                        </template>
                        <template v-slot:item.status="{ item }">
                            <v-chip v-if="item.status === 1" class="ma-2" color="cyan" text-color="white">
                                创建中
                            </v-chip>
                            <v-chip v-else-if="item.status === 2" class="ma-2" color="green" text-color="white">
                                可用
                            </v-chip>
                            <v-chip v-else-if="item.status === 3" class="ma-2" color="blue" text-color="white">
                                已使用
                            </v-chip>
                            <v-chip v-else-if="item.status === 4" class="ma-2" color="red" text-color="white" @click="showErrorMsg(item.statusMsg)">
                                <span>出错</span>
                            </v-chip>
                            <v-chip v-else class="ma-2" color="yellow" text-color="white">
                                未知状态
                            </v-chip>
                        </template>
                        <template v-slot:item.actions="{ item }">
                            <v-btn class="ma-2" color="warning" @click="handleDeleteVps(item)" :disabled="vpsActionLoading" :loading="vpsActionLoading">
                                删除
                            </v-btn>
                            <v-btn class="ma-2" color="info" @click="handleRebootVps(item)" :disabled="vpsActionLoading" :loading="vpsActionLoading">
                                重启
                            </v-btn>
                            <v-btn class="ma-2" color="primary" @click="handleReinstallVps(item)" :disabled="vpsActionLoading" :loading="vpsActionLoading">
                                重装
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="vpsErrorDialog" max-width="450">
                        <v-card>
                            <v-card-title class="headline">错误详情</v-card-title>
                            <v-card-text>
                                <v-textarea outlined auto-grow dense readonly :value="vpsErrorMsg"></v-textarea>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="green darken-1" text @click="vpsErrorDialog = false">
                                    确定
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="vpsRebootDialog" persistent max-width="650">
                        <v-card>
                            <v-card-title class="headline lighten-2">
                                重启服务器
                            </v-card-title>
                            <v-card-text>
                                <p>确定要重启服务器:</p>
                                <p>主机名: {{vpsActionData.hostname}}</p>
                                <p v-if="vpsActionData.ip">IP： {{ vpsActionData.ip }}</p>
                                <p>系统： {{ vpsActionData.os }}</p>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="info" text :loading="vpsActionLoading" @click="rebootVps">
                                    重启
                                </v-btn>
                                <v-btn color="blue-grey" text @click="vpsRebootDialog=false">
                                    关闭
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="vpsReinstallDialog" persistent max-width="650">
                        <v-card>
                            <v-card-title class="headline lighten-2">
                                重装服务器
                            </v-card-title>
                            <v-card-text>
                                <p>确定要重装服务器:</p>
                                <p>主机名: {{vpsActionData.hostname}}</p>
                                <p v-if="vpsActionData.ip">IP： {{ vpsActionData.ip }}</p>
                                <p>系统： {{ vpsActionData.os }}</p>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="info" text :loading="vpsActionLoading" @click="reintallVps">
                                    重装
                                </v-btn>
                                <v-btn color="blue-grey" text @click="vpsReinstallDialog=false">
                                    关闭
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="vpsDeleteDialog" persistent max-width="650">
                        <v-card>
                            <v-card-title class="headline lighten-2">
                                删除服务器
                            </v-card-title>
                            <v-card-text>
                                <p>确定要删除服务器:</p>
                                <p>主机名: {{vpsActionData.hostname}}</p>
                                <p v-if="vpsActionData.ip">IP： {{ vpsActionData.ip }}</p>
                                <p>系统： {{ vpsActionData.os }}</p>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="info" text :loading="vpsActionLoading" @click="deleteVps">
                                    删除
                                </v-btn>
                                <v-btn color="blue-grey" text @click="vpsDeleteDialog=false">
                                    关闭
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
import { DataTableHeader } from 'vuetify/types';

import { api } from '@/api';
import { ITableParam, IPaginationQuery, IVForm, IVuetifySelectItem } from '@/interfaces/index';
import { IVpsCreateData, IVpsPaginationItemData, IVpsSpec } from '@/interfaces/vps';
import { validateRules } from '@/plugins/vee-validate';
import {
    dispatchCreateVps,
    dispatchDestroyVps,
    dispatchGetIspSshKeyList,
    dispatchGetVpsList,
    dispatchGetVpsIsp,
    dispatchGetVpsSpecs,
    dispatchRebootVps,
    dispatchReinstallVps,
} from '@/store/main/actions';
import { readVpsIspList } from '@/store/main/getters';
import { formReset, formValidate } from '@/utils';
import { validate } from 'vee-validate';


@Component
export default class DomainManage extends Vue {
    public pageName = 'VPS管理';
    public tab = null;
    public tabChoices = {
        server: '服务器',
    };
    public vpsHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: '状态', value: 'status', sortable: false },
        { text: 'IP', value: 'ip', sortable: false },
        { text: 'Hostname', value: 'hostname', sortable: false },
        { text: 'ISP', value: 'ispProviderName', sortable: false },
        { text: 'OS', value: 'os', sortable: false },
        { text: 'Region', value: 'region', sortable: false },
        { text: 'Plan', value: 'plan', sortable: false },
        { text: 'Remark', value: 'remark', sortable: false },
        { text: '操作', value: 'actions', sortable: false },
    ];
    public vpsErrorMsg: Nullable<string> = null;
    public vpsErrorDialog = false;
    public vpsItems: any[] = [];
    public vpsTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public tableFooterProps = {
        itemsPerPageOptions: [10, 20, 50, 100],
    };
    public vpsCreateDialog = false;
    public vpsCreateLoading = false;
    public vpsDeleteDialog = false;
    public vpsRebootDialog = false;
    public vpsReinstallDialog = false;
    public vpsActionData = {} as IVpsPaginationItemData;
    public vpsActionLoading = false;
    public vpsCreateData = {} as IVpsCreateData;
    public vpsRawSpecData = {} as IVpsSpec;
    public vpsSshKeyItems: IVuetifySelectItem[] = [];
    public get validateRules() {
        return validateRules;
    }
    public get vpsPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.vpsTableParam.pageNum,
            perPage: this.vpsTableParam.pageSize,
        };
        return queryData;
    }
    public get availableVpsIspItems() {
        const rawIspItems = readVpsIspList(this.$store);
        const availableIpsList: IVuetifySelectItem[] = [];

        for (const isp of rawIspItems) {
            availableIpsList.push({
                text: `${isp.providerName}(${isp.apiKey})`,
                value: isp.id,
            });
        }
        return availableIpsList;
    }
    public get vpsCreateForm(): IVForm {
        return this.$refs.vpsCreateForm as IVForm;
    }
    public get availableVpsRegionItems() {
        const regionData = this.vpsRawSpecData.region;
        return regionData.map((region) => {
            return {
                text: region.name,
                value: region.regionCode,
                features: region.features,
            };
        });
    }
    public get availableVpsOsItems() {
        const regionData = this.vpsRawSpecData.region;
        const osData = this.vpsRawSpecData.os;

        const availableOs = osData.filter((os) => {
            let regionAvailable = false;
            let planAvailable = false;
            if (os.regionCodes.length === 0) {
                regionAvailable = true;
            } else {
                regionAvailable = os.regionCodes.includes(this.vpsCreateData.regionCode);
            }

            if (os.planCodes.length > 0 && this.vpsCreateData.planCode) {
                planAvailable = os.planCodes.includes(this.vpsCreateData.planCode);
            } else {
                planAvailable = true;
            }

            return regionAvailable && planAvailable;
        }).map((os) => {
            return {
                text: os.name,
                value: os.osCode,
            };
        });
        return availableOs;
    }
    public get availableVpsPlanItems() {
        const regionData = this.vpsRawSpecData.region;
        const planData = this.vpsRawSpecData.plan;

        const availablePlan = planData.filter((plan) => {
            const planAvailableInRegion = plan.regionCodes.some(
                (regionCode: string) => {
                    let regionCodeCheck = false;
                    if (
                        this.vpsCreateData.regionCode &&
                        regionCode.toString() === this.vpsCreateData.regionCode.toString()
                    ) {
                        regionCodeCheck = true;
                    }
                    return regionCodeCheck;
                },
            );
            return plan.regionCodes.length === 0 ? 1 : planAvailableInRegion;
        }).filter((plan) => {
            let regionCodeCheck: boolean;

            if (this.vpsCreateData.regionCode && regionData) {
                const planAvailableInRegion = regionData.filter((region) => {
                    if (region.planCodes.length > 0) {
                        return region.planCodes.some(
                            (planCode) => {
                                return planCode.toString() === plan.planCode.toString();
                            });
                    } else {
                        return true;
                    }
                });
                regionCodeCheck = planAvailableInRegion.length > 0;
            } else {
                regionCodeCheck = true;
            }

            return regionCodeCheck;

        }).map((plan) => {
            return {
                text: plan.name,
                value: plan.planCode,
            };
        });
        return availablePlan;
    }

    @Watch('vpsCreateData.ispId', { immediate: true })
    public async onVpsIspChanged(ispId: number) {
        const vpsSpecs = await dispatchGetVpsSpecs(this.$store, { ispId });

        this.vpsRawSpecData = vpsSpecs;
        this.getVpsSshKeyList(ispId);
    }

    @Watch('vpsPaginationQueryParam', { immediate: true, deep: true })
    public async onVpsPaginationChanged() {
        await this.getVpsList();
    }

    public updatePaginationPageNum(pageNum: number) {
        this.vpsTableParam.pageNum = pageNum;
    }
    public updatePaginationPageSize(pageSize: number) {
        this.vpsTableParam.pageSize = pageSize;
    }
    public handleDeleteVps(item: IVpsPaginationItemData) {
        this.vpsActionData = item;
        this.vpsDeleteDialog = true;
    }
    public handleRebootVps(item: IVpsPaginationItemData) {
        this.vpsActionData = item;
        this.vpsRebootDialog = true;
    }
    public handleReinstallVps(item: IVpsPaginationItemData) {
        this.vpsActionData = item;
        this.vpsReinstallDialog = true;
    }
    public async reintallVps() {
        this.vpsActionLoading = true;
        dispatchReinstallVps(this.$store, this.vpsActionData.id).then(() => {
            this.vpsReinstallDialog = false;
            this.getVpsList();
        }).finally(() => {
            this.vpsActionLoading = false;
        });
    }
    public async rebootVps() {
        this.vpsActionLoading = true;
        dispatchRebootVps(this.$store, this.vpsActionData.id).then(() => {
            this.vpsRebootDialog = false;
            this.getVpsList();
        }).finally(() => {
            this.vpsActionLoading = false;
        });
    }
    public async deleteVps() {
        this.vpsActionLoading = true;

        dispatchDestroyVps(this.$store, this.vpsActionData.id).then(() => {
            this.vpsDeleteDialog = false;
            this.getVpsList();
        }).finally(() => {
            this.vpsActionLoading = false;
        });
    }

    public async getVpsList() {
        const vpsListData = await dispatchGetVpsList(this.$store, this.vpsPaginationQueryParam);
        this.vpsItems = vpsListData.items;
        this.vpsTableParam.pageNum = vpsListData.page;
        this.vpsTableParam.total = vpsListData.total;
    }
    public async showErrorMsg(msg: string) {
        this.vpsErrorMsg = msg;
        this.vpsErrorDialog = true;
    }
    public async getVpsSshKeyList(ispId: number) {
        if (ispId) {
            const vpsSshKeyData = await dispatchGetIspSshKeyList(this.$store, ispId);
            this.vpsSshKeyItems = vpsSshKeyData.map((sshKey) => {
                return {
                    text: sshKey.name,
                    value: sshKey.sshKeyId || sshKey.name,
                };
            });
        }
    }

    public async createVps() {
        this.vpsCreateForm.validate().then(async (validated) => {
            if (validated) {
                this.vpsCreateLoading = true;
                await dispatchCreateVps(this.$store, this.vpsCreateData);
                await this.getVpsList();
                this.vpsCreateLoading = false;
                this.vpsCreateDialog = false;
            }
        });
    }
    public async created() {
        await dispatchGetVpsIsp(this.$store);
    }
}
</script>
