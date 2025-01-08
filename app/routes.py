from flask import Blueprint, render_template, request, send_file, jsonify
from app.utils import process_font
import os
import json
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/process', methods=['POST'])
def process():
    if 'font' not in request.files:
        return jsonify({'error': '请选择字体文件'}), 400
    
    font_file = request.files['font']
    if font_file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 获取选项
    options = request.form.get('options', '{}')
    options = json.loads(options)
    
    try:
        # 保存上传的文件
        filename = secure_filename(font_file.filename)
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        font_file.save(input_path)
        
        # 处理字体
        output_filename = f"subset_{filename}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        if process_font(input_path, output_path, options):
            # 计算文件大小
            original_size = os.path.getsize(input_path) / 1024
            new_size = os.path.getsize(output_path) / 1024
            reduction = ((original_size - new_size) / original_size * 100)
            
            # 清理上传的文件
            os.remove(input_path)
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'original_size': f"{original_size:.1f}KB",
                'new_size': f"{new_size:.1f}KB",
                'reduction': f"{reduction:.1f}%"
            })
        else:
            return jsonify({'error': '处理失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(current_app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    ) 