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
    chars = set()
    
    if options.get('latin'):
        # 只保留基本拉丁字母，不包括变体
        chars.update('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    if options.get('numbers'):
        chars.update('0123456789')
    
    if options.get('en_punctuation'):
        chars.update(',.!?;:\'"()[]{}@#$%&*_+-=\\|/<>~`')
    
    if options.get('cn_punctuation'):
        chars.update('，。！？；：""''「」『』（）【】《》〈〉…—～·、')
    
    if options.get('chinese_common'):
        # 添加常用汉字集
        with open('data/common_chinese.txt', 'r', encoding='utf-8') as f:
            chars.update(f.read().strip())
    
    if options.get('chinese_name'):
        # 添加人名用字集
        with open('data/name_chinese.txt', 'r', encoding='utf-8') as f:
            chars.update(f.read().strip())
    
    if options.get('currency'):
        chars.update('$€¥£¢₩₪₱₹')
    
    if options.get('math'):
        chars.update('+-×÷=≠<>≤≥±∑∏√∫∞°')
    
    if options.get('copyright'):
        chars.update('©®™℠℗')
    
    if options.get('arrows'):
        chars.update('←→↑↓↔↕⇄⇅↖↗↘↙')
    
    # 添加自定义字符
    if options.get('customChars'):
        chars.update(options['customChars'])
    
    # 添加基本空格
    chars.add(' ')
    
    return chars

def process_font_file(font_path, options):
    """处理字体文件，返回处理后的字体文件路径"""
    try:
        # 加载字体
        font = TTFont(font_path)
        
        # 获取要保留的字符集
        chars = get_chars_by_options(options)
        if not chars:
            raise ValueError("未选择任何字符集")
        
        # 创建子集化器，设置更严格的选项
        subsetter = Subsetter()
        
        # 只保留基本字符的设置
        subsetter.options.layout_features = ['kern']  # 只保留基本的字距调整
        subsetter.options.name_IDs = [1, 2]  # 只保留字体名称和样式名称
        subsetter.options.recommended_glyphs = True  # 保留推荐的基本字形
        subsetter.options.ignore_missing_glyphs = True
        
        # 将Unicode字符转换为字形ID
        unicodes = set()
        for char in chars:
            try:
                unicode_value = ord(char)
                unicodes.add(unicode_value)
            except TypeError:
                print(f"警告: 无法处理字符 {char}")
        
        # 设置要保留的Unicode值
        subsetter.populate(unicodes=unicodes)
        
        # 应用子集化
        subsetter.subset(font)
        
        # 保存处理后的字体
        output_path = os.path.join(tempfile.gettempdir(), 'processed_' + os.path.basename(font_path))
        font.save(output_path)
        
        return output_path
        
    except Exception as e:
        print(f"处理字体时出错: {str(e)}")
        raise 