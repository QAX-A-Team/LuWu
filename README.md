# 陆吾        
```
888               888       888          
888               888   o   888          
888               888  d8b  888          
888      888  888 888 d888b 888 888  888 
888      888  888 888d88888b888 888  888 
888      888  888 88888P Y88888 888  888 
888      Y88b 888 8888P   Y8888 Y88b 888 
88888888  "Y88888 888P     Y888  "Y88888 
```
**陆吾**即**肩吾**，中国古代神话传说中的昆仑山神明，人面虎身虎爪而九尾。

在红队工作中，基础设施的部署和监控是非常重要的一部分，一个灵活快速的自动化部署工具能够是的前期繁杂的工作变的高效简单。本项目按照模块化设计，架构的每部分使用独立的bash文件，可单独使用。当然，也可以使用web控制端联合使用，达到一键化部署，一键化销毁的目的。

----
## 架构设计
### 架构图
![](https://ws3.sinaimg.cn/large/006tKfTcly1g0yukcashpj317e0sewjv.jpg)

![](https://ws1.sinaimg.cn/large/006tNc79ly1g24ktfz4kzj30zs0nwgqm.jpg)

### 技术选型

 * VPS
    - CS部署：Vultr
    - SMTP部署：DigitalOcean（Vultr封25所以选择DigitalOcean）
    - FileServer部署 QingCloud（当然你也可以使用Vultr、DigitalOcean等等）
    - 其他前置部署：Vultr

 * 开发语言
    - Bash
    - Python

 * 域名服务

    - namesilo

 * WEB控制端

     * Flask
----

## 组件
### CSInstall.sh 
cobaltstrike一键部署脚本，快捷自动化部署cs，红队基础架构部署组件之一。
 * Oracle Java 安装
 * 生成c2profile文件
 * 启动TeamServer
```
 仅支持ubuntu系统
 ubuntu 18.10（vultr）测试成功
```
### VPSDeploy.sh
一键部署DigitalOcean、Vultr服务器(共包含6台VPS；ubuntu 18.04 x86_64 1G 1CPU)
 * 增加ssh钥
 * 创建vps

### MailSetup.sh
一键安装SMTP服务，使用了经过修改的mail-in-a-box项目

### C2Redirectors.sh

一键部署HTTP(S)、DNS通道的前置服务器

----

## 使用
### 准备工作
 1. 注册Vultr、DigitalOcean、namesilo并获取API key。
 2. 在namesilo上手动注册好域名（例如：qianxinateam.com）
 3. 准备好CS文件压缩包（例如：cs3.13.zip）
### CSInstall.sh使用
等待更新

### VPSDeploy.sh使用

等待更新

### MailSetup.sh使用

等待更新

### C2Redirectors.sh使用

等待更新

## 引用的开源项目
 * https://github.com/mail-in-a-box/mailinabox
 * https://github.com/bluscreenofjeff/Malleable-C2-Randomizer
 * https://github.com/bluscreenofjeff/Red-Team-Infrastructure-Wiki
 * <https://github.com/threatexpress/cs2modrewrite>
