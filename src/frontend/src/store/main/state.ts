import { IIspAvailable, IUserProfile, IIspPaginationItemData } from '@/interfaces';

export interface AppNotification {
    content: string;
    color?: string;
    timeout?: number;
    showProgress?: boolean;
}

export interface MainState {
    // user
    token: string;
    tokenType: string;
    isLoggedIn: boolean | null;
    logInError: boolean;
    userProfile: IUserProfile | null;

    // common
    dashboardMiniDrawer: boolean;
    dashboardShowDrawer: boolean;
    notifications: AppNotification[];

    // isp
    availableIsp: IIspAvailable | null;
    domainIsplist: IIspPaginationItemData[];
    vpsIspList: IIspPaginationItemData[];
}
