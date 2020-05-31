"""
    拍摄模式时，读取线程使用的是一边读取显示，一边放入队列中
    评估线程从队列中获取视频帧，并根据信息进行评估
"""

class QueueItem:
    PAUSE_SIGN_INDEX = -1 # 表示 读取暂停
    STOP_SIGN_INDEX = -2  # 表示 读取终止

    '''
        index: 视频帧下标
        image: 固定格式的视频帧
    '''
    def __init__(self, index, image):
        self.frame_index = index
        self.frame = image

if __name__ == "__main__":
    print(QueueItem.PAUSE_SIGN_INDEX)
    item = QueueItem(10, "image")
    print(item.frame_index)
    print(item.frame)