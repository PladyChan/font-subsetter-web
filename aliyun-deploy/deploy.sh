#!/bin/bash

# TypeTrim 阿里云部署脚本
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
DOMAIN="typetrim.com"  # 请修改为您的域名
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
SUPERVISOR_CONF="/etc/supervisor/conf.d/$APP_NAME.conf"

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
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx supervisor certbot python3-certbot-nginx

# 创建应用目录
info "创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/static
mkdir -p $APP_DIR/templates

# 复制应用文件
info "复制应用文件..."
cp -r ../*.py $APP_DIR/
cp -r ../requirements.txt $APP_DIR/
cp -r ../static/* $APP_DIR/static/
cp -r ../templates/* $APP_DIR/templates/

# 设置权限
info "设置权限..."
chown -R www-data:www-data $APP_DIR
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
sed -i "s/typetrim.com/$DOMAIN/g" $NGINX_CONF
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/

# 配置 Supervisor
info "配置 Supervisor..."
cp ./supervisor.conf $SUPERVISOR_CONF
sed -i "s|/var/www/typetrim|$APP_DIR|g" $SUPERVISOR_CONF

# 重启服务
info "重启服务..."
systemctl restart nginx
supervisorctl reread
supervisorctl update
supervisorctl restart $APP_NAME

# 配置 SSL 证书
info "配置 SSL 证书..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

info "部署完成！"
info "您的应用现在应该可以通过 https://$DOMAIN 访问"
info "如果遇到问题，请检查以下日志文件："
info "- Nginx 错误日志: /var/log/nginx/error.log"
info "- Supervisor 日志: /var/log/supervisor/$APP_NAME.err.log"
info "- 应用日志: /var/log/supervisor/$APP_NAME.out.log" 