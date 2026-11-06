"""用 Kokoro 產生單字與片語的發音音檔（開發用，不是網頁的一部分）。

用法（在本儲存庫根目錄執行，Python 用「開口說」專案裡裝好的 Kokoro 環境）：
  C:/cowork/kaikou-project/.tts/venv/Scripts/python.exe tools/make_audio.py
      讀 data/A.json、B.json、C.json、P.json，產生 audio/<題庫>/<檔名>.mp3。
      已存在的檔案會跳過；加 --force 全部重做，加 --only conduct,permit 只重做指定的字。
  C:/cowork/kaikou-project/.tts/venv/Scripts/python.exe tools/make_audio.py --list
      只列出「名詞、動詞念法不同」的字目前採用的念法，不產生音檔。

檔名規則（vocab-quiz.html 的 audioURL() 要一致）：單字轉小寫，空白換成「-」。

需要：kokoro-onnx 0.6.1、模型檔 kokoro-v1.0.onnx 與 voices-v1.0.bin、ffmpeg。
模型預設在 C:/cowork/kaikou-project/.tts/models，可用 --models 指定別的資料夾。
聲音固定用 af_heart（Kokoro 女聲），速度 0.9，所有音檔才會一致。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BANKS = ["A", "B", "C", "P"]
VOICE = "af_heart"
SPEED = 0.9

# 名詞、動詞（或形容詞）念法不同的字。
# Kokoro 只念單一個字時通常用名詞的念法，所以這裡依題庫「中文（正解）的第一個字義」指定念法，
# 用 Kokoro 的音標直接念。音標的 ˈ 標在重音音節的母音前面。
# 新增字時：先用 --list 看預設念法，再參考 espeak 在「to 某字」「the 某字」的念法填入。
HETERONYMS = {
    # 動詞：重音在後
    "conduct":    ("kəndˈʌkt",       "v. 進行"),
    "construct":  ("kənstɹˈʌkt",     "v. 建造"),
    "converse":   ("kənvˈɜːs",       "v. 交談"),
    "decrease":   ("dᵻkɹˈiːs",       "v. 減少"),
    "exploit":    ("ɛksplˈɔɪt",      "v. 剝削"),
    "insert":     ("ɪnsˈɜːt",        "v. 插入"),
    "permit":     ("pɚmˈɪt",         "v. 允許"),
    "recall":     ("ɹᵻkˈɔːl",        "v. 回想"),
    "upgrade":    ("ʌpɡɹˈeɪd",       "v. 升級"),
    # 名詞：重音在前
    "import":     ("ˈɪmpɔːɹt",       "n. 進口"),
    "refund":     ("ɹˈiːfʌnd",       "n. 退款"),
    # -ate 結尾：形容詞、名詞念 -ət，動詞念 -eɪt
    "alternate":  ("ˈɔːltɚnət",      "adj. 輪流的"),
    "articulate": ("ɑːɹtˈɪkjʊlət",   "adj. 口齒清晰的"),
    "delegate":   ("dˈɛlɪɡət",       "n. 代表"),
    "elaborate":  ("ᵻlˈæbɚɹət",      "adj. 精心的"),
}

# 預設念法已經正確、不必指定的字（供 --list 對照，也提醒以後不要重複檢查）
DEFAULT_OK = {
    "abstract": "adj.", "abuse": "n. /s/", "advocate": "v. -eɪt", "associate": "v. -eɪt",
    "certificate": "n. -ət", "combat": "n.", "compact": "adj.", "compliment": "n.",
    "content": "n.", "contrast": "n.", "convert": "v.", "defect": "n.", "deliberate": "adj. -ət",
    "document": "n.", "experiment": "n.", "export": "n.", "frequent": "adj.", "initiate": "v. -eɪt",
    "insult": "n.", "intimate": "adj. -ət", "mandate": "n.", "moderate": "adj. -ət",
    "overlook": "v.", "polish": "v.", "rebel": "n.", "resume": "v. 重新開始", "segment": "n.",
    "sow": "v. /soʊ/", "supplement": "n.", "survey": "n.", "torment": "n.", "transfer": "n.",
    "transport": "n.",
}


def plain(word):
    return word.replace("**", "").strip()


def slug(word):
    return re.sub(r"\s+", "-", plain(word).lower())


def to_mp3(samples, rate, out):
    """前後各留 0.15 秒靜音，轉成單聲道 48 kbps mp3。"""
    pad = np.zeros(int(rate * 0.15), dtype=np.float32)
    pcm = (np.clip(np.concatenate([pad, samples, pad]), -1, 1) * 32767).astype("<i2").tobytes()
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-",
         "-codec:a", "libmp3lame", "-b:a", "48k", str(out)],
        input=pcm, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="C:/cowork/kaikou-project/.tts/models")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="只重做這些字，以逗號分隔")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    from kokoro_onnx import Kokoro
    m = Path(a.models)
    kokoro = Kokoro(str(m / "kokoro-v1.0.onnx"), str(m / "voices-v1.0.bin"))

    if a.list:
        for w, (ph, note) in sorted(HETERONYMS.items()):
            print(f"{w:12} 指定 {ph:16} 預設 {kokoro.tokenizer.phonemize(w):16} {note}")
        return

    only = {w.strip().lower() for w in a.only.split(",")} if a.only else None
    made = skipped = 0
    for bank in BANKS:
        items = json.loads((ROOT / "data" / f"{bank}.json").read_text(encoding="utf-8"))
        for it in items:
            text, key = plain(it["word"]), slug(it["word"])
            if only is not None and plain(it["word"]).lower() not in only:
                continue
            out = ROOT / "audio" / bank / f"{key}.mp3"
            if out.exists() and not a.force and only is None:
                skipped += 1
                continue
            low = text.lower()
            if low in HETERONYMS:
                samples, rate = kokoro.create(HETERONYMS[low][0], voice=VOICE, speed=SPEED, is_phonemes=True)
            else:
                samples, rate = kokoro.create(text, voice=VOICE, speed=SPEED, lang="en-us")
            to_mp3(samples, rate, out)
            made += 1
            if made % 100 == 0:
                print(f"已產生 {made} 個…", flush=True)
    print(f"完成：產生 {made} 個，跳過已存在的 {skipped} 個")


if __name__ == "__main__":
    sys.exit(main())
