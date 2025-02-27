#!/bin/bash

# TypeTrim 阿里云部署脚本 (适用于 Alibaba Cloud Linux)
# 作者: PladyChan
# 日期: $(date +%Y-%m-%d)

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="typetrim"
APP_DIR="/var/www/$APP_NAME"
DOMAIN="typetrim.com"  # 请修改为您的域名或服务器IP
NGINX_CONF="/etc/nginx/conf.d/$APP_NAME.conf"
SUPERVISOR_CONF="/etc/supervisord.d/$APP_NAME.ini"

# 打印带颜色的信息
info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# 检查是否以 root 用户运行
if [ "$(id -u)" != "0" ]; then
   error "此脚本必须以 root 用户运行"
fi

info "开始部署 $APP_NAME 到阿里云..."

# 安装必要的软件包
info "安装必要的软件包..."
yum update -y
yum install -y python3 python3-pip nginx epel-release
yum install -y supervisor certbot python3-certbot-nginx

# 创建应用目录
info "创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/static
mkdir -p $APP_DIR/templates
mkdir -p $APP_DIR/processed

# 复制应用文件
info "复制应用文件..."
cp -r ../*.py $APP_DIR/
cp -r ../requirements.txt $APP_DIR/
cp -r ../static/* $APP_DIR/static/
cp -r ../templates/* $APP_DIR/templates/

# 设置权限
info "设置权限..."
chown -R nginx:nginx $APP_DIR
chmod -R 755 $APP_DIR

# 创建虚拟环境并安装依赖
info "创建虚拟环境并安装依赖..."
python3 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install --upgrade pip
$APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
$APP_DIR/venv/bin/pip install gunicorn

# 配置 Nginx
info "配置 Nginx..."
cp ./nginx.conf $NGINX_CONF
sed -i "s/{{DOMAIN}}/$DOMAIN/g" $NGINX_CONF

# 确保 Nginx 目录存在
mkdir -p /var/log/nginx
touch /var/log/nginx/error.log
touch /var/log/nginx/access.log

# 配置 Supervisor
info "配置 Supervisor..."
mkdir -p /etc/supervisord.d/
cp ./supervisor.conf $SUPERVISOR_CONF
sed -i "s|/var/www/typetrim|$APP_DIR|g" $SUPERVISOR_CONF

# 确保 Supervisor 日志目录存在
mkdir -p /var/log/supervisor
touch /var/log/supervisor/$APP_NAME.out.log
touch /var/log/supervisor/$APP_NAME.err.log

# 启动服务
info "启动服务..."
systemctl enable nginx
systemctl enable supervisord
systemctl restart nginx
systemctl restart supervisord

# 等待 Supervisor 启动
sleep 5

# 检查 Supervisor 是否正常运行
if ! command -v supervisorctl &> /dev/null; then
    warn "supervisorctl 命令不可用，跳过 Supervisor 重启"
else
    supervisorctl reread
    supervisorctl update
    supervisorctl restart $APP_NAME
fi

# 配置防火墙
info "配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    info "防火墙已配置"
else
    warn "未检测到 firewalld，请手动确保端口 80 和 443 已开放"
fi

# 配置 SSL 证书
info "配置 SSL 证书..."
if [[ "$DOMAIN" != *.* ]]; then
    warn "域名格式不正确或使用的是 IP 地址，跳过 SSL 配置"
else
    if command -v certbot &> /dev/null; then
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || warn "SSL 证书配置失败，请稍后手动配置"
    else
        warn "未检测到 certbot，跳过 SSL 配置"
    fi
fi

info "部署完成！"
info "您的应用现在应该可以通过 http://$DOMAIN 访问"
info "如果配置了 SSL 证书，也可以通过 https://$DOMAIN 访问"
info "如果遇到问题，请检查以下日志文件："
info "- Nginx 错误日志: /var/log/nginx/error.log"
info "- Supervisor 日志: /var/log/supervisor/$APP_NAME.err.log"
info "- 应用日志: /var/log/supervisor/$APP_NAME.out.log" 