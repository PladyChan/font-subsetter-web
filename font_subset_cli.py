from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string
import os
import sys

def process_font(input_file, output_dir):
    """处理字体文件"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件路径
        output_file = os.path.join(output_dir, "subset_" + os.path.basename(input_file))
        print(f"\n处理: {input_file} -> {output_file}")
        
        font = TTFont(input_file)
        
        # 基本字符集
        chars = set(string.ascii_letters + string.digits + string.punctuation + '°')
        
        options = Options()
        # 禁用所有OpenType特性
        options.layout_features = []  # 禁用所有特性包括分数
        options.no_subset_tables += ['GSUB']  # 移除字形替换表
        
        subsetter = Subsetter(options=options)
        subsetter.populate(unicodes=[ord(char) for char in chars])
        subsetter.subset(font)
        
        # 修改字体名称
        for name in font['name'].names:
            if name.nameID in (1, 3, 4, 6):
                name.string = name.toUnicode() + "_subset"
        
        font.save(output_file)
        print("✓ 完成")
        return True
        
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False

# 创建输出目录
output_dir = os.path.join(os.getcwd(), "output")

# 获取目录中的所有ttf文件并处理
ttf_files = [f for f in os.listdir('.') if f.endswith('.ttf')]
if ttf_files:
    print(f"找到 {len(ttf_files)} 个字体文件")
    print(f"输出目录: {output_dir}")
    
    success_count = 0
    for ttf in ttf_files:
        if process_font(ttf, output_dir):
            success_count += 1
    
    print(f"\n处理完成！成功处理 {success_count}/{len(ttf_files)} 个文件")
else:
    print("没有找到TTF文件") 