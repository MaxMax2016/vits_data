import os
import re
import time
import torch
import zhconv
import whisper
import pathlib
import soundfile
import threading
import torchaudio


def timeit(func):
    def run(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        print('executing \'%s\' costed %.3fs' % (func.__name__, time.time() - t))
        return res

    return run


def add_line(txt_path, text):
    with open(txt_path, "a") as f:
        f.write(str(text) + "\n")


def get_end_file(dir_path, end):
    file_lists = []
    for root, dirs, files in os.walk(dir_path):
        for f_file in files:
            if f_file.endswith(end):
                file_lists.append(os.path.join(root, f_file).replace("\\", "/"))

    return file_lists


@timeit
def wsp_asr(w_path):
    result = model.transcribe(w_path, language="chinese")
    return result


def wav_to_text(w_path):
    print(f"file:{w_path}")
    result = wsp_asr(w_path)
    sentence = ""
    end = 0
    for i in result["segments"]:
        start = i["start"]
        sen_time = start - end
        if end:
            if sen_time <= 0.5:
                sentence += "，"
            elif 0.5 < sen_time <= 1.5:
                sentence += "。"
            elif 2.5 < sen_time:
                sentence += "……"
        sentence += re.sub("[^\u4e00-\u9fa5，。……]", '', i["text"]).replace(" ", "、")
        end = i["end"]
    sentence += "。"
    sentence = zhconv.convert(sentence, 'zh-cn')
    add_line(f"{project_path}/{project_name}.txt", f"{w_path}|{pro_id}|{sentence}")
    THREADMAX.release()
    print(sentence)


def create_map_txt(txt_path):
    his = []
    if not os.path.exists(txt_path):
        open(txt_path, "w").close()
        print("create filelist.txt")
    else:
        with open(txt_path, "r") as f:
            raw_data = f.readlines()
            for raw_line in raw_data:
                his.append(raw_line.split("|")[0])
    return his


# 并发线程数，i5-8300h、gtx1066这两个刚好支持4线程且有冗余，可试运行一次参考资源利用率自行估计
THREADMAX = threading.BoundedSemaphore(1)

pro_id = 0
project_name = "qiu"
project_path = f"./{project_name}"
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = whisper.load_model("medium").to(dev)

history = create_map_txt(f"{project_path}/{project_name}.txt")
file_list = get_end_file(f"{project_path}", "wav")
count = 0
# asr遍历
for wav_path in file_list:
    if wav_path not in history:
        THREADMAX.acquire()
        thd = threading.Thread(target=wav_to_text, args=(wav_path,))
        thd.start()
    count += 1
    print("%.2f%%" % (count / len(file_list) * 100))
