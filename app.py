from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from typetrim import process_font_file  # 导入原始的 TypeTrim 功能

app = Flask(__name__,
    template_folder='templates',  # 明确指定模板目录
    static_folder='static'        # 明确指定静态文件目录
)

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
        return render_template('index.html')
    except Exception as e:
        return str(e), 500

@app.route('/process', methods=['POST'])
def process_font():
    if 'font' not in request.files:
        return jsonify({'error': '请选择字体文件'}), 400
    
    font_file = request.files['font']
    if font_file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    try:
        # 使用临时文件保存上传的字体
        with tempfile.NamedTemporaryFile(delete=False) as input_temp:
            font_file.save(input_temp.name)
            input_path = input_temp.name
            
        # 使用 TypeTrim 处理字体
        result = process_font_file(input_path)
        
        # 清理临时文件
        os.unlink(input_path)
        
        return jsonify(result)
        
    except Exception as e:
        # 确保清理临时文件
        if 'input_path' in locals():
            os.unlink(input_path)
        return jsonify({'error': str(e)}), 500

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
            download_name=filename
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

if __name__ == '__main__':
    app.run(debug=True) 