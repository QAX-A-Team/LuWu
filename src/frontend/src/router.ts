import Vue from 'vue';
import Router from 'vue-router';

import RouterComponent from './components/RouterComponent.vue';

Vue.use(Router);

export default new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
        {
            path: '/',
            component: () => import(/* webpackChunkName: "start" */ './views/base/Start.vue'),
            children: [
                {
                    path: 'login',
                    // route level code-splitting
                    // this generates a separate chunk (about.[hash].js) for this route
                    // which is lazy-loaded when the route is visited.
                    component: () => import(/* webpackChunkName: "login" */ './views/Login.vue'),
                },
                {
                    path: 'main',
                    component: () => import(/* webpackChunkName: "main" */ './views/base/Main.vue'),
                    children: [
                        {
                            path: 'dashboard',
                            component: () => {
                                return import(/* webpackChunkName: "main-dashboard" */ `./views/base/Dashboard.vue`);
                            },
                        },
                    ],
                },
                {
                    path: 'domain',
                    component: () => import(/* webpackChunkName: "main" */ './views/base/Main.vue'),
                    children: [
                        {
                            path: '',
                            component: () => import(/* webpackChunkName: "domain-main" */ './views/Domain.vue'),
                        },
                    ],
                },
                {
                    path: 'vps',
                    component: () => import(/* webpackChunkName: "main" */ './views/base/Main.vue'),
                    children: [
                        {
                            path: '',
                            component: () => import(/* webpackChunkName: "vps-main" */ './views/Vps.vue'),
                        },
                    ],
                },
                {
                    path: 'module',
                    component: () => import(/* webpackChunkName: "main" */ './views/base/Main.vue'),
                    children: [
                        {
                            path: '',
                            component: () =>
                                import(/* webpackChunkName: "module-manager" */ './views/Module.vue'),
                        },
                    ],
                },
                {
                    path: 'config',
                    component: () => import(/* webpackChunkName: "main" */ './views/base/Main.vue'),
                    children: [
                        {
                            path: '',
                            component: () =>
                                import(/* webpackChunkName: "config-manager" */ './views/Config.vue'),
                        },
                    ],
                },
            ],
        },
        {
            path: '/*',
            redirect: '/',
        },
    ],
});
