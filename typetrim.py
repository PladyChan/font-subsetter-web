"""
TypeTrim - Smart Font Subsetting Tool
-----------------------------------
Copyright (c) 2024 PladyChan
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
""" 

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string
import os
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)

def get_chars_by_options(options):
    """根据选项返回需要保留的字符集"""
    chars = set()
    
    # 基础字符
    if options.get('latin', False):
        chars.update(string.ascii_letters)  # 英文字母
    if options.get('numbers', False):
        chars.update(string.digits)         # 数字
    if options.get('punctuation', False):
        chars.update(',.!?;:\'\"()[]{}')   # 标点符号
    if options.get('degree', False):
        chars.add('°')                      # 度数符号
    
    # 扩展字符
    if options.get('currency', False):
        chars.update('$€¥£¢')              # 货币符号
    if options.get('math', False):
        chars.update('+-×÷=≠<>≤≥')         # 数学符号
    if options.get('copyright', False):
        chars.update('©®™')                # 版权符号
    if options.get('arrows', False):
        chars.update('←→↑↓')               # 箭头
    
    # 特殊功能字符
    if options.get('ligatures', False):
        chars.update('ﬁﬂ')                # 连字
    if options.get('fractions', False):
        chars.update('½¼¾')               # 分数
    if options.get('superscript', False):
        chars.update('⁰¹²³⁴⁵⁶⁷⁸⁹')        # 上标
    if options.get('diacritics', False):
        chars.update('áàâäãåāéèêëēíìîïīóòôöõōúùûüūýÿ')  # 变音符号
    
    # 添加自定义字符
    if 'custom_chars' in options and options['custom_chars']:
        chars.update(options['custom_chars'])
    
    logging.debug(f"生成的字符集: {chars}")
    return chars

def process_font_file(input_path, options=None):
    """处理字体文件并返回结果"""
    try:
        # 加载字体文件
        font = TTFont(input_path)
        
        # 根据选项构建字符集
        chars = get_chars_by_options(options or {})
        if not chars:
            raise Exception("未选择任何字符集")
        
        # 设置 subsetter 选项
        subsetter_options = Options()
        subsetter_options.layout_features = ['kern', 'liga', 'frac']
        subsetter_options.ignore_missing_glyphs = True
        subsetter_options.ignore_missing_unicodes = True
        subsetter_options.desubroutinize = True
        
        # 处理字体
        subsetter = Subsetter(options=subsetter_options)
        subsetter.populate(unicodes=[ord(char) for char in chars])
        
        try:
            subsetter.subset(font)
        except Exception as e:
            logging.error(f"字体处理错误（第一次尝试）: {str(e)}")
            # 如果出错，尝试不使用布局特性
            subsetter_options.layout_features = []
            subsetter_options.no_subset_tables += ['GSUB', 'GPOS']
            subsetter = Subsetter(options=subsetter_options)
            subsetter.populate(unicodes=[ord(char) for char in chars])
            subsetter.subset(font)
        
        # 使用临时文件保存输出
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_path)[1]) as output_temp:
            output_path = output_temp.name
            font.save(output_path)
        
        # 计算文件大小
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        reduction = ((original_size - new_size) / original_size * 100)
        
        return {
            'success': True,
            'filename': os.path.basename(input_path),
            'original_size': f"{original_size:.1f}KB",
            'new_size': f"{new_size:.1f}KB",
            'reduction': f"{reduction:.1f}%",
            'output_path': output_path
        }
        
    except Exception as e:
        logging.error(f"处理字体文件时出错: {str(e)}")
        raise Exception(f"处理字体文件时出错: {str(e)}") 