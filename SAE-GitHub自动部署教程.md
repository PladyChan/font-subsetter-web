# SAE + GitHub 自动部署教程

实现 GitHub 推送代码 → 自动部署到 SAE 的完整流程。

---

## 🎯 实现效果

**就像 Vercel 一样：**
1. 本地修改代码
2. `git push origin main`
3. GitHub Actions 自动触发
4. 自动构建 Docker 镜像
5. 自动推送到阿里云 ACR
6. 自动部署到 SAE
7. **完成！**

---

## 📋 准备工作

### 1. 阿里云容器镜像服务（ACR）

1. **登录阿里云控制台**
2. **开通容器镜像服务 ACR**
   - 搜索"容器镜像服务"
   - 开通服务（免费）

3. **创建镜像仓库**
   - 进入 ACR 控制台
   - 创建命名空间（如：`trimtype`）
   - 创建镜像仓库（如：`trimtype`）
   - 记录仓库地址

### 2. 获取阿里云访问密钥

1. **进入访问控制 RAM**
   - 在阿里云控制台搜索"访问控制"
   - 点击"用户" → "创建用户"
   - 创建用于 CI/CD 的用户

2. **创建 AccessKey**
   - 在用户详情页，创建 AccessKey
   - **保存 AccessKey ID 和 Secret**（只显示一次！）

3. **授权权限**
   - 给用户添加以下权限：
     - `AliyunSAEFullAccess`（SAE 完全访问）
     - `AliyunContainerRegistryFullAccess`（ACR 完全访问）

### 3. 配置 GitHub Secrets

1. **进入 GitHub 仓库**
   - 打开你的仓库：`https://github.com/PladyChan/font-subsetter-web`

2. **添加 Secrets**
   - 点击 "Settings" → "Secrets and variables" → "Actions"
   - 点击 "New repository secret"
   - 添加以下 Secrets：

   **必须添加的 Secrets：**
   ```
   ALIYUN_ACCESS_KEY_ID: 你的 AccessKey ID
   ALIYUN_ACCESS_KEY_SECRET: 你的 AccessKey Secret
   ALIYUN_ACR_USERNAME: ACR 用户名（通常是你的阿里云账号）
   ALIYUN_ACR_PASSWORD: ACR 密码（在 ACR 控制台设置）
   ALIYUN_ACR_NAMESPACE: 你的命名空间（如：trimtype）
   ```

---

## 🚀 部署步骤

### 步骤 1：确认 Dockerfile 存在

项目根目录已经有 `Dockerfile`，确认一下：

```bash
ls -la Dockerfile
```

### 步骤 2：推送 GitHub Actions 配置

我已经创建了 `.github/workflows/deploy-sae.yml`，现在提交：

```bash
git add .github/workflows/deploy-sae.yml
git commit -m "添加 SAE 自动部署配置"
git push origin main
```

### 步骤 3：在 SAE 创建应用

1. **进入 SAE 控制台**
   - 搜索"Serverless 应用引擎 SAE"
   - 进入控制台

2. **创建应用**
   - 点击"创建应用"
   - 应用名称：`trimtype`
   - 应用描述：`TrimType 字体裁剪工具`
   - 其他保持默认

3. **首次部署**
   - 在"部署应用"页面
   - 选择"镜像部署"
   - 镜像地址：先随便填一个（后续会自动更新）
   - 实例规格：1 Core 2 GiB（够用了）
   - 点击"确定"创建应用

### 步骤 4：触发自动部署

1. **推送代码到 GitHub**
   ```bash
   git push origin main
   ```

2. **查看 GitHub Actions**
   - 进入 GitHub 仓库
   - 点击 "Actions" 标签
   - 查看部署进度

3. **等待部署完成**
   - GitHub Actions 会自动：
     - 构建 Docker 镜像
     - 推送到 ACR
     - 部署到 SAE

4. **验证部署**
   - 在 SAE 控制台查看应用状态
   - 获取访问地址
   - 在浏览器中访问测试

---

## 🔄 后续更新

**完全自动化！**

```bash
# 本地修改代码
# ... 编辑文件 ...

# 提交并推送
git add .
git commit -m "更新内容"
git push origin main

# GitHub Actions 自动触发部署！
# 无需任何手动操作
```

---

## 📋 配置说明

### GitHub Actions 工作流说明

`.github/workflows/deploy-sae.yml` 会自动：

1. **检出代码**：从 GitHub 拉取最新代码
2. **构建镜像**：使用 Dockerfile 构建镜像
3. **推送镜像**：推送到阿里云 ACR
4. **部署应用**：自动部署到 SAE

### 修改配置

如果需要修改，编辑 `.github/workflows/deploy-sae.yml`：

- **修改区域**：`region: cn-hangzhou` 改为你的区域
- **修改应用名**：`app-name: trimtype` 改为你的应用名
- **修改命名空间**：在 Secrets 中修改 `ALIYUN_ACR_NAMESPACE`

---

## ❓ 常见问题

### Q: GitHub Actions 执行失败？

**检查：**
1. Secrets 是否配置正确
2. AccessKey 权限是否足够
3. ACR 仓库是否存在
4. SAE 应用是否已创建

### Q: 镜像构建失败？

**检查：**
1. Dockerfile 是否正确
2. 依赖是否都能安装
3. 查看 GitHub Actions 日志

### Q: 部署失败？

**检查：**
1. SAE 应用是否已创建
2. 镜像地址是否正确
3. 查看 SAE 应用日志

### Q: 如何回滚？

**在 SAE 控制台：**
1. 进入应用详情
2. 查看"变更记录"
3. 选择之前的版本
4. 点击"回滚"

---

## 🎯 总结

**实现的效果：**
- ✅ GitHub 推送代码 → 自动部署
- ✅ 完全自动化，无需手动操作
- ✅ 和 Vercel 一样的体验！

**需要做的：**
1. 配置 GitHub Secrets
2. 创建 SAE 应用
3. 推送代码

**之后：**
- 每次推送自动部署
- 完全自动化！

---

需要我帮你：
1. 检查 Dockerfile 是否正确？
2. 修改 GitHub Actions 配置？
3. 解决部署问题？

告诉我你现在到哪一步了！

