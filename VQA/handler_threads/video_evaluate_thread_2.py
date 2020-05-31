import threading
from tkinter import messagebox
from random import randint
import torch
import skvideo.io
import cv2
from torchvision import transforms
from PIL import Image
from VSFA import VSFA
from CNNfeatures import get_features
from bean.record_item import RecordItem
from config_item import *

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


class VideoEvalThread(threading.Thread):
    def __init__(self, APP, video_path):
        super(VideoEvalThread, self).__init__()
        self.APP = APP
        self.video_path = video_path
        print("VideoEvalThread --> init() 评估线程初始化完成！")

    def run(self):
        super().run()
        print("VideoEvalThread --> run() 评估线程开始执行~")
        self.model = VSFA()
        self.model.load_state_dict(torch.load(self.APP.Model_Path))
        self.model.to(self.APP.Device)
        self.model.eval()

        # self.video_data = skvideo.io.vread(self.video_path)
        self.cap = cv2.VideoCapture(self.video_path)

        self.length = int(self.APP.Video_Info.frame_count)
        self.height = int(self.APP.Video_Info.v_height)
        self.width = int(self.APP.Video_Info.v_width)
        self.channel = int(self.APP.Video_Info.v_channel)

        self.APP.app_refresh_video_info()


class VideoMultiEval(VideoEvalThread):
    def __init__(self, APP, video_path):
        super().__init__(APP, video_path)

    def run(self):
        super().run()
        transformed_video = torch.zeros([self.APP.Evaluate_Frame_Count,
                                         self.channel, self.height, self.width])
        cur_frame_index = 0
        frame_count = 0

        next_put_index = randint(0, self.APP.Evaluate_Frame_Count)  # 下次需上传下标
        tail_put_index = next_put_index + self.APP.Evaluate_Frame_Count

        ret, frame = self.cap.read()
        while cur_frame_index < self.length and ret:
            if cur_frame_index == tail_put_index:
                last_put_index = tail_put_index  # 上次发送帧下标
                rand_count = randint(0, self.APP.Evaluate_Frame_Count)
                next_put_index = last_put_index + rand_count
                tail_put_index = next_put_index + self.APP.Evaluate_Frame_Count
                print("camera_thread --> get rand_count = ", rand_count)

            if next_put_index <= cur_frame_index < tail_put_index:
                # frame = cv2.flip(frame, 1)  # 左右翻转 (cv2 显示视频为左右翻转,故为之)
                # cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # 将 frame 转换为 tkinter 可以显示的格式
                # img = Image.fromarray(cv2image)
                frame = transform(frame)  # 转换格式
                transformed_video[frame_count] = frame
                frame_count += 1

            # 满足个数 | 视频最后一帧
            can_get_features = frame_count == self.APP.Evaluate_Frame_Count \
                               or cur_frame_index == self.length - 1
            can_get_features = can_get_features and frame_count > 1

            if can_get_features:
                features = get_features(transformed_video[0: frame_count, ],
                                        frame_batch_size=self.APP.Get_Feature_Batch_Size,
                                        device=self.APP.Device)

                features = torch.unsqueeze(features, 0)  # torch.Size([1, len, xxxx])
                with torch.no_grad():
                    input_length = features.shape[1] * torch.ones(1, 1)
                    outputs = self.model(features, input_length)
                    ans = outputs[0][0].to('cpu').numpy()
                    print("VideoMultiEval --> get ans = ", ans)

                    record_item = RecordItem(cur_frame_index - frame_count, frame_count, ans)
                    record_item.set_method(Method.MULTI_METHOD)
                    self.APP.result_records.append(record_item)
                    self.APP.app_refresh_eval_info()
                frame_count = 0
            cur_frame_index += 1
            ret, frame = self.cap.read()

        self.APP.result_records.append(RecordItem.END_SIGN)
        self.APP.EVAL_END_SIGN.set()
        self.APP.EVAL_STATE = State.FINISHED_STATE
        messagebox.showinfo(title="分段评估", message="分段评估已完成！")


class VideoSingleEval(VideoEvalThread):
    def __init__(self, APP, video_path, start_index=0, end_index=0, is_specified=False):
        super().__init__(APP, video_path)
        self.start_index = start_index
        self.end_index = end_index
        self.is_specified = is_specified

    def run(self):
        super().run()
        cur_frame_index = self.start_index
        self.transformed_video = torch.zeros([self.length, self.channel, self.height, self.width])

        frame_count = self.length
        if self.end_index > frame_count or self.end_index == 0:
            self.end_index = frame_count

        ret, frame = self.cap.read()
        while cur_frame_index < self.end_index and ret:
            print("current_frame_index = ", cur_frame_index)
            # frame = cv2.flip(frame, 1)  # 左右翻转 (cv2 显示视频为左右翻转,故为之)
            # cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将 frame 转换为 tkinter 可以显示的格式
            # img = Image.fromarray(cv2image)
            frame = transform(frame)  # 转换格式
            self.transformed_video[cur_frame_index] = frame
            cur_frame_index += 1
            ret, frame = self.cap.read()

        features = get_features(self.transformed_video,
                                frame_batch_size=self.APP.Get_Feature_Batch_Size,
                                device=self.APP.Device)
        features = torch.unsqueeze(features, 0)

        with torch.no_grad():
            input_length = features.shape[1] * torch.ones(1, 1)
            outputs = self.model(features, input_length)
            ans = outputs[0][0].to('cpu').numpy()

            record_item = RecordItem(0, cur_frame_index, ans)
            if self.is_specified:
                record_item.set_method(Method.SPECIFIED_METHOD)
            else:
                record_item.set_method(Method.SINGLE_METHOD)

            self.APP.result_records.append(record_item)
            self.APP.app_refresh_eval_info()
            print("VideoSingleEval --> 获取评测结果：", ans)

        self.APP.EVAL_END_SIGN.set()
        self.APP.EVAL_STATE = State.FINISHED_STATE
        messagebox.showinfo(title="整段评估结果:", message="视频质量为: " + str(ans))
        print("VideoSingleEval --> end")
