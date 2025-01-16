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
    if options.get('chinese_common', False):
        # 常用汉字集（3500字）
        common_chars = (
            '的一是了我不人在他有这个上们来到时大地为子中你说生国年着就那和要她出也得里后自以会家可下而过天去能对小多然于心学'
            '么之都好看起发当没成只如事把还用第样道想作种开美总从无情己面最女但现前些所同日手又行意动方期它头经长儿回位分爱老'
            '因很给名法间斯知世什两次使身者被高已亲其进此话常与活正感见明问力理尔点文几定本公特做外孩相西果走将月十实向声车全'
            '信重三机工物气每并别真打太新比才便夫再书部水像眼等体却加电主界门利海受听表德少克代员许稜先口由死安写性马光白或住'
            '难望教命花结乐色更拉东神记处让母父应直字场平报友关放至张认接告入笑内英军候民岁往何度山觉路带万男边风解叫任金快原'
            '吃妈变通师立象数四失满战远格士音轻目条呢病始达深完今提求清王化空业思切怎非找片罗钱吗语元喜整荣波表少言某功项近岸'
            '千米型识验史感谱配支谈组别称丽改系温带便速效直必美确传画食源观察铁浪命令商连纪基批群导房离调刚随讲响引示渐强装象'
            '似斗证纸极必居思格造片步状艺设显众争养'
        )
        chars.update(common_chars)
        
    if options.get('chinese_name', False):
        # 人名用字集
        name_chars = '华伟建国志明军平春江红波涛昌鹏飞龙强晓东海峰成荣新刚子杰超艳芳娟秀兰凤英丽娜静敏燕'
        chars.update(name_chars)
    
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
        # 加载字体文件
        logging.debug(f"开始加载字体文件: {input_path}")
        font = TTFont(input_path)
        logging.debug("字体文件加载成功")
        
        # 获取原始文件扩展名
        original_ext = os.path.splitext(input_path)[1].lower()
        
        # 保存原始字体名称信息
        original_names = {}
        if 'name' in font:
            for record in font['name'].names:
                original_names[record.nameID] = record
        
        # 根据选项构建字符集
        chars = get_chars_by_options(options or {})
        if not chars:
            raise Exception("未选择任何字符集")
        logging.debug(f"字符集构建成功，包含 {len(chars)} 个字符")
        
        # 设置 subsetter 选项
        subsetter_options = Options()
        
        # 完全禁用所有布局特性
        subsetter_options.layout_features = []
        subsetter_options.layout_features_exclude = ['*']  # 禁用所有特性
        
        # 禁用所有可能的表
        subsetter_options.drop_tables = [
            'GPOS',  # 禁用高级定位
            'GSUB',  # 禁用字形替换
            'kern',  # 禁用字距调整
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
        
        # 最小化选项
        subsetter_options.name_IDs = ['1', '2']  # 只保留基本名称记录
        subsetter_options.name_languages = ['0x0409']  # 只保留英文
        subsetter_options.notdef_glyph = False  # 不保留 .notdef 字形
        subsetter_options.notdef_outline = False  # 不保留 .notdef 轮廓
        subsetter_options.recommended_glyphs = False  # 禁用推荐字形
        subsetter_options.hinting = False  # 禁用 hinting
        subsetter_options.legacy_kern = False  # 禁用传统字距调整
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
                raise ValueError("字符集无效或为空")
            
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
                raise ValueError("没有有效的 Unicode 字符")
            
            # 转换回列表并排序，确保稳定的处理顺序
            unicodes = sorted(list(unicodes))
            logging.debug(f"Unicode 码点列表（前10个）: {[hex(u) for u in unicodes[:10]]}...")
            
            subsetter.populate(unicodes=unicodes)
            logging.debug("字符集填充成功")
        except Exception as e:
            logging.error(f"填充字符集时出错: {str(e)}")
            raise ValueError(f"字符集处理失败: {str(e)}")
        
        try:
            logging.debug("开始子集化处理")
            subsetter.subset(font)
            logging.debug("子集化处理成功")
        except Exception as e:
            logging.error(f"子集化处理出错: {str(e)}")
            raise ValueError(f"字体处理失败: {str(e)}")
        
        # 恢复原始字体名称信息
        if 'name' in font and original_names:
            try:
                for nameID, record in original_names.items():
                    font['name'].setName(str(record), record.nameID, record.platformID, 
                                       record.platEncID, record.langID)
                logging.debug("成功恢复字体名称信息")
            except Exception as e:
                logging.error(f"恢复字体名称时出错: {str(e)}")
        
        # 使用临时文件保存输出，保持原始扩展名
        logging.debug("开始保存处理后的字体")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as output_temp:
                output_path = output_temp.name
                font.save(output_path)
                logging.debug(f"字体保存成功: {output_path}")
        except Exception as e:
            logging.error(f"保存字体文件时出错: {str(e)}")
            raise ValueError(f"无法保存处理后的字体: {str(e)}")
        
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
        raise Exception(f"处理字体文件时出错: {str(e)}") 