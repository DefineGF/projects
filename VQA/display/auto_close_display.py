import tkinter as tk
from tkinter import ttk
import threading
import time

class AutoCloseDisplay:
    def __init__(self):
        self.window = tk.Toplevel()
        winWidth, winHeight = 600, 150  # 设置窗口大小
        # 获取屏幕分辨率
        screenWidth = self.window.winfo_screenwidth()
        screenHeight = self.window.winfo_screenheight()
        x = int((screenWidth - winWidth) / 2)
        y = int((screenHeight - winHeight) / 2)
        self.window.title("评估结果显示：")
        self.window.geometry("%sx%s+%s+%s" % (winWidth, winHeight, x, y))  # 设置窗口初始位置在屏幕居中
        self.window.resizable(0, 0)  # 设置窗口宽高固定

        self.label_str = tk.StringVar()
        tk.Label(self.window, textvariable=self.label_str).pack(pady=10)

    def time_task(self):
        time.sleep(2)
        self.window.destroy()

class ProgressbarDisplay(AutoCloseDisplay):
    def __init__(self):
        super().__init__()

    def display(self):
        self.label_str.set("评估中，请稍等~")
        self.pb = ttk.Progressbar(self.window, length=400, value=0, mode="indeterminate")
        self.pb.pack(pady=10)
        self.pb.start()
        threading.Thread(target=lambda: self.time_task()).start()
        self.window.mainloop()

