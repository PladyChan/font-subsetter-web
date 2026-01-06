# TrimType 网站部署指南

本项目支持多种部署方式，您可以根据需求选择：

## 方案一：Vercel 部署（推荐，最简单快速）

Vercel 提供免费的 Python 应用托管，适合快速上线。

### 步骤：

1. **安装 Vercel CLI**（如果还没有）：
   ```bash
   npm i -g vercel
   ```

2. **登录 Vercel**：
   ```bash
   vercel login
   ```

3. **部署项目**：
   ```bash
   cd /Users/chensonghao/TeamFile/私人文件库/正在做/工具/字体
   vercel
   ```
   
   按照提示操作：
   - 选择项目设置（直接回车使用默认）
   - 确认部署配置

4. **生产环境部署**：
   ```bash
   vercel --prod
   ```

5. **访问网站**：
   部署完成后，Vercel 会提供一个 URL，例如：`https://trimtype-xxx.vercel.app`

### 优点：
- ✅ 免费（有使用限制）
- ✅ 自动 HTTPS
- ✅ 全球 CDN
- ✅ 自动部署（连接 GitLab 后）

---

## 方案二：阿里云 ECS 部署（适合国内访问）

适合需要国内服务器或已有阿里云 ECS 的情况。

### 前提条件：
- 阿里云 ECS 实例（Alibaba Cloud Linux）
- 域名（可选，用于 HTTPS）

### 步骤：

1. **登录服务器**：
   ```bash
   ssh root@您的服务器IP
   ```

2. **克隆代码**：
   ```bash
   git clone git@gitlab.alibaba-inc.com:songhao.csh/trimtype.git
   cd trimtype
   ```

3. **修改部署配置**：
   ```bash
   nano aliyun-deploy/deploy.sh
   ```
   将 `DOMAIN="typetrim.com"` 改为您的域名或服务器 IP

4. **运行部署脚本**：
   ```bash
   cd aliyun-deploy
   chmod +x deploy.sh
   ./deploy.sh
   ```

5. **配置安全组**：
   - 在阿里云控制台开放 80 和 443 端口

6. **访问网站**：
   - 使用域名或 IP 访问：`http://您的域名` 或 `http://服务器IP`

### 优点：
- ✅ 国内访问速度快
- ✅ 完全控制服务器
- ✅ 可自定义配置

---

## 方案三：其他云平台

### Railway
1. 访问 https://railway.app
2. 连接 GitLab 仓库
3. 自动部署

### Render
1. 访问 https://render.com
2. 连接 GitLab 仓库
3. 选择 Python Web Service
4. 自动部署

### 阿里云函数计算 FC
1. 在阿里云控制台创建函数
2. 上传代码或连接 GitLab
3. 配置触发器

---

## 推荐流程

**快速上线（推荐）**：
1. 使用 Vercel 快速部署（5分钟）
2. 测试功能是否正常
3. 如需国内访问，再部署到阿里云 ECS

**生产环境**：
1. 部署到阿里云 ECS
2. 配置域名和 SSL 证书
3. 设置监控和日志

---

## 部署后检查清单

- [ ] 网站可以正常访问
- [ ] 文件上传功能正常
- [ ] 字体处理功能正常
- [ ] HTTPS 已配置（生产环境）
- [ ] 域名已解析（如使用域名）
- [ ] 错误日志正常

---

## 常见问题

### Vercel 部署失败
- 检查 `vercel.json` 配置
- 确认 Python 版本兼容
- 查看 Vercel 日志

### 阿里云部署失败
- 检查安全组端口是否开放
- 查看 Nginx 日志：`tail -f /var/log/nginx/error.log`
- 查看应用日志：`tail -f /var/log/supervisor/typetrim.out.log`

### 字体处理失败
- 确认 fonttools 已正确安装
- 检查文件上传大小限制
- 查看应用错误日志

---

## 更新部署

### Vercel
```bash
git push gitlab main  # 推送到 GitLab
# Vercel 会自动检测并部署（如果已连接）
# 或手动运行：vercel --prod
```

### 阿里云 ECS
```bash
ssh root@服务器IP
cd /var/www/typetrim
git pull
cd aliyun-deploy
./deploy.sh
```

