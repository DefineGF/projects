from enum import Enum

class Mode(Enum):
    INSERT_FILE_MODE = 0      # 导入视频模式
    CAMERA_MODE = 1    # 摄像头模式
    DEFAULT_MODE = 2   # 保护模式 -> 防止未设置模式情况下误触

class State(Enum):
    UN_START_STATE = 2  # 未启动状态
    PAUSE_STATE = 0    # 暂停状态
    RUNNING_STATE = 1  # 运行状态
    FINISHED_STATE = 3 # 完成状态

class Method(Enum):
    SINGLE_METHOD = 1
    MULTI_METHOD = 2
    SPECIFIED_METHOD = 3 # 指定帧评估

