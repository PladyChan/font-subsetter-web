import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string

class FontSubsetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字体精简工具")
        
        # 设置窗口大小和位置
        window_width = 600
        window_height = 500
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 创建主框架
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建按钮框架
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 选择文件按钮
        self.select_button = ttk.Button(button_frame, text="选择字体文件(可多选)", command=self.select_files)
        self.select_button.pack(side=tk.LEFT, padx=5)
        
        # 选择目录按钮
        self.select_dir_button = ttk.Button(button_frame, text="选择文件夹", command=self.select_directory)
        self.select_dir_button.pack(side=tk.LEFT, padx=5)
        
        # 显示选中文件的列表框
        self.file_list = tk.Listbox(self.main_frame, height=10, width=70)
        self.file_list.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        # 进度显示文本框
        self.log_text = tk.Text(self.main_frame, height=10, width=70)
        self.log_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # 开始处理按钮
        self.process_button = ttk.Button(self.main_frame, text="开始处理", command=self.process_fonts)
        self.process_button.pack(pady=10)
        self.process_button.config(state=tk.DISABLED)
        
        self.input_files = []
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("TTF files", "*.ttf"), ("All files", "*.*")]
        )
        if files:
            self.input_files = list(files)
            self.update_file_list()
            
    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.input_files = [
                os.path.join(directory, f) for f in os.listdir(directory)
                if f.lower().endswith('.ttf')
            ]
            self.update_file_list()
            
    def update_file_list(self):
        self.file_list.delete(0, tk.END)
        if self.input_files:
            for file in self.input_files:
                self.file_list.insert(tk.END, os.path.basename(file))
            self.process_button.config(state=tk.NORMAL)
            self.log(f"已选择 {len(self.input_files)} 个字体文件")
        else:
            self.process_button.config(state=tk.DISABLED)
            self.log("没有找到TTF文件")
            
    def process_single_font(self, input_file, output_dir):
        try:
            output_file = os.path.join(output_dir, "subset_" + os.path.basename(input_file))
            self.log(f"\n处理: {os.path.basename(input_file)}")
            
            font = TTFont(input_file)
            chars = set(string.ascii_letters + string.digits + string.punctuation + '°')
            
            options = Options()
            options.layout_features = []
            options.no_subset_tables += ['GSUB']
            
            subsetter = Subsetter(options=options)
            subsetter.populate(unicodes=[ord(char) for char in chars])
            subsetter.subset(font)
            
            for name in font['name'].names:
                if name.nameID in (1, 3, 4, 6):
                    name.string = name.toUnicode() + "_subset"
            
            font.save(output_file)
            
            original_size = os.path.getsize(input_file) / 1024 / 1024
            new_size = os.path.getsize(output_file) / 1024 / 1024
            
            self.log(f"✓ 完成")
            self.log(f"  原始大小: {original_size:.2f}MB")
            self.log(f"  新大小: {new_size:.2f}MB")
            self.log(f"  减小了: {((original_size - new_size) / original_size * 100):.2f}%")
            return True
            
        except Exception as e:
            self.log(f"✗ 错误: {str(e)}")
            return False
            
    def process_fonts(self):
        if not self.input_files:
            messagebox.showerror("错误", "请先选择字体文件！")
            return
            
        # 创建输出目录
        first_file = self.input_files[0]
        output_dir = os.path.join(os.path.dirname(first_file), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        self.log(f"输出目录: {output_dir}")
        
        success_count = 0
        total = len(self.input_files)
        
        # 禁用按钮，防止重复处理
        self.select_button.config(state=tk.DISABLED)
        self.select_dir_button.config(state=tk.DISABLED)
        self.process_button.config(state=tk.DISABLED)
        
        try:
            for i, input_file in enumerate(self.input_files, 1):
                self.log(f"\n[{i}/{total}] 处理文件...")
                if self.process_single_font(input_file, output_dir):
                    success_count += 1
                    
            self.log(f"\n处理完成！成功处理 {success_count}/{total} 个文件")
            messagebox.showinfo("完成", f"成功处理 {success_count}/{total} 个文件")
        finally:
            # 重新启用按钮
            self.select_button.config(state=tk.NORMAL)
            self.select_dir_button.config(state=tk.NORMAL)
            self.process_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = FontSubsetApp(root)
    root.mainloop() 