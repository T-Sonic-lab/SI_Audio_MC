
# 1. SI Audio M/C (AI Music DJ)
A Python-based AI music DJ application that uses the local LLM runtime Ollama.  
It can play music continuously from multiple folders.

## 2. Description
- Searches for music files (MP3, M4A, WAV, and FLAC) across multiple folders using a local AI model through Ollama.  
    Selection criteria include the season, time of day, and your current mood (entered by the user).  
    A setting is also available to play every track, skipping AI-based selection.

- Crossfade playback provides seamless transitions between tracks.

- Automatic volume leveling keeps the overall volume consistent.

- GPU temperature monitoring with a cooling wait feature for large music libraries or many folders.  
    While the GPU temperature is above 60°C, AI selection pauses and the app sleeps.

- You can change the AI model used by editing the settings. The default model is `llama3`.

- Short-play mode (90 seconds by default) quickly switches between tracks.  
    This is useful for playing through many tracks rapidly.

- List the music folders to scan in `music.txt`.
    You can specify multiple folders and change which `music.txt` file the app uses in the settings.  
    You can create separate lists by genre, for example, and switch between them.  
    The first line of the file is the title.  
    If it contains `[ALL]`, AI-based selection is skipped and all tracks are included.  

- Works offline (runs entirely on your device).  
    The app uses Ollama to run a large language model (LLM) locally and works completely offline.

## 3. Requirements
- OS: Windows 11
- Python: Python 3.12 (a virtual environment is recommended)
- LLM runtime: Ollama (must be running as a service)
- LLM model: `llama3` (must be pulled in Ollama beforehand)
- Supported audio formats: MP3, M4A, WAV, FLAC

## 4. Installation
### 1. Extract all files from the ZIP archive into a folder of your choice.

**Do not run the application directly from the ZIP archive. Extract it to a folder first.**  
**To update the application, replace only `SI_Audio_MC.py`.**

✨ After extracting the downloaded ZIP file, the folder structure should look like this:

**If extracted to the D: drive:**
```text
  🖴D:\
    ┣📁SI_Audio_MC       : Application folder (location is optional) [1]
      ┃  config.ini      : Configuration file
      ┃  music.txt       : List of music folders
      ┃  Prompt.txt      : Prompt
      ┃  Readme.txt      : Application documentation
      ┃  SI_Audio_MC.py  : Main application
      │                   ** End of files included in the ZIP archive [2]**
  ¯¯¯¯│¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
      └📁.venv           : **Folder created by the venv command**
        │    pyvenv.cfg
        │
        ├📁Include
        ├📁Lib
        ├📁Scripts
        └📁share
```

### 2. Set up the environment

#### a. Open Command Prompt.

#### b. Navigate to the folder where you saved the application.
```bash
d:
cd \SI_Audio_MC
```
```text
D:\SI_Audio_MC >
```

#### c. Create the `.venv` virtual environment with this command.
```bash
python -m venv .venv
```

#### d. Activate the virtual environment with this command.
```bash
call .venv\Scripts\activate
```
```text
(.venv) D:\SI_Audio_MC >
```

#### e. Install the required libraries.
- To install all packages at once using the included `requirements.txt` file:
```bash
pip install -r requirements.txt
```

- To install the libraries individually:
```bash
pip install ollama
pip install pygame
pip install pydub
pip install pynvml
pip install configparser
```
    **Install any additional libraries if needed.**

### 3. Add the paths of the folders containing your music files to `music.txt`.

    **Lines beginning with `#` are skipped and treated as excluded folders.**

## 5. Uninstallation
    Delete the application folder and all of its contents.

    **This application does not use the Windows registry.**

## 6. Usage

- **Starting the application**

### 1. Open Command Prompt.

### 2. Navigate to the application folder.
```bash
D:
cd \SI_Audio_MC
```
```text
D:\SI_Audio_MC >
```

### 3. Activate the virtual environment.
```bash
call .venv\Scripts\activate
```
```text
(.venv) D:\SI_Audio_MC >
```

### 4. Start the application.
```bash
python SI_Audio_MC.py
```
Enter your mood, and the AI will select music from each folder.  
Playback begins after the selection process is complete for all folders.

### 5. To exit  

#### a. Stop the application by pressing **Ctrl+C**.

#### b. Exit the virtual environment with the following command.
```bash
call .venv\Scripts\deactivate
```

#### c. Close Command Prompt with the following command.
```bash
exit
```

- **About the `config.ini` settings file**
```text
[DEFAULT]                  ** Default values **
debug=False              : Debug mode (No)
GPU_temp=60              : Maximum GPU temperature (60°C)
short_play=False         : Short-play mode (No)
short_time=90.0          : Short-play duration (90 seconds)
crossfade_ms=30000       : Crossfade duration (30000 ms)
model=llama3             : AI model
prompt=./prompt.txt      : Prompt file
music=./music.txt        : Music folder list file

[SYSTEM]                   ** Optional values **
debug=False              : Set to True to enable debug mode
GPU_temp=60              : Maximum GPU temperature (°C). The app sleeps when this temperature is exceeded.
short_play=True          : Set to True to enable short-play mode
short_time=135.0         : Short-play duration (seconds)
crossfade_ms=45000       : Crossfade duration (ms)
model=llama3             : AI model to use
prompt=./prompt.txt      : Prompt file
music=./music.txt        : Music folder list file
```
  

## 🤝 Feedback
This project is freeware and is intended for free use.  
If you find this software helpful, stars and feedback would be greatly appreciated.

## 📜 License
This project is released under the **MIT License**.  
Anyone is free to use, modify, and redistribute it.  
For the full license terms, including copyright and warranty disclaimers,  
please see the `LICENSE` file in the repository root.

---
### Author

| Item | Details |
| :--- | :--- |
| **Handle** | T-Sonic |
| **Website** | [音速の旅人](https://sonicfarer.nobody.jp/) |
| **Blog** | [A Compass Called `SI Audio M/C` in the Sea of Music](https://sonicfarer.blog-sim.com/Entry/5/) |

---

* Copyright © 2026 T-Sonic *

