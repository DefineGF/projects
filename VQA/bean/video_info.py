from utils import *
import cv2

class VideoInfo:
    v_width = 0
    v_height = 0
    v_channel = 0
    frame_count = 0
    frame_rate = 0

    is_inited = False

    def __init__(self, file_path = ""):
        if file_path != "":
            self.set_file_path(file_path)

    def set_file_path(self, file_path):
        if is_video_file(file_path):
            cap = cv2.VideoCapture(file_path)
            self.v_width = cap.get(3)  # 宽度
            self.v_height = cap.get(4)  # 高度
            self.frame_rate = cap.get(5)  # 帧率
            self.frame_count = cap.get(7)  # 帧数
            ret, frame = cap.read()
            if ret:
                self.v_channel = frame.shape[2]
            cap.release()
            self.is_inited = True

    def clear(self): # 避免多次创建对象
        self.v_width = 0
        self.v_height = 0
        self.v_channel = 0
        self.frame_count = 0
        self.frame_rate = 0
        self.is_inited = False

    def set_frame_width(self, width):
        self.v_width = width

    def set_frame_height(self, height):
        self.v_height = height

    def set_frame_channel(self, channel):
        self.v_channel = channel

    def set_frame_count(self, frame_count):
        self.frame_count = frame_count

    def set_frame_rate(self, frame_rate):
        self.frame_rate = frame_rate

    def get_info_string(self):
        return "width = " + str(self.v_width) + "\n" +\
               "height = " + str(self.v_height) + "\n" +\
               "channel = " + str(self.v_channel) + "\n" +\
               "fps = " + str(format(self.frame_rate, '.1f')) + "\n" +\
               "frame count = " + str(self.frame_count) + "\n"



if __name__ == "__main__":
    videoInfo = VideoInfo("C:\\Users\\lenovo\\Desktop\\论文相关\\VSFA-master\\test_1.mp4")
    print(videoInfo.get_info_string())
