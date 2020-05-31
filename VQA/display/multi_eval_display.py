import numpy as np
import matplotlib.pyplot as plt
from bean.record_item import RecordItem
from utils import *

def multi_eval_show(APP):
    x, y = [], []
    line_x = []
    item_index = 0
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.title("分段评估折线图")
    plt.xlabel("帧数")
    plt.ylabel("评分")
    plt.ion()
    while True:
        if len(APP.result_records) > item_index:
            item = APP.result_records[item_index]
            item_index += 1
            if item != RecordItem.END_SIGN:
                plt.cla()
                start_index = item.start_index
                count = item.count
                ans = item.ans
                line_x.append(start_index)
                line_x.append(start_index + count)
                x.append(start_index + count / 2)
                y.append(ans)
                plt.plot(np.array(x), np.array(y))
                plt.scatter(np.array(x), np.array(y))
                plt.grid()
                plt.pause(0.5)
            else:
                for i in line_x:
                    plt.vlines(i, 0, 1, colors="red", linestyles="dashed")
                break
    plt.title("分段评估折线图")
    plt.xlabel("帧数")
    plt.ylabel("评分")
    plt.ioff()
    save_img_name = generate_file_name_by_time(".png")
    plt.savefig("./output/" + save_img_name)

