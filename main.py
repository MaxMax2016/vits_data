import os
import re
import pathlib
import soundfile
import threading
import torchaudio
from pypinyin import lazy_pinyin, Style
from paddlespeech.cli.asr.infer import ASRExecutor
from paddlespeech.cli.text.infer import TextExecutor


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


def wav_to_lab(wav_path, project_name, pro_id):
    print(f"file:{wav_path}")
    asr = ASRExecutor()
    result = asr(audio_file=pathlib.Path(wav_path), force_yes=True)
    result = re.sub("[^\u4e00-\u9fa5]", '', result)
    pinyin_list = lazy_pinyin(result, style=Style.TONE3, neutral_tone_with_five=True)
    pinyin = " ".join(pinyin_list)
    with open(wav_path.replace(".wav", ".lab"), "w") as f:
        f.write(pinyin)
    add_line(f"{project_path}/{project_name}.txt", f"{wav_path}|{pro_id}|{result}")
    THREADMAX.release()
    print(result)
    print(pinyin)
    print()


# 并发线程数，i5-8300h、gtx1066这两个刚好支持4线程且有冗余，可试运行一次参考资源利用率自行估计
THREADMAX = threading.BoundedSemaphore(4)

project_name = "qiu"
project_path = f"./mfa/{project_name}"
pro_id = 0
history = []
pinyin_dict = []
with open(f"./mfa/mandarin_pinyin.dict", "r", encoding='utf-8') as f:
    raw = f.readlines()
    for line in raw:
        pinyin_dict.append(line.split(" ")[0])
if not os.path.exists(f"{project_path}/{project_name}.txt"):
    file = open(f"{project_path}/{project_name}.txt", "w", encoding='utf-8').close()
    print("create filelist.txt")
else:
    with open(f"{project_path}/{project_name}.txt", "r") as f:
        raw = f.readlines()
        for line in raw:
            history.append(line.split("|")[0])
file_list = get_end_file(f"{project_path}", "wav")
for wav_path in file_list:
    resample_to_16000(wav_path)
    if wav_path not in history:
        THREADMAX.acquire()
        thd = threading.Thread(target=wav_to_lab, args=(wav_path, project_name, pro_id))
        thd.start()
