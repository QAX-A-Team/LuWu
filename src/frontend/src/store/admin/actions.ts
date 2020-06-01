import { api } from '@/api';
import { IUserProfileCreate, IUserProfileUpdate } from '@/interfaces';
import { getStoreAccessors } from 'typesafe-vuex';
import { ActionContext } from 'vuex';
import { dispatchCheckApiError } from '../main/actions';
import { commitAddNotification, commitRemoveNotification } from '../main/mutations';
import { State } from '../state';
import { commitSetUser, commitSetUsers } from './mutations';
import { AdminState } from './state';

type MainContext = ActionContext<AdminState, State>;

export const actions = {
    async actionGetUsers(context: MainContext) {
      try {
          const response = await api.getUsers(context.rootState.main.token);
          if (response) {
              commitSetUsers(context, response);
          }
      } catch (error) {
          await dispatchCheckApiError(context, error);
      }
  },
    async actionUpdateUser(
        context: MainContext,
        payload: { id: number; user: IUserProfileUpdate },
    ) {
      try {
          const loadingNotification = { content: 'saving', showProgress: true };
          commitAddNotification(context, loadingNotification);
        //   const response = (
        //         await Promise.all([
        //             api.updateUser(context.rootState.main.token, payload.id, payload.user),
        //             await new Promise((resolve, reject) => setTimeout(() => resolve(), 500)),
        //         ])
        //   )[0];
          const response = await api.updateUser(context.rootState.main.token, payload.id, payload.user);
          commitSetUser(context, response);
          commitRemoveNotification(context, loadingNotification);
          commitAddNotification(context, {
              content: 'User successfully updated',
              color: 'success',
          });
      } catch (error) {
          await dispatchCheckApiError(context, error);
      }
  },
    async actionCreateUser(context: MainContext, payload: IUserProfileCreate) {
      try {
          const loadingNotification = { content: 'saving', showProgress: true };
          commitAddNotification(context, loadingNotification);
        //   const response = (
        //         await Promise.all([
        //             api.createUser(context.rootState.main.token, payload),
        //             await new Promise((resolve, reject) => setTimeout(() => resolve(), 500)),
        //         ])
        //   )[0];
          const response = await api.createUser(context.rootState.main.token, payload);
          commitSetUser(context, response);
          commitRemoveNotification(context, loadingNotification);
          commitAddNotification(context, {
              content: 'User successfully created',
              color: 'success',
          });
      } catch (error) {
          await dispatchCheckApiError(context, error);
      }
  },
};

const { dispatch } = getStoreAccessors<AdminState, State>('');

export const dispatchCreateUser = dispatch(actions.actionCreateUser);
export const dispatchGetUsers = dispatch(actions.actionGetUsers);
export const dispatchUpdateUser = dispatch(actions.actionUpdateUser);
