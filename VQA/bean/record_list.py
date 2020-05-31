from bean.record_item import RecordItem
from config_item import *


class RecordList:
    records = []

    def __init__(self, record_list):
        self.records = record_list

    def get_records_info(self):
        cur_method = Method.SINGLE_METHOD
        if len(self.records) < 1:  # 可能分段评估时候, 帧数太少未能评估！
            return "未获取结果, 请切换到整体评估~"

        ans = "分段评估: \n"
        quality_sum = 0
        for item in self.records:
            if item.method == Method.SINGLE_METHOD:  # 整体评估
                ans = "整体评估： \n" + "  视频质量为: " + str(item.ans)
                cur_method = Method.SINGLE_METHOD
                break
            if item.method == Method.SPECIFIED_METHOD:
                cur_method = Method.SPECIFIED_METHOD
                ans = "指定评估： \n" + " 视频质量为: " + str(item.ans)
                break
            elif item.method == Method.MULTI_METHOD:
                cur_method = Method.MULTI_METHOD
                frame_from = item.start_index
                frame_to = frame_from + item.count
                quality = item.ans
                quality_sum += quality
                ans = ans + "帧 from = " + str(frame_from) + " to = " + str(frame_to) \
                      + "\n 视频质量 = " + str(format(quality, ".4f")) + "\n"

            elif item == RecordItem.END_SIGN:
                break

        # 计算平均质量
        if cur_method == Method.MULTI_METHOD:
            ans = ans + "\n平均质量为 = " + str(format(quality_sum / (len(self.records)), ".4f"))
        print("评估结果： ", ans)
        return ans
