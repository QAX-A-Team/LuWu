import { IPaginationDataItem, IPaginationData } from './index';


export interface ITeamServerCreate {
    port: number;
    password: string;
    c2ProfileId: number;
    vpsId: number;
    killDate: string;
    remark: Nullable<string>;
    csDownloadUrl: string;
    zipPassword: string;
}

export interface ITeamServerItemData extends IPaginationDataItem {
    id: number;
    ispProviderName: string;
    hostname: string;
}

export interface ITeamServerPaginationData extends IPaginationData {
    items: ITeamServerItemData[];
}


export interface IRedirectorCreate {
    remark: Nullable<string>;
}

export interface IRedirectorItemData extends IPaginationDataItem {
    id: number;
    ispProviderName: string;
    templateSiteName: string;
}

export interface IRedirectorPaginationData extends IPaginationData {
    items: IRedirectorItemData[];
}

export interface IRedirectorCreateData {
    beaconType: string;
    teamServerId: number;
    listenerPort: number;
    redirectDomain: string;
    vpsId: number;
    domainId: number;
    remark: Nullable<string>;
}
