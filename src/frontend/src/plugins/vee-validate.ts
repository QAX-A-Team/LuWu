import { ValidationObserver, ValidationProvider } from 'vee-validate';
import { extend, localize } from 'vee-validate';

import zh from 'vee-validate/dist/locale/zh_CN.json';
import * as rules from 'vee-validate/dist/rules';

import Vue from 'vue';

localize('zh_CN', zh);

Vue.component('ValidationProvider', ValidationProvider);
Vue.component('ValidationObserver', ValidationObserver);

for (const [rule, validation] of Object.entries(rules)) {
    extend(rule, {
      ...validation,
  });
}

export const validateRules = {
    ispApiKey: 'required',
    ispType: 'required',
    c2ProfileName: 'required|alpha_dash',
    c2ProfileFile: 'required|ext:profile',
    domain: { required: true, regex: /^[A-Za-z0-9][A-Za-z0-9_.]*$/ },
    domainIsp: 'required',
    domainMonitorTaskName: { required: true, regex: /^[0-9A-Z_\-\.]*$/i },
    domainMonitorTaskInterval: 'required|integer',
    vpsHostname: { required: true, regex: /^[0-9A-Z_\-\.]*$/i },
    requiredData: 'required',
    remark: 'max: 50',
    url: 'required',
    port: 'required|integer',
    zipFile: 'required|ext:zip',
};
