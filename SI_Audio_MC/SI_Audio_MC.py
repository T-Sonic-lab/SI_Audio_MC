# -*- coding: utf-8 -*-
# Copyright (c) 2026 T-Sonic
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction.

# The Software may be used, copied, modified, merged, published,
# distributed and/or sold by you without restriction.

# PLEASE NOTE:
# While this software is provided under the MIT license,
# the author makes no guarantee regarding its function or reliability.
# Use is strictly at the user's own risk.

# The rights reserved under the MIT License are as follows:
# 1. You may copy, modify, merge, publish, distribute, and sell the Software.
# 2. You must include the copyright notice and the full text of the MIT License
#    in all copies or substantial portions of the Software.

# DISCLAIMER:
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import random
import time  #sleep😴
from datetime import datetime
import threading
import re  #Regexp
import ollama
import pygame
from pydub import AudioSegment
import configparser  #ini File
import pynvml  #GPU Temperature

# 各種設定
IS_DEBUG = False
TARGET_DBFS = -20.0  # 全曲の音量をそろえるターゲット基準値 (デシベル)[-20～-60]

# スレッド間共有用のグローバル変数
next_track_ready = threading.Event()
next_sound_object = None
next_picked_key = ""

IS_ALL_MUSIC = False #全曲演奏

inifile = configparser.ConfigParser()

ROOT_DIR_LIST = []

ALL_KEYS = []          #全曲リスト
ALL_MATCHED_POOL = []  #全抽出リスト

def load_all_music_list():
  global IS_ALL_MUSIC
  file_Music=inifile.get('SYSTEM', 'music')
  print(f"file_Music: {file_Music}")
  if not os.path.exists(file_Music):
    print(f"エラー: {file_Music} が見つかりません。空のリストを返します。")
    return []
  
  root_dir_list = []
  with open(file_Music, "r", encoding="utf-8") as f:
    try:
      for line in f:
        clean_line = line.strip()
        IS_ALL_MUSIC = ('[all]' in clean_line.lower())
        if IS_DEBUG:
          print(f"IS_ALL_MUSIC：{IS_ALL_MUSIC}")
        break
    except StopIteration:
      return []

    for line in f:
      clean_line = line.strip()
      if not clean_line or clean_line.startswith("#"):
        continue
      if os.path.exists(clean_line):
        root_dir_list.append(clean_line)
  return root_dir_list

def load_prompt():
  sPrompt = ""
  filename = inifile.get('SYSTEM', 'prompt')
  if not os.path.exists(filename):
    print(f"警告: Prompt→{filename} が見つかりません。")
    return sPrompt
    
  f=open(filename, "r", encoding="utf-8")
  sPrompt=f.read()
  f.close()
  return sPrompt

def get_context(user_mood):
  now = datetime.now()
  month = now.month
  hour = now.hour
  
  if month in [3, 4, 5]: season = "春 (Spring)"
  elif month in [6, 7, 8]: season = "夏 (Summer)"
  elif month in [9, 10, 11]: season = "秋 (Autumn)"
  else: season = "冬 (Winter)"
  
  if 5 <= hour < 11: timezone = "朝 (Morning)"
  elif 11 <= hour < 16: timezone = "昼・午後 (Afternoon)"
  elif 16 <= hour < 19: timezone = "夕方 (Evening)"
  elif 19 <= hour < 23: timezone = "夜 (Night)"
  else: timezone = "深夜 (Midnight)"
  
  return f"現在の季節: {season}\n現在の時間帯: {timezone}\nリスナーの今の気分: {user_mood}"

def ask_ollama_to_filter(all_keys_list, prompt_text, context_info):
  #"""💡 配列Aから条件にマッチする楽曲をすべてAIに抽出してもらう関数（新仕様）"""

  #files_str = "\n".join(all_keys_list)

  indexed_files = [f"[{i}] {key}" for i, key in enumerate(all_keys_list)]
  files_str = "\n".join(indexed_files)
  
  system_prompt = (f"{prompt_text}\n"
    f"【シチュエーション＆気分】\n{context_info}\n"
  )
  user_prompt = f"【すべての曲リスト】\n{files_str}"

  try:
    response = ollama.chat(
      model=inifile.get('SYSTEM', 'model'),
      messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
      ]
    )
    content = response['message']['content'].strip()

    # AIが返した行から数字（ID）だけを抽出し、元のリストのインデックスとして扱う
    matched_ids = set()
    for line in content.split('\n'):
      match = re.search(r'\d+', line)
      if match:
        idx = int(match.group())
        if 0 <= idx < len(all_keys_list):
          matched_ids.add(idx)
          
    
    # IDを元に、元のリストから安全に曲を抽出（完全一致）
    matched_tracks = [all_keys_list[idx] for idx in sorted(matched_ids)]

    return matched_tracks
  except Exception as e:
    print(f"😖Ollama通信エラー: {e}")
    return []

def main_AI_data(prompt_text, context_info):
  global ALL_KEYS, ALL_MATCHED_POOL

  music_dict = {}
  all_music_dict = {}
  SUPPORTED_EXTENSIONS = ('.mp3', '.m4a', '.flac', '.wav',)

  maxGPU_temp=int(inifile.get('SYSTEM', 'GPU_temp'))
  pynvml.nvmlInit() #GPU
  device_count = pynvml.nvmlDeviceGetCount() #GPU数

  iCNT=0  #フォルダ数
  for root_dir in ROOT_DIR_LIST:
    if not os.path.exists(root_dir):
      continue
    for root, dirs, files in os.walk(root_dir):
      music_dict = {}
      
      GPU_Temp = getGPU_MaxTemp(device_count)
      if GPU_Temp>maxGPU_temp:
        print(f"GPU：{GPU_Temp}℃  🥵冷却中・・・")
        while GPU_Temp>maxGPU_temp:
          time.sleep(5.0) # 5000ミリ秒（5.0秒）スリープする
          GPU_Temp = getGPU_MaxTemp(device_count)
          
      for file in files:
        if file.lower().endswith(SUPPORTED_EXTENSIONS):
          full_path = os.path.join(root, file)
          base_folder_name = os.path.basename(root_dir.rstrip(os.sep))
          display_key = f"[{base_folder_name}]/{os.path.relpath(full_path, root_dir)}"
          music_dict[display_key] = full_path
          
      iCNT+=1
      part_keys = list(music_dict.keys())  # 💡これが「配列A（全件キープ）」
      if music_dict: #配列Aに全件保持
        all_music_dict |= music_dict
        ALL_KEYS += part_keys
        
        matched_pool = []
        if IS_ALL_MUSIC:
          matched_pool = part_keys.copy()  #全曲対象
        else:  # 💡配列B：AIに条件マッチする曲の一括抽出をリクエスト")
          matched_pool = ask_ollama_to_filter(part_keys, prompt_text , context_info)
          #if not matched_pool: # 万が一AIが1曲も返さなかった場合のセーフティ（お好みで調整）
            #matched_pool = part_keys.copy()
        if matched_pool:
          ALL_MATCHED_POOL += matched_pool
        print(f"{iCNT} | {len(matched_pool)} / {len(part_keys)} ： {root}")
        
  pynvml.nvmlShutdown()  #GPU
  return all_music_dict

def getGPU_MaxTemp(device_count):
  maxTemp = 0  #GPU温度
  for i in range(device_count):
    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
    #name = pynvml.nvmlDeviceGetName(handle)
    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
    if temp>maxTemp:
      maxTemp = temp
    #print(f"GPU {i} ({name}): {temp}°C")
    
  return maxTemp

def background_prepare_next_track(next_track_path):
  """💡 再生中に裏で『次の曲のロードと音量調整だけ』をピンポイントで行う関数（超軽量化）"""
  global next_sound_object
  next_sound_object = load_and_normalize_sound(next_track_path)
  next_track_ready.set()

def load_and_normalize_sound(file_path):
  ext = os.path.splitext(file_path)[1].lower()
  match ext:
    case ".mp3":
      format_type = "mp3"
    case ".flac":
      format_type = "flac"
    case ".wav" | ".wave":
      format_type = "wav"
    case ".ogg":
      format_type = "ogg"
    case _:
      format_type = "mp4"
  
  audio = AudioSegment.from_file(file_path, format=format_type)
  change_in_dBFS = TARGET_DBFS - audio.dBFS
  normalized_audio = audio.apply_gain(change_in_dBFS)
  return pygame.mixer.Sound(buffer=normalized_audio.raw_data)

def main():
  global next_sound_object, next_picked_key, ROOT_DIR_LIST, IS_DEBUG
  
  short_play = False  # フル再生モード
  short_time = 90.0   # ショート再生演奏時間(秒)
  
  # pygameの初期化
  pygame.mixer.pre_init(44100, -16, 2, 512)
  pygame.init()
  pygame.mixer.set_num_channels(2)
  ch_current = pygame.mixer.Channel(0)
  ch_next = pygame.mixer.Channel(1)
  
  inifile.read('config.ini', encoding='utf-8-sig') #初期化ファイル
  short_time = float(inifile.get('SYSTEM', 'short_time'))
  short_play = (inifile.get('SYSTEM', 'short_play')=="True")
  IS_DEBUG = (inifile.get('SYSTEM', 'debug')=="True")
  
  default_crossfade_ms = int(inifile.get('SYSTEM', 'crossfade_ms'))
  
  print("🔍音楽ライブラリをスキャン中...")
  ROOT_DIR_LIST = load_all_music_list()
 
  if IS_ALL_MUSIC:
    user_mood = "全曲対象"
  else:
    user_mood = input("今の気分や聴きたい雰囲気を入力してください（例: 元気が出る曲, 落ちつく曲）\n> ")
    if not user_mood.strip():
      user_mood = "平常運転中"
    
  context_info = get_context(user_mood)
  prompt_text = load_prompt() #プロンプト読み取り

  if IS_DEBUG:
    print(f"{prompt_text}\n【シチュエーション＆気分】\n{context_info}\n")

  music_dict = main_AI_data(prompt_text, context_info)

  if not music_dict: # 万が一AIが1曲も返さなかった場合のセーフティ
    print(f"[システム] AIによる抽出結果が0件だったため、全曲を対象にします。\n{context_info}")
    matched_pool = ALL_KEYS.copy()
  else:
    matched_pool = ALL_MATCHED_POOL
  
  print(f"[システム] {len(matched_pool)} /  {len(ALL_KEYS)} 曲")
  
  random.shuffle(matched_pool) # 💡配列Bをランダムに並び替える
  print("[システム] 🔀配列Bのシャッフルが完了しました。再生を開始します。")
  
  pool_index = 0
  song_count = 1
  
  picked_key = matched_pool[pool_index]  # 1曲目の再生準備
  print(f"\n--- {song_count}曲目の再生準備 ---")
  print(f"🎚️音量レベルを調整中...")
  sound_current = load_and_normalize_sound(music_dict[picked_key])
  
  total_duration_sec = sound_current.get_length()
  print(f"\n（現在の配列B再生位置: {pool_index + 1} / {len(matched_pool)} 曲目）")
  print(f"✨ 再生中: {picked_key} (全長: {int(total_duration_sec)}秒)")
  
  ch_current.play(sound_current)
  ch_current.set_volume(1.0)
  
  if short_play:
    duration_sec = short_time
  else:
    duration_sec = total_duration_sec
    
  fade_sec = default_crossfade_ms / 1000.0
  start_time = time.time()
  
  while True: # 音量解析の時間を考慮し、フェード開始の25秒前に裏処理（次の曲のロード）を起動
    lead_time = fade_sec + 25.0
    next_track_triggered = False
    
    while True:
      elapsed = time.time() - start_time
      remaining = duration_sec - elapsed
      
      if remaining <= lead_time and not next_track_triggered:
        next_track_ready.clear()
        
        next_index = pool_index + 1 # 💡 次の曲のインデックスを計算
        
        # 💡 3. 全て流し終わったら、配列Bをランダムに並び替えて最初(0)に戻る
        if next_index >= len(matched_pool):
          print("\n[システム] 🔀配列Bの曲をすべて流し終えました。再シャッフルしてループします。")
          random.shuffle(matched_pool)
          next_index = 0
        
        next_picked_key = matched_pool[next_index]
        
        # 裏スレッドでは「音量調整とロード」だけを行う（Ollamaは呼ばないので超高速）
        bg_thread = threading.Thread(
          target=background_prepare_next_track,
          args=(music_dict[next_picked_key],)
        )
        bg_thread.start()
        next_track_triggered = True
      
      if elapsed >= (duration_sec - fade_sec) or not ch_current.get_busy():
        break
      time.sleep(0.1)
      
    # 裏スレッドでのロード完了を待つ
    next_track_ready.wait()
    
    # インデックスを次の曲に進める（ループ処理を跨いだ場合は上記で0にリセット済）
    pool_index = pool_index + 1 if (pool_index + 1) < len(matched_pool) else 0
    song_count += 1
    
    # クロスフェード開始
    ch_next.play(next_sound_object)
    ch_next.set_volume(0.0)
    total_duration_sec = next_sound_object.get_length()
    
    print(f"\n（現在の配列B再生位置: {pool_index + 1} / {len(matched_pool)} 曲目）")
    print(f"✨ 再生中: {next_picked_key} (全長: {int(total_duration_sec)}秒)")
    fade_steps = 100
    step_sleep = fade_sec / fade_steps
    
    for step in range(1, fade_steps + 1):
      ratio = step / fade_steps
      if ch_current.get_busy():
        ch_current.set_volume(1.0 - ratio)
      if ch_next.get_busy():
        ch_next.set_volume(ratio)
      time.sleep(step_sleep)
    ch_current.stop()
    
    # チャンネルとサウンドの入れ替え
    ch_current, ch_next = ch_next, ch_current
    sound_current = next_sound_object
    start_time = time.time()
    
    inifile.read('config.ini', encoding='utf-8-sig')  #初期化ファイル(動的にチェック)
    default_crossfade_ms = int(inifile.get('SYSTEM', 'crossfade_ms'))
    short_play = (inifile.get('SYSTEM', 'short_play')=="True")  # 短縮再生
    if short_play:
      short_time = float(inifile.get('SYSTEM', 'short_time'))  # 短縮再生時間
      duration_sec = short_time  # 再生時間(Short)
    else:
      duration_sec = sound_current.get_length()		# 再生時間(Full)

if __name__ == "__main__":
  main()

