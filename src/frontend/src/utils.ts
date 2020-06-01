import { ValidationObserver } from 'vee-validate';

export const getLocalToken = () => localStorage.getItem('token');

export const saveLocalToken = (token: string) => localStorage.setItem('token', token);

export const removeLocalToken = () => localStorage.removeItem('token');

export const formValidate = (vm: Vue, formRef: string) => {
    (vm.$refs[formRef] as InstanceType<typeof ValidationObserver>).validate();
};

export const formReset = (vm: Vue, formRef: string) => {
    (vm.$refs[formRef] as InstanceType<typeof ValidationObserver>).reset();
};
