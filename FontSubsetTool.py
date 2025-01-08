import os
import tkinter as tk
from tkinter import filedialog, messagebox
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string

class SimpleFontTool:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("字体精简工具")
        self.window.geometry("500x600")
        self.window.configure(bg='#F5F6F7')
        
        # 创建主框架
        self.main_frame = tk.Frame(self.window, bg='#F5F6F7')
        self.main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # 拖放区域（使用Label模拟）
        self.drop_area = tk.Label(
            self.main_frame,
            text="拖放字体文件到这里\n或点击选择文件",
            bg='white',
            height=10,
            relief='solid',
            borderwidth=1
        )
        self.drop_area.pack(fill='x', pady=(0, 20))
        self.drop_area.bind('<Button-1>', lambda e: self.select_files())
        
        # 开始处理按钮
        self.process_btn = tk.Button(
            self.main_frame,
            text="开始处理",
            command=self.process_files,
            bg='white',
            relief='flat',
            width=40,
            height=2
        )
        self.process_btn.pack(pady=20)
        
        # 进度显示
        self.progress_label = tk.Label(
            self.main_frame,
            text="",
            font=('PingFang SC', 36),
            fg='#888888',
            bg='#F5F6F7'
        )
        self.progress_label.pack(pady=20)
        
        self.files = []
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择字体文件",
            filetypes=[("TTF files", "*.ttf"), ("OTF files", "*.otf")]
        )
        if files:
            self.files = files
            self.drop_area.config(text=f"已选择 {len(files)} 个文件")
            
    def update_progress(self, percent):
        self.progress_label.config(text=f"{percent:.1f}%")
        self.window.update()
        
    def process_files(self):
        if not self.files:
            messagebox.showerror("错误", "请先选择字体文件")
            return
            
        try:
            total = len(self.files)
            for i, file in enumerate(self.files, 1):
                # 创建输出目录
                output_dir = os.path.join(os.path.dirname(file), "output")
                os.makedirs(output_dir, exist_ok=True)
                
                # 处理字体
                font = TTFont(file)
                chars = set(string.ascii_letters + string.digits + string.punctuation + '°')
                
                options = Options()
                options.layout_features = []
                options.no_subset_tables += ['GSUB']
                
                subsetter = Subsetter(options=options)
                subsetter.populate(unicodes=[ord(char) for char in chars])
                subsetter.subset(font)
                
                # 保存文件
                output_file = os.path.join(output_dir, f"subset_{os.path.basename(file)}")
                font.save(output_file)
                
                # 更新进度
                progress = (i / total) * 100
                self.update_progress(progress)
            
            self.progress_label.config(text="")
            messagebox.showinfo("完成", "所有文件处理成功！\n文件已保存到 output 目录")
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = SimpleFontTool()
    app.run() 