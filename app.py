from flask import Flask, render_template, request, send_file, jsonify
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string
import os
from werkzeug.utils import secure_filename
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
            chars.update('éèêëāīūēīō�')
        
        # 修改这部分以处理 GSUB 表
        subsetter_options.layout_features = ['kern']  # 只保留 kerning
        subsetter_options.ignore_missing_glyphs = True  # 忽略缺失的字形
        subsetter_options.ignore_missing_unicodes = True  # 忽略缺失的 Unicode
        subsetter_options.desubroutinize = True  # 优化字体大小
        
        # 处理字体
        subsetter = Subsetter(options=subsetter_options)
        subsetter.populate(unicodes=[ord(char) for char in chars])
        
        try:
            subsetter.subset(font)
        except Exception as e:
            # 如果第一次失败，尝试不同的选项
            subsetter_options.layout_features = []  # 移除所有特性
            subsetter_options.no_subset_tables += ['GSUB', 'GPOS']  # 不处理这些表
            subsetter = Subsetter(options=subsetter_options)
            subsetter.populate(unicodes=[ord(char) for char in chars])
            subsetter.subset(font)
        
        # 保存处理后的文件
        output_filename = f"subset_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        font.save(output_path)
        
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
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True) 