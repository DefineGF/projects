from PIL import Image
import datetime


def img_resize(target_width, target_height, pil_img):  # 缩放图片大小 适配Label
    w, h = pil_img.size
    f = 1
    if w != 0 and h != 0:
        f1 = target_width / w
        f2 = target_height / h
        f = min(f1, f2)
    width = int(w * f)
    height = int(h * f)
    return pil_img.resize((width, height), Image.ANTIALIAS)

def is_video_file(file=""):
    return file.endswith(('.mp4', '.mkv', '.avi', '.wmv', '.iso'))

def generate_file_name_by_time(tail):
    return str(datetime.datetime.now()).split('.')[0].replace(':', '_') + tail

if __name__ == "__main__":
    print(is_video_file())