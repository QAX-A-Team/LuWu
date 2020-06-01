import { IPaginationData, IPaginationDataItem } from '@/interfaces/index';

export interface IVpsPaginationItemData extends IPaginationDataItem {
    ispId: number;
    ip: number | string;
    serverId: number;
    hostname: string;
    os: string;
    plan: string;
    region: string;
    used: boolean;
    teamServers?: [];
    redirectorC2s?: [];
    smtpServers?: [];
}
export interface IVpsPaginationData extends IPaginationData {
    items: IVpsPaginationItemData[];
}

export interface IVpsCreateData {
    hostname: string;
    ispId: number;
    regionCode: number | string;
    osCode: number | string;
    planCode: number | string;
    remark: string;
    sshKeys: number[];
}

export interface IVpsSpecQuery {
    ispId: number;
}

export interface IVpsSpecOs {
    name: string;
    osCode: string | number;
    regionCodes: Array<string | number>;
}

export interface IVpsSpecRegion {
    name: string;
    regionCode: string | number;
    features: string[];
    regionCodes: Array<string | number>;
}

export interface IVpsSpecPlan {
    name: string;
    planCode: string[] | number[];
    regionCodes: [];
    bandwidth: number;
    ram: number;
    vcpu: number;
    disk: number;
    priceMonthly: number;
    priceHourly: number;
    priceYearly: number;
}

export interface IVpsSpec {
    os: IVpsSpecOs[];
    region: IVpsSpecRegion[];
    plan: IVpsSpecPlan[];
}
