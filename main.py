import os
import re
import config
import pathlib
import soundfile
import threading
import torchaudio
from pypinyin import lazy_pinyin, Style
from paddlespeech.cli.asr.infer import ASRExecutor


def resample_to_16000(audio_path):
    raw_audio, raw_sample_rate = torchaudio.load(audio_path)
    if raw_sample_rate != 16000:
        audio_22050 = torchaudio.transforms.Resample(orig_freq=raw_sample_rate, new_freq=16000)(raw_audio)[0]
        soundfile.write(audio_path, audio_22050, 16000)


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


def paddle_asr(w_path):
    asr = ASRExecutor()
    result = asr(audio_file=pathlib.Path(w_path), force_yes=True)
    result = re.sub("[^\u4e00-\u9fa5]", '', result)
    return result


def text_to_lab(w_path, text):
    pinyin_list = lazy_pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
    pinyin = " ".join(pinyin_list)
    print(pinyin)
    with open(w_path.replace(".wav", ".lab"), "w") as f:
        f.write(pinyin)


def wav_to_text(w_path):
    print(f"file:{w_path}")
    result = paddle_asr(w_path)
    add_line(f"{config.project_path}/{config.project_name}.txt", f"{w_path}|{config.pro_id}|{result}")
    THREADMAX.release()
    print(result)


def create_map_txt(txt_path):
    his = []
    if not os.path.exists(txt_path):
        open(txt_path, "w", encoding='utf-8').close()
        print("create filelist.txt")
    else:
        with open(txt_path, "r") as f:
            raw_data = f.readlines()
            for raw_line in raw_data:
                his.append(raw_line.split("|")[0])
    return his


# 并发线程数，i5-8300h、gtx1066这两个刚好支持4线程且有冗余，可试运行一次参考资源利用率自行估计
THREADMAX = threading.BoundedSemaphore(4)

pro_id = config.pro_id
project_name = config.project_name
project_path = config.project_path

pinyin_dict = []
# 获取字典中存在的拼音
with open(config.pinyin_dict_path, "r", encoding='utf-8') as f:
    raw = f.readlines()
    for line in raw:
        pinyin_dict.append(line.split(" ")[0])
history = create_map_txt(f"{project_path}/{project_name}.txt")
file_list = get_end_file(f"{project_path}", "wav")
count = 0
# asr遍历
for wav_path in file_list:
    resample_to_16000(wav_path)
    if wav_path not in history:
        THREADMAX.acquire()
        thd = threading.Thread(target=wav_to_text, args=(wav_path,))
        thd.start()
        count += 1
        print("%.2f%%" % (count / len(file_list) * 100))
# 生成lab文件
with open(f"{project_path}/{project_name}.txt", "r") as f:
    raw = f.readlines()
    for line in raw:
        data = line.replace("\n", "").split("|")
        text_to_lab(data[0], data[-1])
