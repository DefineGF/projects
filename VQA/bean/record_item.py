# Note: 比较显眼的是 END_SIGN 的设置
"""
    END_SIGN 初衷： 折线图动态显示分段评估结果时设计的是边评估边显示，即生产者-消费者模式；
    获取评估结果并显示的一方（消费者) 并不知道何时才算结束，因此通过生产者上传 END_SIGN 来通知消费者评估已经结束！
"""
class RecordItem:
    END_SIGN = 444

    def __init__(self, start_index, count, ans):
        self.start_index = start_index
        self.count = count
        self.ans = ans

    def set_method(self, method):
        self.method = method
