import threading
import torch
from tkinter import messagebox
from torchvision import transforms
from bean.queue_item import QueueItem
from bean.record_item import RecordItem
from VSFA import VSFA
from CNNfeatures import get_features
from config_item import *

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

class CameraEvalThread(threading.Thread):
    def __init__(self, APP, queue):
        super(CameraEvalThread, self).__init__()
        print("CameraEvalThread -->     init()")
        self.APP = APP
        self.source_queue = queue
        self.queue_stop_sign = threading.Event()

    def run(self):
        print("CameraEvalThread -->     run()")
        self.model = VSFA()
        self.model.load_state_dict(torch.load(self.APP.Model_Path))
        self.model.to(self.APP.Device)
        self.model.eval()

        width = int(self.APP.Video_Info.v_width)
        height = int(self.APP.Video_Info.v_height)
        channel = int(self.APP.Video_Info.v_channel)
        print("camera_evaluate_thread --> width = ", width, " height = ", height, "channel = ", channel)
        self.transformed_video = torch.zeros([self.APP.Evaluate_Frame_Count,
                                              channel, height, width])

'''
    摄像头： 分段评估
'''

class CameraMultiEval(CameraEvalThread):
    def __init__(self, APP, queue):
        super().__init__(APP, queue)
        print("CameraMultiEval -->      init()")

    def run(self):
        super().run()
        print("CameraMultiEval -->      run()")
        frame_count = 0
        need_handle = False
        self.queue_stop_sign.clear()

        while True:
            if self.source_queue:  # 判断非空
                queue_item = self.source_queue.get()
                print("camera_evaluate_thread --> get frame")
                if queue_item.frame == QueueItem.PAUSE_SIGN_INDEX:
                    need_handle = True
                elif queue_item.frame == QueueItem.STOP_SIGN_INDEX:
                    need_handle = True
                    self.queue_stop_sign.set()
                else:
                    frame = transform(queue_item.frame)  # 转换格式
                    self.transformed_video[frame_count] = frame
                    frame_count += 1
                    if frame_count == self.APP.Evaluate_Frame_Count:
                        need_handle = True

                if need_handle and frame_count > 1:
                    print("camera evaluate thread -->  开始评估")
                    need_handle = False
                    features = get_features(self.transformed_video[0: frame_count, ],
                                            frame_batch_size=self.APP.Get_Feature_Batch_Size,
                                            device=self.APP.Device)

                    features = torch.unsqueeze(features, 0)  # torch.Size([1, len, xxxx])
                    with torch.no_grad():
                        input_length = features.shape[1] * torch.ones(1, 1)
                        outputs = self.model(features, input_length)
                        ans = outputs[0][0].to('cpu').numpy()
                        print("camera evaluate thread --> get ans = ", ans)

                        record_item = RecordItem(queue_item.frame_index - frame_count, frame_count, ans)
                        record_item.set_method(Method.MULTI_METHOD)
                        self.APP.result_records.append(record_item)
                        self.APP.app_refresh_eval_info()
                    frame_count = 0

            # 阻塞至此
            if self.queue_stop_sign.isSet():
                # self.APP.result_records = self.records
                self.APP.result_records.append(RecordItem.END_SIGN)
                self.APP.EVAL_END_SIGN.set()
                self.APP.EVAL_STATE = State.FINISHED_STATE
                messagebox.showinfo("分段评估", "拍摄模式分段评估已完成！")
                print("camera evaluate thread stop ！")
                break


'''
    摄像头：整段评估
'''
class CameraSingleEval(CameraEvalThread):
    def __init__(self, APP, queue):
        super().__init__(APP, queue)
        print("CameraMultiEval -->      init()")
        # self.records = Queue()

    def run(self):
        super().run()
        self.queue_stop_sign.clear()  # 队列获取数据停止标志
        features = None

        need_post = False
        frame_count = 0
        while True:
            if self.source_queue:
                queue_item = self.source_queue.get()
                print("CameraSingleEval --> get frame")
                if queue_item.frame_index == QueueItem.PAUSE_SIGN_INDEX:
                    need_post = True

                elif queue_item.frame_index == QueueItem.STOP_SIGN_INDEX:
                    need_post = True
                    self.queue_stop_sign.set()
                else:
                    frame = transform(queue_item.frame)
                    self.transformed_video[frame_count] = frame
                    frame_count += 1
                    if frame_count == self.APP.Evaluate_Frame_Count:
                        need_post = True

                if need_post and frame_count > 1:
                    print("CameraSingleEval -->  开始提取特征")
                    need_post = False
                    feature = get_features(self.transformed_video[0: frame_count, ],
                                           frame_batch_size=self.APP.Get_Feature_Batch_Size,
                                           device=self.APP.Device)
                    if features is None:
                        features = feature
                    else:
                        features = torch.cat((features, feature), 0)
                    frame_count = 0

            if self.queue_stop_sign.isSet():
                print("CameraSingleEval -- > 特征提取完毕，开始评估：")
                features = torch.unsqueeze(features, 0)  # torch.Size([1, len, xxxx])
                with torch.no_grad():
                    input_length = features.shape[1] * torch.ones(1, 1)
                    outputs = self.model(features, input_length)
                    ans = outputs[0][0].to('cpu').numpy()
                    print("CameraSingleEval --> get ans = ", ans)

                    record_item = RecordItem(0, frame_count, ans)
                    record_item.set_method(Method.SINGLE_METHOD)
                    self.APP.result_records.append(record_item)
                    self.APP.app_refresh_eval_info()

                messagebox.showinfo("整段评估", "视频质量为:" + str(ans))
                self.APP.EVAL_END_SIGN.set()
                self.APP.EVAL_STATE = State.FINISHED_STATE
                print("CameraSingleEval stop ！")
                break
