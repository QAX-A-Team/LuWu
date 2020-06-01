// Base & common interfaces
export interface ITableParam {
    pageNum: number;
    pageSize: number;
    total: number;
}

export interface IPaginationQuery {
    page?: number;
    perPage?: number;
    count?: boolean;
    queryAll?: boolean;
}

export interface IPaginationDataItem {
    id: number;
    createdOn: Date | string;
    updatedOn: Date | string;
    remark: Nullable<string>;
}

export interface IPaginationData {
    page: number;
    prevNum: Nullable<number>;
    hasPrev: boolean;
    hasNext: boolean;
    total: number;
    items: IPaginationDataItem[];
}

export interface IVuetifySelectItem {
    text: any;
    value: any;
}

export type IVForm = Vue & { validate: () => Promise<boolean>; reset: () => Promise<void> };


// User interfaces
export interface IUserProfile {
    email: string;
    isActive: boolean;
    isSuperuser: boolean;
    username: string;
    id: number;
}

export interface IUserProfileUpdate {
    email?: string;
    username?: string;
    password?: string;
    isActive?: boolean;
    isSuperuser?: boolean;
}

export interface IUserProfileCreate {
    email: string;
    username?: string;
    password?: string;
    isActive?: boolean;
    isSuperuser?: boolean;
}

// Config interfaces
export type IIspPaginationQuery = IPaginationQuery;

export interface IIspPaginationItemData extends IPaginationDataItem {
    type: number;
    provider: number;
    providerName: string;
    apiKey: Nullable<string>;
    isTest: boolean;
}
export interface IIspPaginationData extends IPaginationData {
    items: IIspPaginationItemData[];
}

export interface IIspProvider {
    code: number;
    name: string;
}

export interface IIspAvailable {
    domain?: IIspProvider[];
    vps?: IIspProvider[];
}

export interface IIspProfileCreate {
    provider: Nullable<number>;
    apiKey: Nullable<string>;
    remark?: Nullable<string>;
    isTest?: boolean;
}

export interface IC2ProfileCreate {
    name: string;
    profile?: File;
    remark?: Nullable<string>;
}
export type IC2PaginationQuery = IPaginationQuery;

export interface IC2PaginationItemData extends IPaginationDataItem {
    id: number;
    profileName: string;
}
export interface IC2PaginationData extends IPaginationData {
    items: IC2PaginationItemData[];
}

export interface ISelectionItem {
    text: string | number | object;
    value: string | number | object;
}

export interface IEnumItem {
    code: string;
    name: string;
}
