from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from typetrim import process_font_file  # 导入原始的 TypeTrim 功能
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS  # 添加这行

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__,
    template_folder='templates',  # 明确指定模板目录
    static_folder='static'        # 明确指定静态文件目录
)

# 启用 CORS
CORS(app)

# 添加访问限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 添加安全头
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'  # 防止点击劫持
    response.headers['X-Content-Type-Options'] = 'nosniff'  # 防止内容类型嗅探
    response.headers['X-XSS-Protection'] = '1; mode=block'  # XSS 保护
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # 强制 HTTPS
    return response

# 使用临时目录
def get_temp_dir():
    return tempfile.gettempdir()

# 添加错误处理
@app.errorhandler(500)
def handle_500_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error)
    }), 500

@app.route('/')
def index():
    try:
        app.logger.debug('Attempting to render index.html')
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering template: {str(e)}')
        return str(e), 500

@app.route('/process', methods=['POST'])
@limiter.limit("30 per minute")
def process_font():
    if 'font' not in request.files:
        return jsonify({'error': '请选择字体文件'}), 400
    
    font_file = request.files['font']
    if font_file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    try:
        # 获取选项
        options = json.loads(request.form.get('options', '{}'))
        logging.debug(f"接收到的选项: {options}")
        
        # 使用临时文件保存上传的字体
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(font_file.filename)[1]) as input_temp:
            font_file.save(input_temp.name)
            input_path = input_temp.name
            
        try:
            # 使用 TypeTrim 处理字体，传入选项
            logging.debug(f"开始处理字体文件: {input_path}")
            # 将 customChars 转换为 custom_chars
            if 'customChars' in options:
                options['custom_chars'] = options.pop('customChars')
            result = process_font_file(input_path, options)
            logging.debug(f"字体处理结果: {result}")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            import traceback
            stack_trace = traceback.format_exc()
            logging.error(f"字体处理错误: {error_msg}")
            logging.error(f"错误类型: {error_type}")
            logging.error(f"错误堆栈: {stack_trace}")
            return jsonify({
                'error': f"处理失败: {error_msg}",
                'error_type': error_type,
                'stack_trace': stack_trace
            }), 500
        
        # 清理输入临时文件
        os.unlink(input_path)
        
        # 添加下载链接到结果
        result['download_url'] = f"/download/{os.path.basename(result['output_path'])}"
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        import traceback
        stack_trace = traceback.format_exc()
        logging.error(f"处理过程发生错误: {error_msg}")
        logging.error(f"错误类型: {error_type}")
        logging.error(f"错误堆栈: {stack_trace}")
        # 确保清理临时文件
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass
        return jsonify({
            'error': f"处理失败: {error_msg}",
            'error_type': error_type,
            'stack_trace': stack_trace
        }), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        # 从临时存储获取文件
        temp_path = os.path.join(get_temp_dir(), filename)
        if not os.path.exists(temp_path):
            return jsonify({'error': '文件不存在或已过期'}), 404
        
        response = send_file(
            temp_path,
            as_attachment=True,
            mimetype='font/ttf',
            download_name=os.path.basename(filename)
        )
        
        # 文件发送后删除临时文件
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(temp_path)
            except:
                pass
                
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    app.run(debug=True) 