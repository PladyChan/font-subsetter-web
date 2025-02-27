from flask import Flask, render_template, request, send_file, jsonify, send_from_directory, url_for
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
import time
import traceback

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

# 全局任务状态字典
task_status_dict = {}

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
    """处理上传的字体文件"""
    try:
        # 检查是否有文件上传
        if 'font' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        font_file = request.files['font']
        
        # 检查文件名是否为空
        if font_file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 检查文件类型
        if not font_file.filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
            return jsonify({'error': '不支持的文件类型，请上传TTF、OTF、WOFF或WOFF2格式的字体文件'}), 400
        
        # 获取选项
        options = {}
        if 'options' in request.form:
            try:
                options = json.loads(request.form['options'])
            except json.JSONDecodeError:
                return jsonify({'error': '选项格式错误'}), 400
        
        # 创建临时目录
        temp_dir = get_temp_dir()
        
        # 生成安全的文件名
        original_filename = secure_filename(font_file.filename)
        input_filename = f"{uuid.uuid4()}_{original_filename}"
        input_file = os.path.join(temp_dir, input_filename)
        
        # 保存上传的文件
        font_file.save(input_file)
        
        # 检查文件大小
        file_size = os.path.getsize(input_file)
        if file_size > 100 * 1024 * 1024:  # 100MB
            os.remove(input_file)
            return jsonify({'error': '文件大小超过100MB限制'}), 413
        
        if file_size < 1024:  # 1KB
            os.remove(input_file)
            return jsonify({'error': '文件过小，可能不是有效的字体文件'}), 400
        
        # 生成输出文件名
        output_filename = f"optimized_{input_filename}"
        output_file = os.path.join(temp_dir, output_filename)
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        task_status_dict[task_id] = {
            'status': 'pending',
            'message': '任务已创建，等待处理',
            'progress': 0,
            'original_filename': original_filename,
            'input_file': input_file,
            'output_file': output_file,
            'output_filename': output_filename,
            'created_time': time.time()
        }
        
        # 启动后台线程处理任务
        threading.Thread(
            target=process_font_task,
            args=(task_id, input_file, output_file, options),
            daemon=True
        ).start()
        
        # 返回任务ID
        return jsonify({
            'task_id': task_id,
            'message': '任务已创建，正在处理'
        })
        
    except Exception as e:
        app.logger.error(f"创建处理任务失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/status/<task_id>')
def task_status(task_id):
    """获取任务状态"""
    if task_id not in task_status_dict:
        return jsonify({
            'status': 'error',
            'message': '任务不存在或已过期'
        }), 404
    
    status_data = task_status_dict[task_id]
    
    # 如果任务已完成，添加下载链接
    if status_data['status'] == 'completed':
        # 确保结果包含所有必要的信息
        if 'result' not in status_data:
            status_data['result'] = {}
        
        if 'download_url' not in status_data['result']:
            output_filename = status_data.get('output_filename', '')
            if output_filename:
                status_data['result']['download_url'] = url_for('download_file', filename=os.path.basename(output_filename))
        
        # 确保包含文件大小信息
        if 'original_size' not in status_data['result'] and 'original_size_bytes' in status_data:
            status_data['result']['original_size'] = format_file_size(status_data['original_size_bytes'])
        
        if 'new_size' not in status_data['result'] and 'new_size_bytes' in status_data:
            status_data['result']['new_size'] = format_file_size(status_data['new_size_bytes'])
        
        if 'reduction' not in status_data['result'] and 'original_size_bytes' in status_data and 'new_size_bytes' in status_data:
            original_size = status_data['original_size_bytes']
            new_size = status_data['new_size_bytes']
            if original_size > 0:
                reduction_percentage = ((original_size - new_size) / original_size) * 100
                status_data['result']['reduction'] = f"{reduction_percentage:.1f}%"
            else:
                status_data['result']['reduction'] = "0%"
        
        if 'filename' not in status_data['result'] and 'original_filename' in status_data:
            status_data['result']['filename'] = status_data['original_filename']
    
    # 如果任务已完成或出错，并且已经过了一定时间，可以清理任务状态
    if status_data['status'] in ['completed', 'error'] and 'completed_time' in status_data:
        completed_time = status_data['completed_time']
        if time.time() - completed_time > 3600:  # 1小时后清理
            # 延迟删除，确保客户端有足够时间获取结果
            task_status_dict.pop(task_id, None)
    
    return jsonify(status_data)

@app.route('/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    try:
        temp_dir = get_temp_dir()
        return send_from_directory(temp_dir, filename, as_attachment=True)
    except Exception as e:
        app.logger.error(f"下载文件时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def process_font_task(task_id, input_file, output_file, options):
    """处理字体文件的后台任务"""
    try:
        # 更新任务状态为处理中
        task_status_dict[task_id]['status'] = 'processing'
        task_status_dict[task_id]['message'] = '正在处理字体...'
        task_status_dict[task_id]['progress'] = 10
        
        # 获取原始文件大小
        original_size = os.path.getsize(input_file)
        task_status_dict[task_id]['original_size_bytes'] = original_size
        task_status_dict[task_id]['original_filename'] = os.path.basename(input_file)
        
        # 检查文件大小
        if original_size < 1024:  # 小于1KB
            raise ValueError(f"文件过小 ({format_file_size(original_size)}), 可能不是有效的字体文件")
        
        if original_size > 100 * 1024 * 1024:  # 大于100MB
            raise ValueError(f"文件过大 ({format_file_size(original_size)}), 超过100MB限制")
        
        # 更新进度
        task_status_dict[task_id]['progress'] = 30
        task_status_dict[task_id]['message'] = '正在分析字体...'
        
        # 处理字体
        subsetter = Subsetter()
        
        # 设置子集化选项
        subsetter_options = SubsetterOptions()
        
        # 保留.notdef字形
        subsetter_options.notdef_glyph = True
        subsetter_options.notdef_outline = True
        
        # 根据用户选择设置选项
        if options.get('latin', False):
            subsetter_options.layout_features = ['*']
            subsetter_options.unicodes = ['U+0000-007F']  # 基本拉丁字母
        
        if options.get('latin_ext', False):
            subsetter_options.layout_features = ['*']
            subsetter_options.unicodes = ['U+0000-024F']  # 扩展拉丁字母
        
        if options.get('basic_punctuation', False):
            subsetter_options.layout_features = ['*']
            subsetter_options.unicodes = ['U+0020-002F', 'U+003A-0040', 'U+005B-0060', 'U+007B-007E']  # 基本标点
        
        if options.get('ligatures', False):
            subsetter_options.layout_features.append('liga')
            subsetter_options.layout_features.append('dlig')
        else:
            subsetter_options.layout_features.remove('liga') if 'liga' in subsetter_options.layout_features else None
            subsetter_options.layout_features.remove('dlig') if 'dlig' in subsetter_options.layout_features else None
        
        if options.get('fractions', False):
            subsetter_options.layout_features.append('frac')
        else:
            subsetter_options.layout_features.remove('frac') if 'frac' in subsetter_options.layout_features else None
        
        if options.get('superscript_subscript', False):
            subsetter_options.layout_features.append('sups')
            subsetter_options.layout_features.append('subs')
        else:
            subsetter_options.layout_features.remove('sups') if 'sups' in subsetter_options.layout_features else None
            subsetter_options.layout_features.remove('subs') if 'subs' in subsetter_options.layout_features else None
        
        if options.get('diacritics', False):
            subsetter_options.layout_features.append('ccmp')
            subsetter_options.layout_features.append('mark')
        else:
            subsetter_options.layout_features.remove('ccmp') if 'ccmp' in subsetter_options.layout_features else None
            subsetter_options.layout_features.remove('mark') if 'mark' in subsetter_options.layout_features else None
        
        # 自定义字符
        if 'customChars' in options and options['customChars']:
            custom_chars = options['customChars']
            subsetter_options.text = custom_chars
        
        # 更新进度
        task_status_dict[task_id]['progress'] = 60
        task_status_dict[task_id]['message'] = '正在优化字体...'
        
        # 执行子集化
        font = TTFont(input_file)
        subsetter.subset(font, options=subsetter_options)
        
        # 更新进度
        task_status_dict[task_id]['progress'] = 80
        task_status_dict[task_id]['message'] = '正在保存字体...'
        
        # 保存结果
        font.save(output_file)
        
        # 检查输出文件大小
        new_size = os.path.getsize(output_file)
        if new_size < 1024:  # 小于1KB
            raise ValueError(f"处理后文件过小 ({format_file_size(new_size)}), 可能处理失败")
        
        task_status_dict[task_id]['new_size_bytes'] = new_size
        
        # 计算减少的百分比
        reduction_percentage = ((original_size - new_size) / original_size) * 100
        
        # 更新任务状态为已完成
        task_status_dict[task_id]['status'] = 'completed'
        task_status_dict[task_id]['message'] = '处理完成'
        task_status_dict[task_id]['progress'] = 100
        task_status_dict[task_id]['completed_time'] = time.time()
        
        # 设置结果信息
        task_status_dict[task_id]['result'] = {
            'filename': os.path.basename(output_file),
            'original_size': format_file_size(original_size),
            'new_size': format_file_size(new_size),
            'reduction': f"{reduction_percentage:.1f}%",
            'download_url': url_for('download_file', filename=os.path.basename(output_file))
        }
        
        # 记录成功日志
        app.logger.info(f"任务 {task_id} 成功完成: {input_file} -> {output_file}, 大小减少: {reduction_percentage:.1f}%")
        
    except Exception as e:
        # 更新任务状态为错误
        task_status_dict[task_id]['status'] = 'error'
        task_status_dict[task_id]['message'] = str(e)
        task_status_dict[task_id]['completed_time'] = time.time()
        
        # 记录错误日志
        app.logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        
        # 清理临时文件
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception as cleanup_error:
            app.logger.error(f"清理临时文件失败: {str(cleanup_error)}")

def format_file_size(size_in_bytes):
    """格式化文件大小"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    app.run(debug=True) 