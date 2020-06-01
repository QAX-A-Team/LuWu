import { IPaginationDataItem, IPaginationData } from '@/interfaces/index';


export interface IPurchasableDomainSearchParam {
    ispId: number;
    domain: string;
}

export interface IPurchasableDomainItem {
    text: string;
    price?: number;
    purchasable: boolean;
}

export interface IPurchaseDomainData {
    domain: string;
    price: number;
    ispId: number;
    providerName: string;
}

export interface IDomainPaginationItemData extends IPaginationDataItem {
    id: number;
    domain: string;
    providerName: string;
    nameServer: string;
    dnsRecords: string[];
    status: boolean;
}

export interface IDomainPaginationData extends IPaginationData {
    items: IDomainPaginationItemData[];
}

export interface IDomainVerifyParam {
    vtToken?: string;
    domain: string;
}

export interface IDomainVerifyData {
    all: string;
    health: string;
    burnedExplanation: string;
    healthDns: string;
    talos: string;
    xforce: string;
    opendns: string;
    bluecoat: string;
    mxtoolbox: string;
    trendmicro: string;
    fortiguard: string;
}

export interface IDomainMonitorData {
    domainId: number;
    name: string;
    interval: number;
    remark?: string;
}

export interface IDomainMonitorPaginationItemData extends IPaginationDataItem {
    id: number;
    domainId: number;
    name: string;
    interval: number;
    active: boolean;
    healthRecords: [];
}

export interface IDomainMonitorPaginationData extends IPaginationData {
    items: IDomainMonitorPaginationItemData[];
}


export interface IDomainGrowCreateData {
    ispId: number;
    vpsId: number;
    domainId: number;
    siteTemplateId: number;
    remark: Nullable<string>;
}

export interface IDomainGrowPaginationItemData extends IPaginationDataItem, IDomainGrowCreateData {
    id: number;
    ispProviderName: string;
    siteTemplateName: string;
    healthRecords: [];
}

export interface IDomainGrowPaginationData extends IPaginationData {
    items: IDomainGrowPaginationItemData[];
}
