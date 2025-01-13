from flask import Flask, render_template, request, send_file, jsonify
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from werkzeug.utils import secure_filename
import string
import os
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# 确保上传和输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_font():
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
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        font_file.save(input_path)
        
        # 加载字体文件
        font = TTFont(input_path)
        
        # 根据选项构建字符集
        chars = set()
        
        # 基础字符
        if options.get('latin'):
            chars.update(string.ascii_letters)
        if options.get('numbers'):
            chars.update(string.digits)
        if options.get('punctuation'):
            chars.update(string.punctuation)
        if options.get('degree'):
            chars.add('°')
        
        # 扩展字符
        if options.get('currency'):
            chars.update('$€¥£')
        if options.get('math'):
            chars.update('+-×÷=')
        if options.get('copyright'):
            chars.update('©®™')
        if options.get('arrows'):
            chars.update('←→↑↓')
        
        # 设置 subsetter 选项
        subsetter_options = Options()
        
        # 特殊功能
        if options.get('ligatures'):
            subsetter_options.layout_features.append('liga')
        if options.get('fractions'):
            subsetter_options.layout_features.append('frac')
        if options.get('superscript'):
            subsetter_options.layout_features.extend(['sups', 'subs'])
        if options.get('diacritics'):
            chars.update('éèêëāīūēīō')
        
        subsetter_options.layout_features = ['kern']
        subsetter_options.ignore_missing_glyphs = True
        subsetter_options.ignore_missing_unicodes = True
        subsetter_options.desubroutinize = True
        
        # 处理字体
        subsetter = Subsetter(options=subsetter_options)
        subsetter.populate(unicodes=[ord(char) for char in chars])
        
        try:
            subsetter.subset(font)
        except Exception as e:
            subsetter_options.layout_features = []
            subsetter_options.no_subset_tables += ['GSUB', 'GPOS']
            subsetter = Subsetter(options=subsetter_options)
            subsetter.populate(unicodes=[ord(char) for char in chars])
            subsetter.subset(font)
        
        # 保存处理后的文件，使用原始文件名
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        try:
            font.save(output_path)
        except Exception as e:
            return jsonify({'error': f'保存文件失败: {str(e)}'}), 500
        
        # 计算文件大小
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        reduction = ((original_size - new_size) / original_size * 100)
        
        # 清理上传的文件
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'filename': filename,  # 使用原始文件名
            'original_size': f"{original_size:.1f}KB",
            'new_size': f"{new_size:.1f}KB",
            'reduction': f"{reduction:.1f}%"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': f'文件不存在: {file_path}'}), 404
        
        # 添加响应头
        response = send_file(
            file_path,
            as_attachment=True,
            mimetype='font/ttf',
            download_name=filename  # 使用原始文件名
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'application/octet-stream'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 