import { IPaginationDataItem, IPaginationData } from './index';

export interface ISiteTemplateCreate {
    name: string;
    remark?: string;
    zipFile: File;
}

export interface ISiteTemplateUpdate {
    id: number;
    name: string;
    remark: Nullable<string>;
}

export interface ISiteTemplatePaginationItemData extends IPaginationDataItem {
    name: string;
    scriptTemplate: string;
}

export interface ISiteTemplatePaginationData extends IPaginationData {
    items: ISiteTemplatePaginationItemData[];
}

export interface ISshConfigData {
    privateKey: string;
    publicKey: string;
}
