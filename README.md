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

在红队工作中，基础设施的部署和监控是非常重要的一部分，一个灵活快速的自动化部署工具能够使前期繁杂的工作变的高效简单。本项目按照模块化设计，架构的每部分使用独立的bash文件，可单独使用。当然，也可以使用web控制端联合使用，达到一键化部署，一键化销毁的目的。

## 功能述求
基于Cobaltstrike自动化的部署红队基础设施
1. 通过界面实施监控整个基础设施当前状态
2. 通过界面操作部署

## 设计思路
1. 通过调用vultr、DigitalOcean等VPS提供商的API接口，创建VPS和自动化执行脚本（bash）
2. 利用bash脚本安装基础设施组件

## 功能
1. 主界面展示目前启动的 vps、cs团队服务器、前置服务器，具体的参数（IP、cs端口，cs密码，cs的作用）
2. VPS管理，创建VPS、删除VPS、重置VPS、重启VPS等、以及展示相关的数据（VPS提供商、VPS（IP、ssh私钥、地区、规格等））
3. CS团队服务器管理（teamServer），Teamserver是一个软件，通过我们的bash脚本自动化安装在VPS上，安装了TeamServer的VPS我们就叫它cs团队服务器
    - 创建团队服务器（在创建好的VPS中选择一台VPS，执行我们的bash脚本）
    - 删除团队服务器（直接删除VPS）
4. 前置服务器，前置服务器是用来转发流量的，把请求流量转个给团队服务器（HTTP（s）、DNS等流量）,前置服务器也是一台VPS，在VPS上通过Bash脚本一键安装流量转发
    - 创建前置服务器（在创建好的VPS中选择一台VPS，前置服务器创建基于有cs团队服务器的前提，因为会用到cd团队服务的IP和其他配置文件）
    - 删除团队服务（删除VPS）

## 引用的开源项目
* https://github.com/mail-in-a-box/mailinabox
* https://github.com/bluscreenofjeff/Malleable-C2-Randomizer
* https://github.com/bluscreenofjeff/Red-Team-Infrastructure-Wiki
* <https://github.com/threatexpress/cs2modrewrite>
