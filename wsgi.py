from app import app
from config import Config

# 初始化应用配置
Config.init_app(app)

# 添加错误处理
@app.errorhandler(500)
def handle_500_error(error):
    return str(error), 500

if __name__ == "__main__":
    app.run() 