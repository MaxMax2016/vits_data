import os
import config
import textgrid


def add_line(txt_path, text):
    with open(txt_path, "a", encoding='utf-8') as f:
        f.write(str(text) + "\n")


pro_id = config.pro_id
project_name = config.project_name
project_path = config.project_path

wav_paths = []
raw_texts = []
file = open(f"{project_path}/{project_name}_align.txt", "w", encoding='utf-8').close()
with open(f"{project_path}/{project_name}.txt", "r", encoding='utf-8') as f:
    raw = f.readlines()
    for line in raw:
        wav_paths.append(line.split("|")[0])
        raw_texts.append(line.split("|")[-1])
# 遍历textgrid，按时间分配停顿符号
for wav_path, raw_text in zip(wav_paths, raw_texts):
    tg = textgrid.TextGrid()
    try:
        tg.read(wav_path.replace("/wavs/", "/text/").replace(".wav", ".TextGrid"))  # 'file.TextGrid' 是文件名
    except FileNotFoundError:
        continue
    pinyin_list = tg.tiers[0].intervals
    mark = [x.mark for x in pinyin_list]
    t_time = [round(x.maxTime - x.minTime, 3) for x in pinyin_list]
    raw_text = list(raw_text)[:-1]
    out_text = []
    for i in range(0, len(mark)):
        if mark[i] == "":
            if 0.35 < t_time[i] <= 0.6:
                out_text.append("、")
            elif 0.6 < t_time[i] <= 1:
                out_text.append("，")
            elif 1 < t_time[i] <= 2:
                out_text.append("。")
            elif 2 < t_time[i]:
                out_text.append("……")
        else:
            if len(raw_text):
                out_text.append(raw_text[0])
                del (raw_text[0])
    if out_text and out_text[0] in ["、", "，", "。"]:
        del (out_text[0])
    result = "".join(out_text)
    add_line(f"{project_path}/{project_name}_align.txt", f"{wav_path}|{pro_id}|{result}")
# 输出filelist
f_train = open(f"{project_path}/{project_name}_train.txt", "w", encoding='utf-8')
f_val = open(f"{project_path}/{project_name}_val.txt", "w", encoding='utf-8')
with open(f"{project_path}/{project_name}_align.txt", "r", encoding='utf-8') as f:
    raw = f.readlines()
    for line in raw:
        if "/train/" in line:
            f_train.write(line)
        else:
            f_val.write(line)
f_train.close()
f_val.close()
