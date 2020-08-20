## 安装、构建

### 配置目录

配置目录在`conf`目录下，以后端为例子：

- 线上后端配置在`conf/backend/env.docker`， 默认用户名: `${FIRST_SUPERUSER_USERNAME}`, 默认密码: `${FIRST_SUPERUSER_PASSWORD}`，比如现在`FIRST_SUPERUSER_USERNAME=luwu` 即用户名为luwu

### 前置依赖

- docker (https://docs.docker.com/engine/install/)
- docker-compose (https://docs.docker.com/compose/install)

### 构建

（在项目根目录下）

可参考下面命令

```bash
cd luwu
docker-compose -f dockerfiles/docker-compose.release.yml build
```

### 初始化数据

```bash
docker-compose -f dockerfiles/docker-compose.release.yml exec backend /bin/sh

(进入容器后)
alembic upgrade head && alembic revision --autogenerate && alembic upgrade head
python initial_data.py
```

### 启动

```bash
docker-compose -f dockerfiles/docker-compose.release.yml up -d
```

## 使用

### 登录

未更改配置文件的情况下

默认用户名： luwu
默认密码： C*+*rRLsTF57JqPE

### 生成luwu的ssh key

点击`配置管理 -> SSH KEY`
点击按钮生成 `SSH KEY`

### 添加ISP配置

点击 `配置管理 -> ISP -> 添加按钮`
填写配置后保存，点击`刷新VPS配置`按钮

#### ISP API 配置获取

- namesilo https://www.namesilo.com/account/api-manager
- vultr https://my.vultr.com/settings/#settingsapi
- digitalocean https://cloud.digitalocean.com/api_access
- 阿里云 https://ram.console.aliyun.com/manage/ak
- 腾讯云 https://console.cloud.tencent.com/cam/capi

