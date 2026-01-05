"""
TrimType字体裁剪工具
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
        chars.add(' ')  # 只保留基本空格
    if options.get('numbers', False):
        chars.update(string.digits)         # 数字
    if options.get('en_punctuation', False):
        # 英文标点和特殊符号，移除多余空格
        chars.update(',.!?;:\'\"()[]{}')
        chars.update('@#$%^&*_+-=\\|/<>~`')
    if options.get('cn_punctuation', False):
        # 中文标点
        chars.update('，。！？；：""''「」『』（）【】《》〈〉…—～·、')
    if options.get('chinese_all', False):
        # 全部常用中日韩统一表意文字与扩展 A
        chars.update(chr(code) for code in range(0x3400, 0x9FFF + 1))
    
    # 扩展字符
    if options.get('currency', False):
        chars.update('$€¥£¢')              # 货币符号
    if options.get('math', False):
        chars.update('+-×÷=≠<>≤≥°')         # 数学符号
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
    if 'customChars' in options and options['customChars']:
        chars.update(options['customChars'])
    
    logging.debug(f"生成的字符集: {chars}")
    return chars

def process_font_file(input_path, options=None):
    """处理字体文件并返回结果"""
    try:
        # 获取原始文件扩展名
        original_ext = os.path.splitext(input_path)[1].lower()
        
        # 加载字体文件
        logging.debug(f"开始加载字体文件: {input_path}")
        if original_ext == '.ttc':
            # TTC 是字体集合，需要指定具体的子字体；默认取第 0 个
            from fontTools.ttLib import TTCollection
            try:
                collection = TTCollection(input_path)
                if not collection.fonts:
                    raise Exception("字体集合文件中未找到可用的子字体")
                font = collection.fonts[0]
                logging.debug(f"TTC 字体集合加载成功，包含 {len(collection.fonts)} 个子字体，默认使用第 0 个")
            except Exception as e:
                # 某些 .ttc 实际可能是普通字体或不符合集合规范，回退为普通字体打开
                error_msg = str(e).lower()
                if "not a font collection" in error_msg:
                    logging.warning("该文件不是有效的字体集合格式，将按普通字体处理")
                else:
                    logging.warning(f"按字体集合解析失败，将按普通字体重试: {e}")
                try:
                    font = TTFont(input_path)
                    logging.debug("按普通字体方式加载成功")
                except Exception as e2:
                    error_msg2 = str(e2).lower()
                    if "load failed" in error_msg2 or "failed to load" in error_msg2:
                        raise Exception("无法加载字体文件，可能是文件格式不正确、已损坏或不受支持")
                    else:
                        raise Exception("无法加载字体文件，可能是文件格式不正确或已损坏")
        else:
            font = TTFont(input_path)
            logging.debug("字体文件加载成功")
        
        # 保存原始字体名称信息
        original_names = {}
        if 'name' in font:
            for record in font['name'].names:
                original_names[record.nameID] = record
        
        # 根据选项构建字符集
        chars = get_chars_by_options(options or {})
        if not chars:
            raise Exception("请至少选择一个字符集选项（如英文字母、数字、标点符号等）")
        logging.debug(f"字符集构建成功，包含 {len(chars)} 个字符")
        
        # 设置 subsetter 选项
        subsetter_options = Options()
        
        # 完全禁用所有布局特性
        subsetter_options.layout_features = []
        subsetter_options.layout_features_exclude = ['*']  # 禁用所有特性
        
        # 禁用不必要的表，但保留 macOS 识别字体所需的关键表
        # 注意：kern 表对 macOS 识别字体很重要，不能移除
        subsetter_options.drop_tables = [
            'GPOS',  # 禁用高级定位
            'GSUB',  # 禁用字形替换（但保留基本字形）
            'morx',  # 禁用扩展变形
            'feat',  # 禁用布局特性
            'lcar',  # 禁用连字调整
            'gvar',  # 禁用字形变化
            'cvar',  # 禁用CVT变化
            'JSTF',  # 禁用对齐
            'MATH',  # 禁用数学排版
            'COLR',  # 禁用颜色
            'CPAL',  # 禁用调色板
            'sbix',  # 禁用位图
            'STAT',  # 禁用样式属性
        ]
        # 不删除 kern 表，macOS 可能需要它来识别字体
        
        # 保留 macOS 识别字体所需的关键名称记录
        # name ID 1: 字体族名, 2: 子族名, 4: 完整字体名, 6: PostScript 名称
        subsetter_options.name_IDs = ['1', '2', '4', '6']  # 保留 macOS 需要的名称记录
        # 保留更多语言，确保 macOS 能识别
        subsetter_options.name_languages = ['*']  # 保留所有语言记录，确保兼容性
        subsetter_options.notdef_glyph = True  # 保留 .notdef 字形
        subsetter_options.notdef_outline = True  # 保留 .notdef 轮廓
        subsetter_options.recommended_glyphs = False  # 禁用推荐字形
        subsetter_options.hinting = True  # 保留 hinting，macOS 可能需要
        subsetter_options.legacy_kern = True  # 保留传统字距调整，macOS 可能需要
        subsetter_options.ignore_missing_glyphs = True
        subsetter_options.ignore_missing_unicodes = True
        subsetter_options.retain_gids = False  # 不保留原始字形ID
        subsetter_options.desubroutinize = True  # 优化字形轮廓
        subsetter_options.no_subset_tables += ['prep', 'gasp', 'DSIG']  # 不处理这些表
        
        logging.debug(f"Subsetter 选项设置完成: {vars(subsetter_options)}")
        
        # 处理字体
        subsetter = Subsetter(options=subsetter_options)
        logging.debug("开始填充字符集")
        try:
            # 验证字符集
            if not isinstance(chars, set) or not chars:
                raise ValueError("字符集配置错误，请重新选择字符集选项")
            
            # 转换字符到 Unicode 码点
            unicodes = set()  # 使用集合去重
            for char in chars:
                try:
                    if isinstance(char, str):
                        # 确保字符是 UTF-8 编码
                        char_encoded = char.encode('utf-8').decode('utf-8')
                        unicode_value = ord(char_encoded)
                        unicodes.add(unicode_value)
                    else:
                        logging.warning(f"跳过无效字符: {char}")
                except (TypeError, ValueError, UnicodeError) as e:
                    logging.error(f"无法转换字符 '{char}' 到 Unicode: {str(e)}")
                    continue
            
            if not unicodes:
                raise ValueError("未找到有效的字符，请检查字符集选项设置")
            
            # 转换回列表并排序，确保稳定的处理顺序
            unicodes = sorted(list(unicodes))
            logging.debug(f"Unicode 码点列表（前10个）: {[hex(u) for u in unicodes[:10]]}...")
            
            subsetter.populate(unicodes=unicodes)
            logging.debug("字符集填充成功")
        except Exception as e:
            logging.error(f"填充字符集时出错: {str(e)}")
            error_msg = str(e)
            if "字符集" in error_msg or "字符" in error_msg:
                raise ValueError(error_msg)
            else:
                raise ValueError(f"字符集处理失败：{error_msg}")
        
        try:
            logging.debug("开始子集化处理")
            subsetter.subset(font)
            logging.debug("子集化处理成功")
        except Exception as e:
            logging.error(f"子集化处理出错: {str(e)}")
            error_msg = str(e)
            if "字体" in error_msg or "glyph" in error_msg.lower() or "unicode" in error_msg.lower():
                # 保持原有消息，但确保是中文
                if any('\u4e00' <= char <= '\u9fff' for char in error_msg):
                    raise ValueError(error_msg)
                else:
                    raise ValueError(f"字体裁剪处理失败：可能是字体文件格式不支持或已损坏")
            else:
                raise ValueError(f"字体裁剪处理失败：{error_msg}")
        
        # 恢复原始字体名称信息，确保 macOS 能识别
        if 'name' in font and original_names:
            restored = 0
            # 优先恢复关键的名称记录（macOS 需要的）
            critical_name_ids = [1, 2, 4, 6]  # 字体族名、子族名、完整名称、PostScript名称
            for nameID in critical_name_ids:
                if nameID in original_names:
                    try:
                        record = original_names[nameID]
                        font['name'].setName(str(record), record.nameID, record.platformID,
                                             record.platEncID, record.langID)
                        restored += 1
                    except Exception as e:
                        logging.warning(f"跳过无法恢复的关键名称记录 {nameID}: {e}")
            
            # 然后恢复其他名称记录
            for nameID, record in original_names.items():
                if nameID not in critical_name_ids:
                    try:
                        font['name'].setName(str(record), record.nameID, record.platformID,
                                             record.platEncID, record.langID)
                        restored += 1
                    except Exception as e:
                        logging.warning(f"跳过无法恢复的名称记录 {record}: {e}")
            logging.debug(f"成功恢复 {restored} 条名称记录")
        
        # 使用临时文件保存输出，保持原始扩展名
        logging.debug("开始保存处理后的字体")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as output_temp:
                output_path = output_temp.name
                font.save(output_path)
                logging.debug(f"字体保存成功: {output_path}")
        except Exception as e:
            logging.error(f"保存字体文件时出错: {str(e)}")
            raise ValueError("无法保存处理后的字体文件，请重试")
        
        # 计算文件大小
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        reduction = ((original_size - new_size) / original_size * 100)
        logging.debug(f"文件大小: 原始={original_size:.1f}KB, 处理后={new_size:.1f}KB, 减少={reduction:.1f}%")
        
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
        logging.error(f"错误类型: {type(e)}")
        import traceback
        logging.error(f"错误堆栈: {traceback.format_exc()}")
        
        # 如果错误消息已经是友好的中文，直接抛出
        error_msg = str(e)
        if any('\u4e00' <= char <= '\u9fff' for char in error_msg):
            raise Exception(error_msg)
        else:
            # 根据错误类型提供友好的中文提示
            error_lower = error_msg.lower()
            if "not a font collection" in error_lower:
                raise Exception("该文件不是有效的字体集合格式")
            elif "font" in error_lower and ("invalid" in error_lower or "corrupt" in error_lower):
                raise Exception("字体文件格式不正确或已损坏，请检查文件是否完整")
            elif "permission" in error_lower or "access" in error_lower:
                raise Exception("无法访问字体文件，请检查文件权限")
            else:
                raise Exception(f"处理字体文件时出错：{error_msg}") 