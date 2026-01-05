from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from typetrim import process_font_file  # 导入 TrimType 字体裁剪功能
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS  # 添加这行
import uuid

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__,
    template_folder='templates',  # 明确指定模板目录
    static_folder='static'        # 明确指定静态文件目录
)

# 设置上传文件大小限制为 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

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

# 错误消息翻译函数
def translate_error_message(error_msg):
    """将技术错误消息翻译为用户友好的中文提示"""
    error_msg_lower = error_msg.lower()
    
    # 常见错误消息映射
    translations = {
        "not a font collection": "该文件不是有效的字体集合格式，已尝试按普通字体处理",
        "ttc 文件中未找到可用子字体": "字体集合文件中未找到可用的子字体",
        "未选择任何字符集": "请至少选择一个字符集选项（如英文字母、数字等）",
        "字符集无效或为空": "字符集配置错误，请重新选择字符集选项",
        "没有有效的 unicode 字符": "未找到有效的字符，请检查字符集选项",
        "字符集处理失败": "字符集处理失败，请重新选择字符集选项",
        "字体处理失败": "字体裁剪处理失败，可能是字体文件格式不支持或已损坏",
        "无法保存处理后的字体": "保存处理后的字体文件失败，请重试",
        "处理后的文件大小异常，可能处理失败": "处理后的文件异常，可能是字体文件格式问题",
        "too many requests": "请求过于频繁，请稍后再试",
        "forbidden": "访问被拒绝，可能是文件过大或服务器限制",
        "internal server error": "服务器内部错误，请稍后重试",
        "load failed": "无法加载字体文件，可能是文件格式不正确、已损坏或不受支持",
        "failed to load": "无法加载字体文件，可能是文件格式不正确、已损坏或不受支持",
    }
    
    # 尝试匹配错误消息
    for key, value in translations.items():
        if key in error_msg_lower:
            return value
    
    # 如果没有匹配，返回原始消息（如果已经是中文）或通用提示
    if any('\u4e00' <= char <= '\u9fff' for char in error_msg):
        return error_msg
    else:
        return f"处理失败：{error_msg}"

# 添加错误处理
@app.errorhandler(500)
def handle_500_error(error):
    return jsonify({
        "error": "服务器内部错误",
        "message": "服务器处理请求时发生错误，请稍后重试"
    }), 500

@app.errorhandler(413)
def handle_413_error(error):
    return jsonify({
        "error": "文件太大",
        "message": "上传的文件超过100MB限制"
    }), 413

@app.route('/')
def index():
    try:
        app.logger.debug('Attempting to render index.html')
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering template: {str(e)}')
        return str(e), 500

def allowed_file(filename):
    """检查文件是否是允许的字体格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'ttf', 'otf', 'woff', 'woff2', 'eot', 'ttc'}

@app.route('/process', methods=['POST'])
@limiter.exempt  # 明确豁免速率限制，允许批量处理
def process_font():
    if 'font' not in request.files:
        return jsonify({'error': '未找到字体文件'}), 400
    
    font_file = request.files['font']
    if font_file.filename == '':
        return jsonify({'error': '未选择字体文件'}), 400
    
    if not allowed_file(font_file.filename):
        return jsonify({'error': '不支持的字体格式'}), 400
    
    try:
        # 保存原始文件名和大小
        original_filename = font_file.filename
        original_size = len(font_file.read())
        font_file.seek(0)  # 重置文件指针
        
        # 检查文件大小
        if original_size < 1024:  # 小于1KB
            return jsonify({'error': '文件大小异常，可能不是有效的字体文件'}), 400
        if original_size > 100 * 1024 * 1024:  # 大于100MB
            return jsonify({'error': '文件超过100MB限制'}), 400
        
        # 获取选项
        options = json.loads(request.form.get('options', '{}'))
        logging.debug(f"接收到的选项: {options}")
        
        # 使用临时文件保存上传的字体
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as input_temp:
            font_file.save(input_temp.name)
            input_path = input_temp.name
            
        try:
            # 使用 TrimType 处理字体
            logging.debug(f"开始处理字体文件: {input_path}")
            result = process_font_file(input_path, options)
            
            # 检查处理后的文件大小
            if os.path.getsize(result['output_path']) < 1024:  # 小于1KB
                raise Exception("处理后的文件大小异常，可能处理失败，请检查字体文件是否有效")
            
            logging.debug(f"字体处理结果: {result}")
            
            # 清理输入临时文件
            os.unlink(input_path)
            
            # 添加下载链接到结果
            result['download_url'] = f"/download/{os.path.basename(result['output_path'])}?original_name={original_filename}"
            result['filename'] = original_filename
            
            return jsonify(result)
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            import traceback
            stack_trace = traceback.format_exc()
            logging.error(f"字体处理错误: {error_msg}")
            logging.error(f"错误类型: {error_type}")
            logging.error(f"错误堆栈: {stack_trace}")
            
            # 清理临时文件
            try:
                os.unlink(input_path)
                if 'result' in locals() and 'output_path' in result:
                    os.unlink(result['output_path'])
            except:
                pass
                
            # 翻译错误消息为用户友好的中文
            friendly_error = translate_error_message(error_msg)
            return jsonify({
                'error': friendly_error
            }), 500
        
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
                
        # 翻译错误消息为用户友好的中文
        friendly_error = translate_error_message(error_msg)
        return jsonify({
            'error': friendly_error
        }), 500

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    try:
        # 获取原始文件名
        original_name = request.args.get('original_name', filename)
        
        # 从临时存储获取文件
        temp_path = os.path.join(get_temp_dir(), filename)
        if not os.path.exists(temp_path):
            return jsonify({'error': '文件不存在或已过期'}), 404
        
        response = send_file(
            temp_path,
            as_attachment=True,
            mimetype='font/ttf',
            download_name=original_name  # 使用原始文件名
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
        friendly_error = translate_error_message(str(e))
        return jsonify({'error': friendly_error}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    import os
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=True) 