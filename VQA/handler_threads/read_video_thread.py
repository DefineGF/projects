import threading
import cv2
from PIL import ImageTk, Image
from tkinter import messagebox
import utils

'''
    设置 APP 视频信息： 读取线程使用OpenCV， 用于获取视频帧率
'''
class ReadVideoThread(threading.Thread):
    def __init__(self, APP, video_path = None):
        super(ReadVideoThread, self).__init__()
        self.APP = APP
        self.read_file_path = video_path

        self.state_running, self.state_no_pause = threading.Event(), threading.Event()
        self.state_running.clear()
        self.state_no_pause.set()

    def run(self):
        self.state_running.set()
        self.cap = cv2.VideoCapture(self.read_file_path)
        if not self.cap.isOpened():
            messagebox.showerror(title="错误:", message="视频打开失败")
            self.cap.release()

        cur_frame_index = 0
        while True:
            self.state_no_pause.wait() # for pause
            if not self.state_running.isSet(): # for stop
                self.cap.release()
                break
            # 核心工作区
            ret, frame = self.cap.read()
            if ret:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                img = utils.img_resize(self.APP.label_width, self.APP.label_height, img)
                img_tk = ImageTk.PhotoImage(image=img)
                self.APP.refresh_main_label(photo=img_tk)
                self.APP.app_refresh_cur_frame_count(cur_frame_index)
                cur_frame_index += 1

            else: # 主动结束： 读取完毕
                self.state_running.clear()
                self.cap.release()
                messagebox.showinfo("读取视频", "视频读取完毕！")
                self.APP.app_refresh()
                break

    def pause(self):
        self.state_no_pause.clear()

    def resume(self):
        self.state_no_pause.set()

    def stop(self): # 被动结束
        self.state_running.clear()
        self.state_no_pause.set()
        self.APP.app_refresh()
