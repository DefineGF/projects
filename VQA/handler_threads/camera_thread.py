import threading
import cv2
from PIL import ImageTk, Image
from tkinter import messagebox
from queue import Queue
from bean.queue_item import QueueItem
from config_item import *
from random import randint
import utils

# PAUSE_SIGN = QueueItem(QueueItem.PAUSE_SIGN_INDEX, None)
# STOP_SIGN = QueueItem(QueueItem.STOP_SIGN_INDEX, None)

class CameraThread(threading.Thread):
    def __init__(self, APP):
        super(CameraThread, self).__init__()
        print("CameraThread -->     init()")
        self.APP = APP
        self.frame_queue = Queue()
        self.save_file_name = "./output/" + utils.generate_file_name_by_time(".mp4")
        self.out = cv2.VideoWriter(self.save_file_name,
                                   cv2.VideoWriter_fourcc('m', 'p', '4', 'v'),  # 设置格式
                                   self.APP.Camera_Frame_Rate, # 写入文件帧率
                                   (APP.label_width, APP.label_height))

        self.state_running = threading.Event()
        self.state_no_pause = threading.Event() # false : 暂停

        self.state_running.clear() # 未启动

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(3, self.APP.label_width)
        self.cap.set(4, self.APP.label_height) # set 只能保证 frame 参数，get无效

        self.APP.Video_Info.set_frame_rate(self.APP.Camera_Frame_Rate)
        self.APP.Video_Info.set_frame_width(self.APP.label_width)
        self.APP.Video_Info.set_frame_height(self.APP.label_height)
        self.APP.Video_Info.set_frame_channel(3) # 默认设置3

        if self.cap.isOpened():
            self.ret, self.frame = self.cap.read()
            if self.ret:
                self.APP.Video_Info.set_frame_channel(self.frame.shape[2])  # 设置通道数
            print("camera thread --> 视频格式设置成功！")

        self.APP.app_refresh_video_info() # 刷新视频信息


    def run(self):
        print("CameraThread -->     run()")
        self.state_running.set()  # 设置状态为 运行
        self.state_no_pause.set() # 设置状态 未暂停
        if not self.cap.isOpened():
            messagebox.showerror(title="错误:", message="视频打开失败")
            # self.cap.release() 这里会有bug
            return

        ret, frame = self.ret, self.frame  # 一帧也不丢哦

        # 设置几个用来 随机间隔提取帧 的参数
        next_put_index = randint(0, self.APP.Evaluate_Frame_Count) # 下次需上传下标
        tail_out_index = next_put_index + self.APP.Evaluate_Frame_Count
        cur_frame_index = 0 # 当前帧下标

        while True:
            self.APP.app_refresh_cur_frame_count(cur_frame_index)
            if not self.state_no_pause.isSet(): # 暂停信号
                self.frame_queue.put(QueueItem(cur_frame_index, QueueItem.PAUSE_SIGN_INDEX))

            self.state_no_pause.wait() # for pause

            if not self.state_running.isSet(): # for stop
                self.frame_queue.put(QueueItem(cur_frame_index, QueueItem.STOP_SIGN_INDEX)) # 终止信号
                self.APP.Video_Info.set_frame_count(cur_frame_index + 1)
                self.APP.app_refresh_video_info() # 确定帧数之后再次刷新视频信息
                self.cap.release()
                self.out.release()
                break

            # 核心工作区
            if ret:
                frame = cv2.flip(frame, 1)  # 左右翻转 (cv2 显示视频为左右翻转,故为之)
                frame = cv2.resize(frame, (self.APP.label_width, self.APP.label_height))
                # 将 frame 转换为 tkinter 可以显示的格式
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.out.write(cv2image)
                img = Image.fromarray(cv2image)

                '''
                    分段检测需要随机提取帧放入队列
                    整段检测只需全部放入队列即可
                '''
                if self.APP.EVALUATE_METHOD == Method.MULTI_METHOD: # 分段检测
                    if cur_frame_index == tail_out_index:
                        last_put_index = tail_out_index # 上次发送帧下标
                        rand_count = randint(0, self.APP.Evaluate_Frame_Count)
                        next_put_index = last_put_index + rand_count
                        tail_out_index = next_put_index + self.APP.Evaluate_Frame_Count
                        print("camera_thread --> get rand_count = ", rand_count)

                    if next_put_index <= cur_frame_index < tail_out_index:
                        self.frame_queue.put(QueueItem(cur_frame_index, img))
                        print("camera thread --> put frame")

                elif self.APP.EVALUATE_METHOD == Method.SINGLE_METHOD: # 整段检测
                    self.frame_queue.put(QueueItem(cur_frame_index, img))

                img_tk = ImageTk.PhotoImage(image=img)
                self.APP.refresh_main_label(photo=img_tk)
                # 这步可不能忘了
                ret, frame = self.cap.read()
                cur_frame_index += 1
            else:
                break

    def pause(self):
        self.state_no_pause.clear()

    def resume(self):
        self.state_no_pause.set()

    def stop(self):
        self.state_running.clear()
        self.state_no_pause.set() # 这一步很重要
        return self.save_file_name
