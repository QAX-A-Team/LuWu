<template>
    <v-content>
        <v-container fluid fill-height class="loginOverlay">
            <v-layout align-center justify-center>
                <v-flex xs12 sm8 md4>
                    <v-card class="elevation-12">
                        <v-toolbar dark color="primary">
                            <v-toolbar-title>{{appName}}</v-toolbar-title>
                            <v-spacer></v-spacer>
                        </v-toolbar>
                        <v-card-text>
                            <v-form @keyup.enter="submit">
                                <v-text-field @keyup.enter="submit" v-model="username" prepend-icon="person" name="login" label="用户名" type="text"></v-text-field>
                                <v-text-field @keyup.enter="submit" v-model="password" prepend-icon="lock" name="password" label="密码" id="password" type="password"></v-text-field>
                            </v-form>
                            <div v-if="loginError">
                                <v-alert :value="loginError" transition="fade-transition" type="error">
                                    Incorrect user
                                </v-alert>
                            </div>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn @click.prevent="submit">登录</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-flex>
            </v-layout>
        </v-container>
    </v-content>
</template>

<script lang="ts">
import { api } from '@/api';
import { appName } from '@/env';
import { dispatchLogIn } from '@/store/main/actions';
import { readLoginError } from '@/store/main/getters';
import { Component, Vue } from 'vue-property-decorator';

@Component
export default class Login extends Vue {
    public username: string = '';
    public password: string = '';
    public appName = appName;

    public get loginError() {
        return readLoginError(this.$store);
    }

    public submit() {
        dispatchLogIn(this.$store, { username: this.username, password: this.password });
    }
}
</script>

<style>
.loginOverlay {
    background-image: url("https://images.unsplash.com/photo-1488866022504-f2584929ca5f?dpr=1&auto=compress,format&fit=crop&w=1650&h=&q=80&cs=tinysrgb&crop=");
    background-repeat:no-repeat;
    -webkit-background-size: cover;
    -moz-background-size: cover;
    -o-background-size: cover;
    background-size: cover;
    background-size: 100% 100%;
    height: 100%;
    position: fixed;
    width: 100%;
    overflow: hidden;
}
</style>
