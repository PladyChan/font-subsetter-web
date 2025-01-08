from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string
import os

def process_font(input_path, output_path, options):
    try:
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
            chars.update('éèêëāīūēīōǖ')
        
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
        
        font.save(output_path)
        return True
        
    except Exception as e:
        print(f"Error processing font: {str(e)}")
        return False 