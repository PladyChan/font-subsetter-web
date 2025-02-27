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
import threading
from filelock import FileLock
import uuid
import shutil

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

# 添加全局锁字典
processing_locks = {}
processing_status = {}

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
    # 在 Vercel 环境中使用 /tmp 目录
    if os.environ.get('VERCEL'):
        tmp_dir = '/tmp'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir
    return tempfile.gettempdir()

# 添加错误处理
@app.errorhandler(500)
def handle_500_error(error):
    logging.error(f"500 错误: {str(error)}")
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error)
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
           filename.rsplit('.', 1)[1].lower() in {'ttf', 'otf', 'woff', 'woff2', 'eot'}

@app.route('/process', methods=['POST'])
@limiter.limit("30 per minute")
def process_font():
    if 'font' not in request.files:
        return jsonify({'error': '未找到字体文件'}), 400
    
    font_file = request.files['font']
    if font_file.filename == '':
        return jsonify({'error': '未选择字体文件'}), 400
    
    if not allowed_file(font_file.filename):
        return jsonify({'error': '不支持的字体格式'}), 400
    
    try:
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存原始文件名和大小
        original_filename = secure_filename(font_file.filename)
        font_data = font_file.read()
        original_size = len(font_data)
        
        # 检查文件大小
        if original_size < 1024:  # 小于1KB
            return jsonify({'error': '文件大小异常，可能不是有效的字体文件'}), 400
        if original_size > 100 * 1024 * 1024:  # 大于100MB
            return jsonify({'error': '文件超过100MB限制'}), 400
        
        # 获取选项
        options = json.loads(request.form.get('options', '{}'))
        logging.debug(f"接收到的选项: {options}")
        
        # 创建任务状态
        processing_status[task_id] = {
            'status': 'preparing',
            'progress': 0,
            'message': '准备处理文件...'
        }
        
        # 确保临时目录存在
        temp_dir = get_temp_dir()
        os.makedirs(temp_dir, exist_ok=True)
        
        # 使用临时文件保存上传的字体
        input_path = os.path.join(temp_dir, f"{task_id}_input{os.path.splitext(original_filename)[1]}")
        with open(input_path, 'wb') as f:
            f.write(font_data)
            
        # 创建文件锁
        lock_path = os.path.join(temp_dir, f"{task_id}.lock")
        processing_locks[task_id] = FileLock(lock_path)
        
        # 启动后台处理线程
        thread = threading.Thread(
            target=process_font_task,
            args=(task_id, input_path, options, original_filename)
        )
        thread.daemon = True  # 设置为守护线程，确保主进程退出时线程也会退出
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'processing',
            'status_url': f'/status/{task_id}'
        })
        
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
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if 'lock_path' in locals() and os.path.exists(lock_path):
                    os.unlink(lock_path)
            except Exception as cleanup_error:
                logging.error(f"清理临时文件时出错: {str(cleanup_error)}")
                
        return jsonify({
            'error': f"处理失败: {error_msg}",
            'error_type': error_type
        }), 500

def process_font_task(task_id, input_path, options, original_filename):
    lock = processing_locks.get(task_id)
    if not lock:
        logging.error(f"任务 {task_id} 的锁不存在")
        return
        
    try:
        with lock:
            processing_status[task_id]['status'] = 'processing'
            processing_status[task_id]['progress'] = 30
            processing_status[task_id]['message'] = '正在处理字体...'
            
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
                
            # 使用 TypeTrim 处理字体
            logging.debug(f"开始处理字体文件: {input_path}")
            result = process_font_file(input_path, options)
            
            # 检查处理后的文件是否存在
            if not os.path.exists(result['output_path']):
                raise FileNotFoundError(f"输出文件不存在: {result['output_path']}")
                
            # 检查处理后的文件大小
            output_size = os.path.getsize(result['output_path'])
            if output_size < 1024:  # 小于1KB
                raise Exception(f"处理后的文件大小异常 ({output_size} 字节)，可能处理失败")
            
            # 复制输出文件到一个更稳定的位置
            output_filename = f"{task_id}_output{os.path.splitext(original_filename)[1]}"
            stable_output_path = os.path.join(get_temp_dir(), output_filename)
            shutil.copy2(result['output_path'], stable_output_path)
            
            # 更新结果中的输出路径
            result['output_path'] = stable_output_path
            
            processing_status[task_id]['status'] = 'completed'
            processing_status[task_id]['progress'] = 100
            processing_status[task_id]['message'] = '处理完成'
            processing_status[task_id]['result'] = {
                'download_url': f"/download/{output_filename}?original_name={original_filename}",
                'filename': original_filename,
                'original_size': result['original_size'],
                'new_size': result['new_size'],
                'reduction': result['reduction']
            }
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Task {task_id} failed: {error_msg}")
        import traceback
        logging.error(traceback.format_exc())
        
        if task_id in processing_status:
            processing_status[task_id]['status'] = 'error'
            processing_status[task_id]['message'] = f"处理失败: {error_msg}"
        
    finally:
        # 清理资源
        try:
            if os.path.exists(input_path):
                os.unlink(input_path)
            
            # 清理锁文件
            lock_path = os.path.join(get_temp_dir(), f"{task_id}.lock")
            if os.path.exists(lock_path):
                os.unlink(lock_path)
                
            # 从字典中移除锁
            if task_id in processing_locks:
                del processing_locks[task_id]
                
        except Exception as cleanup_error:
            logging.error(f"清理资源时出错: {str(cleanup_error)}")

@app.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id not in processing_status:
        return jsonify({'error': '任务不存在'}), 404
        
    status = processing_status[task_id]
    
    # 如果任务完成或出错，从状态字典中删除
    if status['status'] in ['completed', 'error']:
        status_copy = status.copy()
        # 延迟删除，确保客户端有足够时间获取结果
        if 'delete_after' not in status:
            status['delete_after'] = 5  # 5次请求后删除
        else:
            status['delete_after'] -= 1
            if status['delete_after'] <= 0:
                del processing_status[task_id]
        return jsonify(status_copy)
        
    return jsonify(status)

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    try:
        # 获取原始文件名
        original_name = request.args.get('original_name', filename)
        
        # 从临时存储获取文件
        temp_path = os.path.join(get_temp_dir(), filename)
        if not os.path.exists(temp_path):
            return jsonify({'error': '文件不存在或已过期'}), 404
        
        # 检查文件大小
        file_size = os.path.getsize(temp_path)
        if file_size < 1024:  # 小于1KB
            return jsonify({'error': f'文件大小异常 ({file_size} 字节)，可能已损坏'}), 400
        
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
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logging.error(f"删除临时文件时出错: {str(e)}")
                
        return response
        
    except Exception as e:
        logging.error(f"下载文件时出错: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
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