<template>
    <v-card>
        <v-tabs background-color="transparent" grow v-model="tab">
            <v-tab :key="tabKey" v-for="(tabValue, tabKey) in tabChoices">{{ tabValue }}</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
            <v-tab-item key="manage">
                <v-card>
                    <v-data-table @update:page="updateDomainPaginationPageNum" @update:items-per-page="updateDomainPaginationPageSize" :headers="domainHeaders" :items="domainItems" :page.sync="domainTableParam.pageNum" :server-items-length="domainTableParam.total" :footer-props="tableFooterProps">
                        <template v-slot:top>
                            <v-toolbar flat color="white">
                                域名列表
                                <v-divider class="mx-4" inset vertical></v-divider>
                                <v-dialog v-model="domainCreateDialog" width="500">
                                    <template v-slot:activator="{ on }">
                                        <v-btn color="primary lighten-2" dark v-on="on">
                                            添加
                                        </v-btn>
                                    </template>
                                    <v-card>
                                        <v-card-title class="headline  lighten-2">
                                            增加域名
                                        </v-card-title>
                                        <v-card-text>
                                            <ValidationObserver ref="domainCreateForm">
                                                <v-form>
                                                    <ValidationProvider name="主域名" :rules="validateRules.domain" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" label="主域名" v-model="domainCreateData.domain" placeholder="填写主域名(例如:redteam.fun)"></v-text-field>
                                                    </ValidationProvider>
                                                    <ValidationProvider name="域名提供商" :rules="validateRules.domainIsp" v-slot="{ errors }">
                                                        <v-select v-model="domainCreateData.ispId" :items="availableDomainIspItems" label="域名提供商" :error-messages="errors"></v-select>
                                                    </ValidationProvider>
                                                    <ValidationProvider name="备注" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" v-model="domainCreateData.remark" label="备注"></v-text-field>
                                                    </ValidationProvider>
                                                </v-form>
                                            </ValidationObserver>
                                        </v-card-text>
                                        <v-divider></v-divider>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="info" text @click="createDomain">
                                                提交
                                            </v-btn>
                                            <v-btn color="blue-grey" text @click="domainCreateDialog=false">
                                                关闭
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                                <v-col>
                                    <v-btn color="primary lighten-2" :loading="domainReloadButtonLoading" @click="handleReloadDomain">
                                        刷新DNS数据
                                        <template v-slot:loader>
                                            <span>数据刷新中...</span>
                                        </template>
                                    </v-btn>
                                </v-col>
                                <v-spacer></v-spacer>
                            </v-toolbar>
                        </template>
                        <template v-slot:item.index="{ item }">
                            <span>{{ domainItems.indexOf(item)+1 }}</span>
                        </template>
                        <template v-slot:item.status="{ item }">
                            <span>{{ item.status? "已使用" : "可用" }}</span>
                        </template>
                        <template v-slot:item.dnsRecord="{ item }">
                            <v-btn class="ma-2" outlined color="indigo" @click="viewDomainDnsRecordItem(item)">
                                查看
                            </v-btn>
                        </template>
                        <template v-slot:item.actions="{ item }">
                            <v-btn class="mx-2" fab small color="warning" @click="deleteDomainItem(item)">
                                <v-icon dark>delete</v-icon>
                            </v-btn>
                        </template>
                    </v-data-table>
                    <v-dialog v-model="domainDnsRecordViewDialog" max-width="700">
                        <v-card>
                            <v-card-title class="headline">DNS记录</v-card-title>
                            <v-divider></v-divider>
                            <v-card-text>
                                <v-simple-table>
                                    <template v-slot:default>
                                        <thead>
                                            <tr>
                                                <th v-for="item in headerdomainDnsRecordHeaders" :key="item.value">{{item.text}}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="item of domainActionData.dnsRecords" :key="item.name">
                                                <td>{{ domainActionData.dnsRecords.indexOf(item) + 1 }}</td>
                                                <td>{{ item.host }}</td>
                                                <td>{{ item.type }}</td>
                                                <td>{{ item.value }}</td>
                                                <td>{{ item.ttl }}</td>
                                                <td>{{ item.distance }}</td>
                                            </tr>
                                        </tbody>
                                    </template>
                                </v-simple-table>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="green darken-1" text @click="domainDnsRecordViewDialog=false">
                                    关闭
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                    <v-dialog v-model="domainDeleteDialog" max-width="500">
                        <v-card>
                            <v-card-title class="headline">操作确认</v-card-title>
                            <v-card-text>
                                确定要删除 {{domainActionData.domain}} 吗？
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="warning darken-1" text @click="handleDeleteDomain">
                                    提交
                                </v-btn>
                                <v-btn color="green darken-1" text @click="domainDeleteDialog=false">
                                    取消
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-card>
            </v-tab-item>
            <v-tab-item key="purchase">
                <v-card>
                    <v-row>
                        <v-col>
                            <v-card>
                                <v-card-text>
                                    <v-container>
                                        <ValidationObserver ref="domainPurchaseForm">
                                            <v-row align="center">
                                                <v-col cols="4">
                                                    <ValidationProvider name="域名提供商" :rules="validateRules.domainIsp" v-slot="{ errors }">
                                                        <v-select :items="availableDomainIspItems" label="域名提供商" v-model="purchasableDomainSearchParam.ispId" :error-messages="errors"></v-select>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="4">
                                                    <ValidationProvider name="域名" v-slot="{ errors }">
                                                        <v-text-field v-model="purchasableDomainSearchParam.domain" :error-messages="errors" label="域名"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="4">
                                                    <v-btn bottom color="success" :loading="searchPurchasableDomainLoading" @click="searchPurchasableDomain">搜索</v-btn>
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
                                <v-data-table :headers="domainPurchaseHeaders" :items="domainPurchaseItems" hide-default-footer>
                                    <template v-slot:item.index="{ item }">
                                        <span>{{ domainPurchaseItems.indexOf(item)+1 }}</span>
                                    </template>
                                    <template v-slot:item.status="{ item }">
                                        <span>{{ item.purchasable? "可购买" : "不可购买" }}</span>
                                    </template>
                                    <template v-slot:item.action="{ item }">
                                        <v-btn class="ma-2" outlined color="indigo" :disabled="!item.purchasable" @click="handlePurchaseDomain(item)">
                                            购买
                                        </v-btn>
                                    </template>
                                </v-data-table>
                                <v-dialog persistent v-model="domainPurchaseDialog" max-width="500">
                                    <v-card>
                                        <v-card-title class="headline">确认购买</v-card-title>
                                        <v-card-text>
                                            <p>请仔细确认域名是否是需要购买的域名</p>
                                            <p>域名：{{ domainPurchaseData.domain }}</p>
                                            <p>价格($)： {{ domainPurchaseData.price > 0 ? domainPurchaseData.price : '未获取到有效价格' }}</p>
                                            <v-text-field label="输入域名提供商(防止误操作)" required v-model="domainPurchaseData.providerName" :hint="domainIspProviderName"></v-text-field>
                                        </v-card-text>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="blue darken-1" text :loading="domainPurchaseLoading" @click="purchaseDomain">购买</v-btn>
                                            <v-btn color="green darken-1" text @click="domainPurchaseDialog = false">取消</v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card>
            </v-tab-item>
            <v-tab-item key="verify">
                <v-card>
                    <v-card>
                        <v-card-text>
                            <v-container>
                                <ValidationObserver ref="domainVerifyForm">
                                    <v-row align="center">
                                        <v-col cols="2">
                                        </v-col>
                                        <v-col cols="8">
                                            <ValidationProvider name="域名" :rules="validateRules.domain" v-slot="{ errors }">
                                                <v-text-field :error-messages="errors" v-model="DomainVerifyParam.domain" label="域名"></v-text-field>
                                            </ValidationProvider>
                                        </v-col>
                                        <v-col cols="2">
                                            <v-btn bottom color="success" :loading="domainVerifyLoading" @click="handleVerifyDomain">验证</v-btn>
                                        </v-col>
                                    </v-row>
                                </ValidationObserver>
                            </v-container>
                        </v-card-text>
                    </v-card>
                    <v-card>
                        <v-simple-table>
                            <template v-slot:default>
                                <thead>
                                    <tr>
                                        <th v-for="item in domainVerifyHeaders" :key="item.value" :width="item.width">{{item.text}}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(value, name, index) in domainVerifyData" :key="name">
                                        <td>{{ index + 1 }}</td>
                                        <td>{{ name }}</td>
                                        <td>{{ value.toString() }}</td>
                                    </tr>
                                </tbody>
                            </template>
                        </v-simple-table>
                    </v-card>
                </v-card>
            </v-tab-item>
            <v-tab-item key="monitor">
                <v-card>
                    <v-row>
                        <v-col>
                            <v-card>
                                <v-card-title>添加监控任务</v-card-title>
                                <v-card-text>
                                    <v-container>
                                        <ValidationObserver ref="domainMonitorForm">
                                            <v-row align="center">
                                                <v-col cols="3">
                                                    <ValidationProvider name="域名" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                        <v-select v-model="domainMonitorData.domainId" :items="domainMonitorDomainSelections" label="域名" :error-messages="errors"></v-select>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="任务名" :rules="validateRules.domainMonitorTaskName" v-slot="{ errors }">
                                                        <v-text-field v-model="domainMonitorData.name" :error-messages="errors" label="任务名"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="间隔时间" :rules="validateRules.domainMonitorTaskInterval" v-slot="{ errors }">
                                                        <v-text-field v-model="domainMonitorData.interval" :error-messages="errors" label="间隔时间（秒）"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="备注" v-slot="{ errors }">
                                                        <v-text-field v-model="domainMonitorData.remark" :error-messages="errors" label="备注"></v-text-field>
                                                    </ValidationProvider>
                                                </v-col>
                                            </v-row>
                                        </ValidationObserver>
                                    </v-container>
                                </v-card-text>
                                <v-divider>
                                    <v-btn block></v-btn>
                                </v-divider>
                                <v-card-actions class="justify-center">
                                    <v-btn large color="info" @click="addDomainMonitorTask">添加任务</v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col>
                            <v-card>
                                <v-card-title>监控任务列表</v-card-title>
                                <v-data-table @update:page="updateDomainMonitorPaginationPageNum" @update:items-per-page="updateDomainMonitorPaginationPageSize" :headers="domainMonitorHeaders" :items="domainMonitorItems" :page.sync="domainMonitorTableParam.pageNum" :server-items-length="domainMonitorTableParam.total" :footer-props="tableFooterProps">
                                    <template v-slot:item.index="{ item }">
                                        <span>{{ domainMonitorItems.indexOf(item)+1 }}</span>
                                    </template>
                                    <template v-slot:item.active="{ item }">
                                        <v-switch v-model="item.active" disabled></v-switch>
                                    </template>
                                    <template v-slot:item.health="{ item }">
                                        <v-btn class="ma-2" color="primary" @click="viewDomainMonitorHealthRecord(item)">查看</v-btn>
                                    </template>
                                    <template v-slot:item.action="{ item }">
                                        <v-btn class="mx-2" fab small color="primary" @click="handleEditDomainMonitor(item)">
                                            <v-icon dark>edit</v-icon>
                                        </v-btn>
                                        <v-btn class="mx-2" fab small color="warning" @click="handleDeleteDomainMonitor(item)">
                                            <v-icon dark>delete</v-icon>
                                        </v-btn>
                                    </template>
                                </v-data-table>
                                <v-dialog v-model="domainMontiorHealthRecordViewDialog" max-width="1000">
                                    <v-card>
                                        <v-card-title class="headline">
                                            <p>域名分类和健康状况(是否被标记为恶意或可疑域名)</p>
                                            <v-spacer></v-spacer>
                                            <v-btn color="green darken-1" text @click="domainMontiorHealthRecordViewDialog=false">
                                                关闭
                                            </v-btn></v-card-title>
                                        <v-divider></v-divider>
                                        <v-card-text>
                                            <v-data-table :headers="domainMonitorHealthRecordHeaders" :items="domainMonitorActionDataHealthRecords" :footer-props="tableFooterProps">
                                                <template v-slot:item.index="{ item }">
                                                    <span>{{ domainMonitorActionDataHealthRecords.indexOf(item)+1 }}</span>
                                                </template>
                                            </v-data-table>
                                        </v-card-text>
                                    </v-card>
                                </v-dialog>
                                <v-dialog v-model="domainMonitorDeleteDialog" persistent max-width="650">
                                    <v-card>
                                        <v-card-title class="headline lighten-2">
                                            删除监控任务
                                        </v-card-title>
                                        <v-card-text>
                                            确定要删除： {{ domainMonitorActionData.domainName }} 的监控任务 {{ domainMonitorActionData.name }} 吗？
                                        </v-card-text>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="info" text @click="deleteDomainMonitor">
                                                删除
                                            </v-btn>
                                            <v-btn color="blue-grey" text @click="domainMonitorDeleteDialog=false">
                                                关闭
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                                <v-dialog v-model="domainMonitorUpdateDialog" max-width="700">
                                    <v-card>
                                        <v-card-title class="headline">修改任务</v-card-title>
                                        <v-card-text>
                                            <ValidationObserver ref="domainMonitorUpdateForm">
                                                <v-row align="center">
                                                    <v-col cols="6">
                                                        <ValidationProvider name="域名" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select disabled v-model="domainMonitorActionData.domainId" :items="domainMonitorDomainSelections" label="域名" :error-messages="errors"></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="6">
                                                        <ValidationProvider name="任务名" :rules="validateRules.domainMonitorTaskName" v-slot="{ errors }">
                                                            <v-text-field v-model="domainMonitorActionData.name" :error-messages="errors" label="任务名"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="6">
                                                        <ValidationProvider name="间隔时间" :rules="validateRules.domainMonitorTaskInterval" v-slot="{ errors }">
                                                            <v-text-field v-model="domainMonitorActionData.interval" :error-messages="errors" label="间隔时间（秒）"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="6">
                                                        <ValidationProvider name="备注" v-slot="{ errors }">
                                                            <v-text-field v-model="domainMonitorActionData.remark" :error-messages="errors" label="备注"></v-text-field>
                                                        </ValidationProvider>
                                                    </v-col>
                                                    <v-col cols="6">
                                                        <ValidationProvider name="任务状态" v-slot="{ errors }">
                                                            <v-switch v-model="domainMonitorActionData.active" :error-messages="errors" :label="domainMonitorActionData.active ? '启用': '停用'"></v-switch>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                            </ValidationObserver>
                                        </v-card-text>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="green darken-1" text @click="updateDomainMonitor">
                                                提交
                                            </v-btn>
                                            <v-btn color="darken-1" text @click="domainMonitorUpdateDialog=false">
                                                取消
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card>
            </v-tab-item>
            <v-tab-item key="grow">
                <v-card>
                    <v-row>
                        <v-col>
                            <v-card>
                                <v-card-title>域名一键培养</v-card-title>
                                <v-card-text>
                                    <v-container>
                                        <ValidationObserver ref="domainGrowForm">
                                            <v-row align="center">
                                                <v-col cols="3">
                                                    <ValidationProvider name="域名提供商" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                        <v-select :items="availableDomainIspItems" label="域名提供商" :error-messages="errors" v-model="domainGrowCreateData.ispId"></v-select>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="域名" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                        <v-select :items="domainMonitorDomainSelections" label="域名" :error-messages="errors" v-model="domainGrowCreateData.domainId"></v-select>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="模板网站" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                        <v-select :items="domainGrowTemplateSiteSelections" label="模板网站" :error-messages="errors" v-model="domainGrowCreateData.templateId"></v-select>
                                                    </ValidationProvider>
                                                </v-col>
                                                <v-col cols="3">
                                                    <ValidationProvider name="备注" v-slot="{ errors }">
                                                        <v-text-field :error-messages="errors" label="备注" v-model="domainGrowCreateData.remark"></v-text-field>
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
                                            <ValidationObserver ref="domainGrowVpsForm">
                                                <v-row align="center">
                                                    <v-col cols="3">
                                                    </v-col>
                                                    <v-col cols="6">
                                                        <ValidationProvider name="server" :rules="validateRules.requiredData" v-slot="{ errors }">
                                                            <v-select :items="domainGrowVpsSelections" label="server" v-model="domainGrowCreateData.vpsId" :error-messages="errors"></v-select>
                                                        </ValidationProvider>
                                                    </v-col>
                                                </v-row>
                                            </ValidationObserver>
                                        </v-container>
                                    </v-card-text>
                                </v-card>
                                <v-divider></v-divider>
                                <v-card-actions class="justify-center">
                                    <v-btn large color="info" :loading="domainGrowCreateLoading" @click="domainGrowCreate">开始培养</v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col>
                            <v-card>
                                <v-card-title>培养网站列表</v-card-title>
                                <v-data-table @update:page="updateDomainGrowPaginationPageNum" @update:items-per-page="updateDomainGrowPaginationPageSize" :headers="domainGrowHeaders" :items="domainGrowItems" :page.sync="domainGrowTableParam.pageNum" :server-items-length="domainGrowTableParam.total" :footer-props="tableFooterProps">
                                    <template v-slot:item.index="{ item }">
                                        <span>{{ domainGrowItems.indexOf(item)+1 }}</span>
                                    </template>
                                    <template v-slot:item.action="{ item }">
                                        <v-btn class="ma-2" color="warning" @click="handleDeleteDomainGrow(item)" :loading="domainGrowActionLoading">
                                            删除
                                        </v-btn>
                                    </template>
                                </v-data-table>
                                <v-dialog v-model="domainGrowDeleteDialog" persistent max-width="650">
                                    <v-card>
                                        <v-card-title class="headline lighten-2">
                                            删除培养网站
                                        </v-card-title>
                                        <v-card-text>
                                            <p>确定要删除吗，该操作会停止服务器的NGINX运行:</p>
                                            <p>域名: {{ domainGrowActionData.domainName}}</p>
                                            <p>网站模板: {{  domainGrowActionData.templateName }}</p>
                                        </v-card-text>
                                        <v-card-actions>
                                            <v-spacer></v-spacer>
                                            <v-btn color="info" text @click="deleteDomainGrow">
                                                删除
                                            </v-btn>
                                            <v-btn color="blue-grey" text @click="domainGrowDeleteDialog=false">
                                                关闭
                                            </v-btn>
                                        </v-card-actions>
                                    </v-card>
                                </v-dialog>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card>
            </v-tab-item>
        </v-tabs-items>
    </v-card>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import { DataTableHeader } from 'vuetify/types';

import { api } from '@/api';
import { ITableParam, IPaginationQuery, ISelectionItem, IVuetifySelectItem, IVForm } from '@/interfaces/index';
import {
    IDomainPaginationItemData,
    IDomainVerifyData,
    IDomainVerifyParam,
    IPurchasableDomainItem,
    IPurchaseDomainData,
    IPurchasableDomainSearchParam,
    IDomainMonitorData,
    IDomainMonitorPaginationItemData,
    IDomainGrowPaginationData,
    IDomainGrowPaginationItemData,
    IDomainGrowCreateData,
} from '@/interfaces/domain';
import { validateRules } from '@/plugins/vee-validate';
import {
    dispatchCreateDomain,
    dispatchReloadDomainDnsRecord,
    dispatchGetDomainIsp,
    dispatchGetDomainList,
    dispatchPurchaseDomain,
    dispatchSearhPurchasableDomain,
    dispatchCreateDomainMonitorTask,
    dispatchGetDomainMonitorList,
    dispatchUpdateDomainMonitor,
    dispatchDeleteDomainMonitor,
    dispatchGetDomainGrowList,
    dispatchCreateDomainGrow,
    dispatchDeleteDomainGrow,
} from '@/store/main/actions';
import { readDomainIspList } from '@/store/main/getters';
import { formReset, formValidate } from '@/utils';
import { validate } from 'vee-validate';


@Component
export default class DomainManage extends Vue {
    public pageName = '域名管理';
    public tab = null;
    public tabChoices = {
        manage: '管理',
        purchase: '购买',
        verify: '验证',
        monitor: '监控',
        grow: '培养',
    };

    public domainHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'DomainName', value: 'domain', sortable: false },
        { text: 'NameServer', value: 'nameServer', sortable: false },
        { text: 'DnsRecord', value: 'dnsRecord', sortable: false },
        { text: 'ISP', value: 'providerName', sortable: false },
        { text: '备注', value: 'remark', sortable: false },
        { text: '操作', value: 'actions', sortable: false },
    ];
    public headerdomainDnsRecordHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: 'Host', value: 'host', sortable: false },
        { text: 'Type', value: 'type', sortable: false },
        { text: 'Value', value: 'value', sortable: false },
        { text: 'TTL', value: 'ttl', sortable: false },
        { text: 'Distance', value: 'distance', sortable: false },
    ];
    public domainItems: IDomainPaginationItemData[] = [];
    public domainTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public tableFooterProps = {
        itemsPerPageOptions: [10, 20, 50, 100],
    };
    public domainCreateDialog = false;
    public domainReloadButtonLoading = false;
    public domainDnsRecordViewDialog = false;
    public domainDeleteDialog = false;
    public domainPurchaseDialog = false;
    public domainPurchaseLoading = false;
    public domainCreateData = {};
    public domainActionData = {} as IDomainPaginationItemData;
    public domainPurchaseHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: '域名', value: 'text', sortable: false },
        { text: '价格($)', value: 'price', sortable: false },
        { text: '状态', value: 'status', sortable: false },
        { text: '操作', value: 'action', sortable: false },
    ];
    public domainPurchaseItems: IPurchasableDomainItem[] = [];
    public purchasableDomainSearchParam = {} as IPurchasableDomainSearchParam;
    public searchPurchasableDomainLoading = false;
    public domainPurchaseData = {} as IPurchaseDomainData;
    public DomainVerifyParam = {} as IDomainVerifyParam;
    public domainVerifyLoading = false;
    public domainVerifyData = {} as IDomainVerifyData;
    public domainVerifyHeaders: DataTableHeader[] = [
        { text: '#', value: 'index', width: '30%' },
        { text: '项目', value: 'key', width: '40%' },
        { text: '值', value: 'value', width: '30%' },
    ];
    public domainMonitorTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public domainMonitorHeaders: DataTableHeader[] = [
        { text: '#', value: 'index' },
        { text: '任务名', value: 'name' },
        { text: '域名', value: 'domainName' },
        { text: '间隔时间', value: 'interval' },
        { text: '活动状态', value: 'active' },
        { text: '备注', value: 'remark' },
        { text: '健康状况', value: 'health' },
        { text: '操作', value: 'action' },
    ];
    public domainMonitorHealthRecordHeaders: DataTableHeader[] = [
        { text: '#', value: 'index', sortable: false },
        { text: '测试时间', value: 'createdOn', sortable: false },
        { text: '域名', value: 'host', sortable: false },
        { text: 'Talos', value: 'talos', sortable: false },
        { text: 'Xforce', value: 'xforce', sortable: false },
        { text: 'Opendns', value: 'opendns', sortable: false },
        { text: 'Bluecoat', value: 'bluecoat', sortable: false },
        { text: 'Mxtoolbox', value: 'mxtoolbox', sortable: false },
        { text: 'Trendmicro', value: 'trendmicro', sortable: false },
        { text: 'Fortiguard', value: 'fortiguard', sortable: false },
        { text: 'Health', value: 'health', sortable: false },
        { text: 'Explanation', value: 'explanation', sortable: false },
        { text: 'Health DNS', value: 'healthDns', sortable: false },
    ];
    public domainMonitorDomainSelections: ISelectionItem[] = [];
    public domainMonitorItems: IDomainMonitorPaginationItemData[] = [];
    public domainMonitorData = {} as IDomainMonitorData;
    public domainMonitorActionData = {} as IDomainMonitorPaginationItemData;
    public domainMontiorHealthRecordViewDialog = false;
    public domainMonitorUpdateDialog = false;
    public domainMonitorDeleteDialog = false;

    public domainGrowHeaders: DataTableHeader[] = [
        { text: '#', value: 'index', sortable: false },
        { text: '域名', value: 'domainName', sortable: false },
        { text: '域名提供商', value: 'providerName', sortable: false },
        { text: 'VPS', value: 'vpsHostname', sortable: false },
        { text: 'ip', value: 'vpsIp', sortable: false },
        { text: '网站模板', value: 'templateName', sortable: false },
        { text: '备注', value: 'remark', sortable: false },
        { text: '操作', value: 'action', sortable: false },
    ];
    public domainGrowItems: IDomainGrowPaginationItemData[] = [];
    public domainGrowTableParam: ITableParam = {
        pageNum: 1,
        pageSize: 10,
        total: 0,
    };
    public domainGrowVpsSelections: ISelectionItem[] = [];
    public domainGrowTemplateSiteSelections: ISelectionItem[] = [];
    public domainGrowCreateLoading = false;
    public domainGrowCreateData = {} as IDomainGrowCreateData;
    public domainGrowActionData = {} as IDomainGrowPaginationItemData;
    public domainGrowActionLoading = false;
    public domainGrowDeleteDialog = false;

    public get domainCreateForm(): IVForm {
        return this.$refs.domainCreateForm as IVForm;
    }
    public get availableDomainIspItems() {
        const rawDomainIspItems = readDomainIspList(this.$store);
        const availableIpsList: IVuetifySelectItem[] = [];

        for (const isp of rawDomainIspItems) {
            availableIpsList.push({
                text: `${isp.providerName}(${isp.apiKey})`,
                value: isp.id,
            });
        }
        return availableIpsList;
    }
    public get domainPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.domainTableParam.pageNum,
            perPage: this.domainTableParam.pageSize,
        };
        return queryData;
    }
    public get domainIspProviderName() {
        const rawDomainItems = readDomainIspList(this.$store);
        let providerName = '域名提供商名称';

        for (const isp of rawDomainItems) {
            if (this.domainPurchaseData.ispId === isp.id) {
                providerName = isp.providerName;
            }
        }
        return `请输入 ${providerName}`;
    }
    public get validateRules() {
        return validateRules;
    }
    public get domainMonitorForm() {
        return this.$refs.domainMonitorForm as IVForm;
    }
    public get domainMonitorPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.domainMonitorTableParam.pageNum,
            perPage: this.domainMonitorTableParam.pageSize,
        };
        return queryData;
    }
    public get domainGrowPaginationQueryParam() {
        const queryData: IPaginationQuery = {
            page: this.domainGrowTableParam.pageNum,
            perPage: this.domainGrowTableParam.pageSize,
        };
        return queryData;
    }
    public get domainMonitorActionDataHealthRecords() {
        return this.domainMonitorActionData.healthRecords;
    }

    @Watch('domainPaginationQueryParam', { immediate: true, deep: true })
    public async onDomainPaginationChanged() {
        await this.getDomainList();
    }
    @Watch('domainMonitorPaginationQueryParam', { immediate: true, deep: true })
    public async onDomainMonitorPaginationChanged() {
        await this.getDomainMonitorList();
    }
    @Watch('domainGrowPaginationQueryParam', { immediate: true, deep: true })
    public async onDomainGrowPaginationChanged() {
        await this.getDomainGrowList();
    }

    public updateDomainPaginationPageNum(pageNum: number) {
        this.domainTableParam.pageNum = pageNum;
    }
    public updateDomainPaginationPageSize(pageSize: number) {
        this.domainTableParam.pageSize = pageSize;
    }
    public viewDomainDnsRecordItem(domainItem) {
        this.domainActionData = Object.assign({}, domainItem);
        this.domainDnsRecordViewDialog = true;
    }
    public deleteDomainItem(domainItem) {
        this.domainActionData = Object.assign({}, domainItem);
        this.domainDeleteDialog = true;
    }
    public async getDomainList() {
        const domainListData = await dispatchGetDomainList(this.$store, this.domainPaginationQueryParam);
        this.domainTableParam.total = domainListData.total;
        this.domainItems = domainListData.items;
    }
    public async searchPurchasableDomain() {
        this.searchPurchasableDomainLoading = true;
        dispatchSearhPurchasableDomain(this.$store, this.purchasableDomainSearchParam).then((res) => {
            this.domainPurchaseItems = res;
        }).finally(() => {
            this.searchPurchasableDomainLoading = false;
        });
    }
    public async createDomain() {
        this.domainCreateForm.validate().then(async (validated) => {
            if (validated) {
                await dispatchCreateDomain(this.$store, this.domainCreateData);
                await this.getDomainList();
                this.domainCreateDialog = false;
            }
        });
    }

    public async handleReloadDomain() {
        this.domainReloadButtonLoading = true;
        dispatchReloadDomainDnsRecord(this.$store).then(() => {
            this.getDomainList();
        }).finally(() => {
            this.domainReloadButtonLoading = false;
        });
    }
    public async handleDeleteDomain() {
        api.deleteDomain(this.domainActionData.id).then(() => {
            this.domainDeleteDialog = false;
            this.getDomainList();
        });
    }
    public async handlePurchaseDomain(item: IPurchasableDomainItem) {
        this.domainPurchaseData = {
            price: item.price || -1,
            domain: item.text,
            ispId: this.purchasableDomainSearchParam.ispId,
            providerName: '',
        };
        this.domainPurchaseDialog = true;
    }
    public purchaseDomain(item: IPurchasableDomainItem) {
        this.domainPurchaseLoading = true;
        dispatchPurchaseDomain(this.$store, this.domainPurchaseData).then(() => {
            item.purchasable = false;
            this.domainPurchaseDialog = false;
        }).finally(() => {
            this.domainPurchaseLoading = false;
        });
    }

    public handleVerifyDomain() {
        this.domainVerifyLoading = true;
        api.verifyDomain(this.DomainVerifyParam).then((res) => {
            this.domainVerifyData = res;
        }).finally(() => {
            this.domainVerifyLoading = false;
        });
    }

    public updateDomainMonitorPaginationPageNum(pageNum: number) {
        this.domainMonitorTableParam.pageNum = pageNum;
    }
    public updateDomainMonitorPaginationPageSize(pageSize: number) {
        this.domainMonitorTableParam.pageSize = pageSize;
    }
    public async getDomainMonitorList() {
        const domainMonitorListData = await dispatchGetDomainMonitorList(
            this.$store, this.domainMonitorPaginationQueryParam,
        );
        this.domainMonitorTableParam.total = domainMonitorListData.total;
        this.domainMonitorItems = domainMonitorListData.items;
    }
    public async getDomainMonitorDomainSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const domainData = await api.getDomainList(queryParam);

        this.domainMonitorDomainSelections = domainData.items.map((item) => {
            return {
                text: item.domain,
                value: item.id,
            };
        });
    }
    public addDomainMonitorTask() {
        this.domainMonitorForm.validate().then(async (validated) => {
            if (validated) {
                await dispatchCreateDomainMonitorTask(this.$store, this.domainMonitorData);
                this.getDomainMonitorList();
            }
        });
    }
    public viewDomainMonitorHealthRecord(item: IDomainMonitorPaginationItemData) {
        this.domainMonitorActionData = item;
        this.domainMontiorHealthRecordViewDialog = true;
    }
    public handleEditDomainMonitor(item: IDomainMonitorPaginationItemData) {
        this.domainMonitorActionData = item;
        this.domainMonitorUpdateDialog = true;
    }
    public handleDeleteDomainMonitor(item: IDomainMonitorPaginationItemData) {
        this.domainMonitorActionData = item;
        this.domainMonitorDeleteDialog = true;
    }
    public updateDomainMonitor() {
        dispatchUpdateDomainMonitor(this.$store, this.domainMonitorActionData).then(() => {
            this.getDomainMonitorList();
        }).finally(() => {
            this.domainMonitorUpdateDialog = false;
        });
    }
    public async deleteDomainMonitor() {
        await dispatchDeleteDomainMonitor(this.$store, this.domainMonitorActionData.id);
        this.domainMonitorDeleteDialog = false;
        this.getDomainMonitorList();
    }
    public updateDomainGrowPaginationPageNum(pageNum: number) {
        this.domainGrowTableParam.pageNum = pageNum;
    }
    public updateDomainGrowPaginationPageSize(pageSize: number) {
        this.domainGrowTableParam.pageSize = pageSize;
    }
    public async getDomainGrowList() {
        const domainGrowListData = await dispatchGetDomainGrowList(
            this.$store, this.domainGrowPaginationQueryParam,
        );

        this.domainGrowTableParam.total = domainGrowListData.total;
        this.domainGrowItems = domainGrowListData.items;
    }
    public async getDomainGrowVpsSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const domainData = await api.getVpsList(queryParam);

        this.domainGrowVpsSelections = domainData.items.map((item) => {
            return {
                text: item.hostname,
                value: item.id,
            };
        });
    }
    public async getDomainTemplateSiteSelections() {
        const queryParam: IPaginationQuery = { queryAll: true };
        const templateSiteData = await api.getSiteTemplateList(queryParam);

        this.domainGrowTemplateSiteSelections = templateSiteData.items.map((item) => {
            return {
                text: item.name,
                value: item.id,
            };
        });
    }
    public prepareDomainGrowSelections() {
        this.getDomainGrowVpsSelections();
        this.getDomainTemplateSiteSelections();
    }
    public domainGrowCreate() {
        this.domainGrowCreateLoading = true;
        dispatchCreateDomainGrow(this.$store, this.domainGrowCreateData).then(() => {
            this.getDomainGrowList();
        }).finally(() => {
            this.domainGrowCreateLoading = false;
        });
    }
    public handleDeleteDomainGrow(item: IDomainGrowPaginationItemData) {
        this.domainGrowActionData = Object.assign({}, item);
        this.domainGrowDeleteDialog = true;
    }
    public async deleteDomainGrow() {
        await dispatchDeleteDomainGrow(this.$store, this.domainGrowActionData.id);
        this.domainGrowDeleteDialog = false;
        this.getDomainGrowList();
    }

    public async created() {
        await dispatchGetDomainIsp(this.$store);
        this.getDomainMonitorDomainSelections();
        this.prepareDomainGrowSelections();
    }
}
</script>
