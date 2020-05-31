from tkinter import *
from tkinter import messagebox

class InputWindow:
    def __init__(self, frame_count):
        self.frame_count = frame_count
        self.frame_start = ""
        self.frame_to = ""

    def start(self):
        self.root = Tk()
        Label(self.root, text= "总帧数为: " + str(self.frame_count)).grid(row=0, sticky=W)
        Label(self.root, text='起始：').grid(row=1, sticky=W)
        Label(self.root, text='终止：').grid(row=2, sticky=W)

        self.e_from = Entry(self.root) # 起始输入框
        self.e_from.grid(row=1, column=1, sticky=E)
        self.e_to = Entry(self.root)   # 终止输入框
        self.e_to.grid(row=2, column=1, sticky=E)

        # 登录按钮
        b_login = Button(self.root, text='提交', command = self.submit)
        b_login.grid(row=3, column=1, sticky=E)
        self.root.mainloop()
        print("退出事件循环!")
        return self.frame_start, self.frame_to

    def submit(self):
        self.frame_start = self.e_from.get()
        self.frame_to = self.e_to.get()
        if self.is_input_available():
            print("from = " + self.frame_start + " to = " + self.frame_to)
            self.root.quit()
            self.root.destroy()
        else:
            messagebox.showerror("错误输入:", "请输入正确区间上的正整数...")

    def is_input_available(self):
        input_available = (self.frame_start.isdigit() and self.frame_to.isdigit()) # 纯数字（负数 & 小数除外)
        if input_available: # 再次检测区间
            input_available = input_available and \
                              (int(self.frame_start) < int(self.frame_to) <= self.frame_count)
        return input_available

if __name__ == "__main__":
    input_window = InputWindow(10)
    input_window.start()
    print("from = " + input_window.frame_start + " to = " + input_window.frame_to)