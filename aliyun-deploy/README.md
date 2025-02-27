# TypeTrim 阿里云部署指南 (适用于 Alibaba Cloud Linux)

本文档提供了将 TypeTrim 应用部署到阿里云 ECS 的详细步骤。

## 前提条件

1. 一台运行 Alibaba Cloud Linux 的阿里云 ECS 实例
2. 一个已解析到该 ECS 实例的域名（可选）
3. 具有 root 或 sudo 权限的用户账号

## 部署步骤

### 1. 准备工作

登录到您的阿里云 ECS 实例：

```bash
ssh root@您的ECS实例IP
```

### 2. 安装 Git 并克隆代码库

```bash
yum update -y
yum install -y git
git clone https://github.com/PladyChan/font-subsetter-web.git
cd font-subsetter-web
```

### 3. 修改配置

编辑部署脚本中的域名配置：

```bash
nano aliyun-deploy/deploy.sh
```

将 `DOMAIN="typetrim.com"` 修改为您自己的域名或服务器IP地址。

### 4. 运行部署脚本

```bash
cd aliyun-deploy
chmod +x deploy.sh
./deploy.sh
```

脚本将自动完成以下工作：
- 安装必要的软件包
- 创建应用目录
- 复制应用文件
- 设置权限
- 创建虚拟环境并安装依赖
- 配置 Nginx
- 配置 Supervisor
- 启动服务
- 配置防火墙
- 配置 SSL 证书（如果使用域名）

### 5. 验证部署

部署完成后，您可以通过以下方式验证应用是否正常运行：

```bash
# 检查 Nginx 状态
systemctl status nginx

# 检查 Supervisor 状态
supervisorctl status typetrim

# 检查应用日志
tail -f /var/log/supervisor/typetrim.out.log
```

然后，在浏览器中访问您的域名或服务器IP来验证应用是否正常工作。

## 故障排除

如果遇到问题，请检查以下日志文件：

- Nginx 错误日志: `/var/log/nginx/error.log`
- Supervisor 日志: `/var/log/supervisor/typetrim.err.log`
- 应用日志: `/var/log/supervisor/typetrim.out.log`

### 常见问题

1. **端口未开放**：确保在阿里云安全组中开放了80和443端口
2. **服务未启动**：使用 `systemctl status nginx` 和 `systemctl status supervisord` 检查服务状态
3. **权限问题**：确保应用目录权限正确 `chown -R nginx:nginx /var/www/typetrim`

## 更新应用

要更新应用，请执行以下步骤：

```bash
cd /path/to/font-subsetter-web
git pull
cd aliyun-deploy
./deploy.sh
```

## 安全建议

1. 配置防火墙，只开放必要的端口（80、443）
2. 定期更新系统和软件包
3. 设置强密码并使用 SSH 密钥登录
4. 考虑使用阿里云 WAF 进行额外的安全防护