from tkinter import *
from tkinter import messagebox
import tkinter.filedialog as FD
import os
import shutil
import torch
from config_item import *
import threading
from handler_threads import camera_thread, read_video_thread
from handler_threads import camera_evaluate_thread, video_evaluate_thread_2
from display.auto_close_display import ProgressbarDisplay
from bean.video_info import VideoInfo
from bean.record_list import RecordList
from display.multi_eval_display import *
from display.input_window import InputWindow
from utils import *

win_width, win_height = 800, 720


class APP:
    WORK_MODE = Mode.DEFAULT_MODE  # 设置保护模式
    WORK_STATE = State.UN_START_STATE  # 显示图像线程状态
    EVAL_STATE = State.UN_START_STATE  # 评估线程状态
    EVALUATE_METHOD = Method.MULTI_METHOD  # 默认分段评估
    EVAL_END_SIGN = threading.Event()  # 评估线程终止标志
    EVAL_END_SIGN.clear()

    Evaluate_Frame_Count = 32  # 分段评估 每次评估帧数量
    Get_Feature_Batch_Size = 8  # 特征提取 batch_size
    Camera_Frame_Rate = 30  # fps
    result_records = []  # 保存评估结果

    Device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    Model_Path = "models/VSFA.pt"

    label_width, label_height = 640, 640
    video_thread = None

    def __init__(self):
        self.open_file_path, self.save_file_path = None, None
        self.Video_Info = VideoInfo()
        self.window = Tk()
        self.window.geometry("%sx%s+100+10" % (win_width, win_height))
        self.window.title("默认模式")
        self.window.protocol("WM_DELETE_WINDOW", self.window.iconify)

        # 几个组件初始化
        self.init_menu()
        self.init_bottom_frame()
        self.init_right_frame()
        self.init_main_frame()

        self.window.mainloop()

    def init_menu(self):
        main_menu = Menu(self.window)
        mode_menu = Menu(main_menu, tearoff=0)
        config_menu = Menu(main_menu, tearoff=0)

        # 设置 模式 目录
        mode_menu.add_command(label="文件模式",
                              command=lambda: self.set_mode(Mode.INSERT_FILE_MODE))
        mode_menu.add_command(label="拍摄模式",
                              command=lambda: self.set_mode(Mode.CAMERA_MODE))
        mode_menu.add_separator()  # 添加分割线
        mode_menu.add_command(label="Quit", command=self.my_quit)

        # 设置 配置 目录
        config_fps_menu = Menu(config_menu, tearoff=0)
        config_fps_menu.add_command(label="15", command=lambda: self.set_fps(15))
        config_fps_menu.add_command(label="20", command=lambda: self.set_fps(20))
        config_fps_menu.add_command(label="30", command=lambda: self.set_fps(30))
        config_fps_menu.add_command(label="45", command=lambda: self.set_fps(45))
        config_fps_menu.add_command(label="60", command=lambda: self.set_fps(60))
        config_menu.add_cascade(label="视频保存帧率", menu=config_fps_menu)
        config_menu.add_separator()

        config_eval_frames_menu = Menu(config_menu, tearoff=0)
        config_eval_frames_menu.add_command(label="8", command=lambda: self.set_eval_frame_count(8))
        config_eval_frames_menu.add_command(label="16", command=lambda: self.set_eval_frame_count(16))
        config_eval_frames_menu.add_command(label="32", command=lambda: self.set_eval_frame_count(32))
        config_eval_frames_menu.add_command(label="64", command=lambda: self.set_eval_frame_count(64))
        config_menu.add_cascade(label="评估帧间隔", menu=config_eval_frames_menu)

        main_menu.add_cascade(label="model", menu=mode_menu)
        main_menu.add_cascade(label="config", menu=config_menu)
        self.window.config(menu=main_menu)

    def init_bottom_frame(self):
        bottom_frame = LabelFrame(self.window, height=30)
        bottom_frame.pack(side=BOTTOM, fill=X)

        self.string_cur_frame_count = StringVar(value="0")

        # 三个单选按钮
        self.string_radio_btn = StringVar(value="1")  # 默认分段评估
        self.radio_select_before = StringVar(value="1")  # 用来记录当前选中，用于回滚

        Radiobutton(bottom_frame, text="分段评估",  # 分段评估
                    value=1,
                    variable=self.string_radio_btn,
                    command=lambda:
                    self.radio_btn_select(self.radio_select_before, self.string_radio_btn)).place(relx=0.03)

        Radiobutton(bottom_frame, text="整体评估",  # 整体评估
                    value=2,
                    variable=self.string_radio_btn,
                    command=lambda:
                    self.radio_btn_select(self.radio_select_before, self.string_radio_btn)).place(relx=0.15)

        Radiobutton(bottom_frame, text="指定评估",
                    value=3,
                    variable=self.string_radio_btn,
                    command=lambda:
                    self.radio_btn_select(self.radio_select_before, self.string_radio_btn)).place(relx=0.27)

        Label(bottom_frame, textvariable=self.string_cur_frame_count).place(relx=0.42)

        # 启动 & 暂停 按钮
        self.string_start_stop = StringVar(value="start")
        self.string_pause_resume = StringVar(value="pause")
        self.btn_start_stop = Button(bottom_frame, width=10,
                                     textvariable=self.string_start_stop,
                                     command=self.ui_start_stop)

        self.btn_pause_resume = Button(bottom_frame, width=10,
                                       textvariable=self.string_pause_resume,
                                       command=self.ui_pause_resume)

        self.btn_start_stop.place(relx=0.55)
        self.btn_pause_resume.place(relx=0.7)

        # 显示结果按钮
        self.btn_display_result = Button(bottom_frame, text=">>", command=self.evaluate_display)
        self.btn_display_result.place(relx=0.9)

    def init_right_frame(self):
        self.string_video_info = StringVar()
        self.string_eval_info = StringVar()

        left_frame = LabelFrame(self.window, width=20)
        left_frame.pack(side=RIGHT, fill=Y)
        top_frame = LabelFrame(left_frame, width=10)
        top_frame.pack(side=TOP)
        bottom_frame = LabelFrame(left_frame)
        bottom_frame.pack(side=BOTTOM, pady=10)

        Label(top_frame, text="视频信息").pack(side=TOP, fill=X)
        self.video_info_label = Label(top_frame,
                                      width=20, height=15,
                                      justify=LEFT,
                                      textvariable=self.string_video_info,
                                      background="yellow")
        self.video_info_label.pack(fill=X)

        Label(bottom_frame, text="评估信息").pack(side=TOP, fill=X)
        self.eval_info_label = Label(bottom_frame,
                                     width=20, height=20,
                                     justify=LEFT,
                                     textvariable=self.string_eval_info,
                                     background="yellow")
        self.eval_info_label.pack(fill=X)

    # ---------------------------------工作 & 评估 模式选择--------------------------------------
    def set_mode(self, mode):
        if self.WORK_STATE == State.UN_START_STATE or self.WORK_STATE == State.FINISHED_STATE:
            self.WORK_MODE = mode
            self.Video_Info.clear()  # 更换文件 或者 模式 清空Video_Info 信息
            self.WORK_STATE = State.UN_START_STATE

            if mode == Mode.CAMERA_MODE:
                self.window.title("当前工作模式: 拍摄模式")

            elif mode == Mode.INSERT_FILE_MODE:
                self.window.title("当前工作模式: 文件模式")
                self.open_file_path = FD.askopenfilename()
                print("加载文件信息~")
                self.Video_Info.set_file_path(self.open_file_path)
                print("加载完毕")
                if self.Video_Info.is_inited:
                    self.app_refresh_video_info()
        else:
            messagebox.showwarning("警告!", message="请等待当前执行完毕！")

    def radio_btn_select(self, before, current):
        # 未启动 或者 评估结束时候才可以修改评估模式
        can_set = self.WORK_STATE == State.UN_START_STATE or self.WORK_STATE == State.FINISHED_STATE
        can_set = can_set and (self.EVAL_STATE == State.UN_START_STATE or self.EVAL_STATE == State.FINISHED_STATE)
        if not can_set:
            print("state = " + str(self.WORK_STATE == State.UN_START_STATE))
            messagebox.showerror("错误提醒:", "当前不能修改评估模式哦~")
            current.set(before.get())
            return

        self.EVAL_STATE = State.UN_START_STATE
        if self.string_radio_btn.get() == '1':
            self.EVALUATE_METHOD = Method.MULTI_METHOD
            before.set(current.get())
            print("设置为: 分段评估")
        elif self.string_radio_btn.get() == '2':
            self.EVALUATE_METHOD = Method.SINGLE_METHOD
            before.set(current.get())
            print("设置成: 整段评估")
        else:
            if self.WORK_MODE != Mode.INSERT_FILE_MODE:
                messagebox.showerror("操作错误： ", "当前评估方式只能工作在读取文件模式中~")
                current.set(before.get())
            else:
                if is_video_file(self.open_file_path):
                    self.EVALUATE_METHOD = Method.SPECIFIED_METHOD
                    input_window = InputWindow(self.Video_Info.frame_count)
                    self.specified_frame_from, self.specified_frame_to = input_window.start()
                    if input_window.is_input_available():
                        before.set(current.get())
                        print("设置成: 指定评估模式~ from = " + self.specified_frame_from + " to = " + self.specified_frame_to)
                    else:  # 不排除直接关掉输入框的可能
                        current.set(before.get())
                else:
                    current.set(before.get())
                    self.open_file_path = FD.askopenfilename()

    # -----------------------------界面动态修改--------------------------------------------------
    def init_main_frame(self):
        main_frame = Frame(self.window)
        main_frame.pack(side=TOP, expand=TRUE, fill=BOTH)
        self.label_main = Label(main_frame)
        self.label_main.place(width=self.label_width, height=self.label_height, y=25)

    def refresh_main_label(self, photo):
        self.label_main.config(image=photo)
        self.label_main.image = photo

    def app_refresh(self):
        self.string_start_stop.set("start")
        self.string_pause_resume.set("pause")
        self.WORK_STATE = State.FINISHED_STATE

    def app_refresh_cur_frame_count(self, index):
        self.string_cur_frame_count.set(str(index))

    def app_refresh_video_info(self):
        self.string_video_info.set(self.Video_Info.get_info_string())

    def app_refresh_eval_info(self):
        self.string_eval_info.set(RecordList(self.result_records).get_records_info())

    def evaluate_display(self):
        if self.EVALUATE_METHOD == Method.MULTI_METHOD:  # "分段评估"
            if self.WORK_STATE == State.UN_START_STATE:
                messagebox.showwarning("警告:", "还未启动, 请点击 start 启动！")
            elif self.EVAL_STATE == State.RUNNING_STATE:
                ProgressbarDisplay().display()
            elif self.EVAL_STATE == State.FINISHED_STATE:
                multi_eval_show(self)

        else:  # "整体评估"
            if self.EVAL_END_SIGN.isSet():  # 评估完成
                if self.result_records:
                    item = self.result_records[0]
                    print_string = "视频评估质量为： " + str(item.ans)
                    messagebox.showinfo("整段评估结果:", message=print_string)
            else:
                ProgressbarDisplay().display()

    # -----------------------------菜单栏配置-------------------------------------------
    def set_fps(self, fps):
        print("设置拍摄视频保存帧率为：", fps)
        self.Camera_Frame_Rate = fps

    def set_eval_frame_count(self, count):
        print("设置评估帧间隔为: ", count)
        self.Evaluate_Frame_Count = count

    def my_quit(self):
        self.result_records.clear()
        self.window.quit()
        self.window.destroy()
        print("退出主界面！")

    '''
        启动线程前做一些初始化的工作
    '''

    def init_start(self):
        self.string_start_stop.set("stop")  # 设置按钮更改
        self.EVAL_END_SIGN.clear()  # 设置为完成
        self.result_records.clear()  # 清空之前的评估结果
        self.WORK_STATE = State.RUNNING_STATE  # 设置运行状态为运行时
        self.EVAL_STATE = State.RUNNING_STATE  # 设置评估状态为运行时
        self.string_eval_info.set("")  # 清空之前的评估结果

    """
        ui_start_stop & ui_pause_resume 进行必要的逻辑判断，然后调用相应的函数
        my_start(), my_pause(), my_resume(), my_stop() 只完成核心功能 :)
    """

    def ui_start_stop(self):  # start or stop
        if self.WORK_STATE == State.UN_START_STATE \
                or self.EVAL_END_SIGN.isSet():  # 未开始显示 或者 评估结束方能启动线程
            print("开始：")

            if self.WORK_MODE == Mode.CAMERA_MODE:  # 拍摄模式
                self.video_thread = camera_thread.CameraThread(self)
                # 设置评估线程
                if self.EVALUATE_METHOD == Method.MULTI_METHOD:  # 分段评估
                    self.evaluate_thread = camera_evaluate_thread.CameraMultiEval(self, self.video_thread.frame_queue)

                elif self.EVALUATE_METHOD == Method.SINGLE_METHOD:  # 整段评估
                    print("设置整段评估!")
                    self.evaluate_thread = camera_evaluate_thread.CameraSingleEval(self, self.video_thread.frame_queue)

                print("eval = ", self.EVALUATE_METHOD, " work_model = ", self.WORK_MODE)

                self.init_start()
                self.video_thread.setDaemon(True)
                self.evaluate_thread.setDaemon(True)
                self.video_thread.start()
                self.evaluate_thread.start()

            elif self.WORK_MODE == Mode.INSERT_FILE_MODE:  # 读取文件模式
                if is_video_file(self.open_file_path):  # 选择的文件必存在（因为是选择的:)
                    self.video_thread = read_video_thread.ReadVideoThread(self, self.open_file_path)
                    # 设置评估线程
                    if self.EVALUATE_METHOD == Method.MULTI_METHOD:  # 分段评估
                        self.evaluate_thread = video_evaluate_thread_2.VideoMultiEval(self, self.open_file_path)

                    elif self.EVALUATE_METHOD == Method.SINGLE_METHOD:  # 整体评估
                        self.evaluate_thread = \
                            video_evaluate_thread_2.VideoSingleEval(self, self.open_file_path,
                                                                    start_index=0,
                                                                    end_index=self.Video_Info.frame_count)

                    elif self.EVALUATE_METHOD == Method.SPECIFIED_METHOD:  # 指定区间评估
                        self.evaluate_thread = \
                            video_evaluate_thread_2.VideoSingleEval(self, self.open_file_path,
                                                                    start_index=int(self.specified_frame_from) - 1,
                                                                    end_index=int(self.specified_frame_to) - 1,
                                                                    is_specified=True)

                    self.init_start()
                    self.video_thread.setDaemon(True)
                    self.evaluate_thread.setDaemon(True)
                    self.video_thread.start()
                    self.evaluate_thread.start()
                else:
                    print("APP --> 选择视频路径")
                    self.open_file_path = FD.askopenfilename()
            else:
                messagebox.showwarning("警告：", message="请先选择工作模式!")
        elif self.WORK_STATE == State.RUNNING_STATE or self.WORK_STATE == State.PAUSE_STATE:  # 停止键
            print("停止~")
            self.my_stop()

    def ui_pause_resume(self):
        if self.WORK_STATE == State.RUNNING_STATE:
            self.my_pause()
        elif self.WORK_STATE == State.PAUSE_STATE:
            self.my_resume()
        else:
            messagebox.showwarning("警告：", message="未启动~~")

    def my_pause(self):
        self.video_thread.pause()
        self.string_pause_resume.set("resume")
        self.WORK_STATE = State.PAUSE_STATE

    def my_resume(self):
        self.video_thread.resume()
        self.string_pause_resume.set("pause")
        self.WORK_STATE = State.RUNNING_STATE

    def my_stop(self):
        self.app_refresh()
        if self.WORK_MODE == Mode.INSERT_FILE_MODE:
            self.video_thread.stop()

        elif self.WORK_MODE == Mode.CAMERA_MODE:  # 保存拍摄到的视频
            save_video_name = self.video_thread.stop()
            to_move = messagebox.askquestion(message="是否更改保存路径名称？")

            if to_move == 'yes':
                src_file_path = os.getcwd() + "\\" + save_video_name
                dst_file_path = FD.asksaveasfilename()
                while True:
                    if len(dst_file_path) == 0:  # 设置路径的时候选择了 取消
                        break
                    if dst_file_path[-4:] != ".mp4":
                        messagebox.showerror("错误!", message="请以 .mp4 为格式后缀！")
                        dst_file_path = FD.asksaveasfilename()
                    else:
                        break
                if os.path.exists(src_file_path):
                    shutil.move(src_file_path, dst_file_path)
                else:
                    messagebox.showwarning("警告:", message="原文件路径已经更改!")
            else:
                print("保存至根目录！ 文件名：", save_video_name)


if __name__ == "__main__":
    app = APP()
