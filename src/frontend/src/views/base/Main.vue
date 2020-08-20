<template>
    <div>
        <v-navigation-drawer permanent clipped app>
            <v-list dense>
                <v-subheader>操作台</v-subheader>
                <template v-for="item in menuItems">
                    <v-list-group v-if="item.children" :key="item.text" v-model="item.model" :prepend-icon="item.model ? item.icon : item['icon-alt']" append-icon="">
                        <template v-slot:activator>
                            <v-list-item>
                                <v-list-item-content>
                                    <v-list-item-title>
                                        {{ item.text }}
                                    </v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                        </template>
                        <v-list-item v-for="(child, i) in item.children" :key="i">
                            <v-list-item-action v-if="child.icon">
                                <v-icon>{{ child.icon }}</v-icon>
                            </v-list-item-action>
                            <v-list-item-content>
                                <v-list-item-title>
                                    {{ child.text }}
                                </v-list-item-title>
                            </v-list-item-content>
                        </v-list-item>
                    </v-list-group>
                    <v-list-item v-else :key="item.text" :to="item.route">
                        <v-list-item-action>
                            <v-icon>{{ item.icon }}</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>
                                {{ item.text }}
                            </v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                </template>
            </v-list>
        </v-navigation-drawer>
        <v-app-bar clipped-left app dark color="primary">
            <v-toolbar-title v-text="appName"></v-toolbar-title>
            <v-spacer></v-spacer>
            <v-menu auto> 
                <template v-slot:activator="{ on }">
                    <v-btn depressed large text v-on="on">
                        <v-icon left>person</v-icon>
                        {{ username }}
                    </v-btn>
                </template>
                <v-list>
                    <v-list-item @click="logout">
                        <v-icon>exit_to_app</v-icon>
                        注销
                    </v-list-item>
                </v-list>
            </v-menu>
        </v-app-bar>
        <v-main>
            <router-view></router-view>
        </v-main>
        <v-footer class="pa-3" fixed app>
            <v-spacer></v-spacer>
            <span>2020 &copy; {{teamName}}</span>
        </v-footer>
    </div>
</template>

<script lang="ts">
import { appName, teamName } from '@/env';
import { dispatchUserLogOut } from '@/store/main/actions';
import { readUserProfile, readHasAdminAccess } from '@/store/main/getters';
import { commitSetDashboardMiniDrawer, commitSetDashboardShowDrawer } from '@/store/main/mutations';
import { Component, Vue } from 'vue-property-decorator';

const routeGuardMain = async (to, from, next) => {
    if (to.path === '/main') {
        next('/main/dashboard');
    } else {
        next();
    }
};

@Component
export default class Main extends Vue {
    public appName = appName;
    public teamName = teamName;
    public menuItems = [
        { icon: 'web', text: '域名管理', route: '/domain' },
        { icon: 'computer', text: 'VPS管理', route: '/vps' },
        { icon: 'device_hub', text: '组件管理', route: '/module' },
        { icon: 'build', text: '配置管理', route: '/config' },
    ];

    public beforeRouteEnter(to, from, next) {
        routeGuardMain(to, from, next);
    }

    public beforeRouteUpdate(to, from, next) {
        routeGuardMain(to, from, next);
    }

    public get hasAdminAccess() {
        return readHasAdminAccess(this.$store);
    }
    public get username() {
        const userProfile = readUserProfile(this.$store);
        return userProfile ? userProfile.username : null;
    }
    public async logout() {
        await dispatchUserLogOut(this.$store);
    }
}
</script>
<style scoped>
</style>