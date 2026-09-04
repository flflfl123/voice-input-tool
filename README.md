[中文]( README_zh.md)
***

# Voice Input Tool

A Windows voice input tool based on AI large models, supporting multiple speech recognition services, triggered by global hotkeys, with recognition results automatically pasted to the cursor position.

***

##  Before You Start

 ⚠️**This project was entirely written with AI assistance (Vibe Coding). The author does not know programming.**

 **Tech Stack: Python + CustomTkinter**

This tool was originally made **just for personal use**, so the features are relatively basic and the code may be full of errors and not elegant.

The motivation for creating this software came from seeing a voice input project called **VIBING**, but it was not open source. To avoid potential issues, I made this open-source version.

Currently, it only supports **Windows**, as I don't have Mac or Linux computers, don't know programming, and don't plan to develop versions for other platforms. However, I will keep it open source, hoping this project can help others.

Please be gentle if you don't like it 🙏

***

## Features

- **Global Hotkey Trigger**: Press `Ctrl+Alt` to start recording, press again to stop and recognize
- **Multiple Recognition Services**: Supports Doubao, Volcengine, OpenAI compatible format (e.g., DashScope)
- **Auto Paste**: Recognition results automatically copied to clipboard and pasted to cursor position
- **Tray Icon**: System tray displays recording status, supports right-click menu
- **Floating Window**: Optional floating window; when enabled, only the floating window is shown (main window hidden) with real-time recording status, and recognition results are automatically copied to clipboard and pasted to cursor position; when floating window is disabled, results are displayed in the main window text box and require manual click to copy
- **Theme Switching**: Supports light/dark themes
- **Multi-language Support**: Supports 15 interface languages
- **History Records**: Automatically saves recognition history

## System Requirements

- Windows 10 (Windows 11 should work in theory, but not tested)
- Python 3.8 or higher
- Microphone device

##Screenshot
<img width="1442" height="871" alt="PixPin_2026-04-30_20-04-36" src="https://github.com/user-attachments/assets/0fb2dc21-44ef-4da9-a43b-a48a37f26cf1" />


<img width="1442" height="871" alt="PixPin_2026-04-30_20-04-53" src="https://github.com/user-attachments/assets/95530406-9133-4745-b7d5-4618657c5bfb" />


<img width="1442" height="871" alt="PixPin_2026-04-30_20-05-05" src="https://github.com/user-attachments/assets/120ea524-84c8-4aaa-9353-1208fab044da" />


<img width="1442" height="871" alt="PixPin_2026-04-30_20-05-40" src="https://github.com/user-attachments/assets/692fd1fa-e970-4159-a0ab-8bccdb70a1ca" />


<img width="1442" height="871" alt="PixPin_2026-04-30_20-05-56" src="https://github.com/user-attachments/assets/0ba4a907-a038-48fd-8829-145a80c047fa" />

## Installation

### 1. Clone the Project

```bash
git clone <repository URL>
cd voice-input-tool
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Copy the example config file:

```bash
copy config\config.example.json config\config.json
```

Edit `config/config.json` and fill in your API keys:

```json
{
  "asr_provider": "openai_compatible",
  "base_url": "https://api.openai.com/v1",
  "api_key": "YOUR_API_KEY",
  "model": "whisper-1"
}
```

## Configuration

### ASR Provider Configuration

The project supports three speech recognition services:

#### 1. OpenAI Compatible Format (Recommended)

For services compatible with OpenAI API such as DashScope, OpenAI Whisper, etc.

```json
{
  "asr_provider": "openai_compatible",
  "base_url": "https://api.openai.com/v1",
  "api_key": "YOUR_API_KEY",
  "model": "whisper-1"
}
```

#### 2. Doubao Large Model

```json
{
  "asr_provider": "doubao",
  "app_key": "YOUR_APP_KEY",
  "access_key": "YOUR_ACCESS_KEY",
  "resource_id": "volc.bigasr.sauc.duration",
  "asr_mode": "bigmodel_async"
}
```

#### 3. Volcengine

```json
{
  "asr_provider": "volcengine",
  "app_key": "YOUR_APP_KEY",
  "access_key": "YOUR_ACCESS_KEY",
  "cluster": "volcengine_streaming_common"
}
```

### Other Configuration Items

| Config                  | Description                    | Default |
| ----------------------- | ------------------------------ | ------- |
| `sample_rate`           | Audio sample rate (Hz)         | 16000   |
| `chunk_size`            | Audio chunk size (bytes)       | 3200    |
| `autostart`             | Auto-start on boot             | false   |
| `theme`                 | Theme mode (light/dark)        | dark    |
| `floating_enabled`      | Floating window feature        | true    |
| `language`              | Interface language             | zh\_CN  |

## Usage

### Start the Program

**Command Line:**

```bash
python -m voiceinput
```

**In IDE:**

In IDEs like VS Code or PyCharm, directly run the `voiceinput/__main__.py` file.

### Operation Flow

1. Program minimizes to system tray after startup
2. Before first use, configure API settings via tray icon right-click menu -> Settings
3. Press `Ctrl+Alt` to start recording
4. Press `Ctrl+Alt` again to stop recording after speaking
5. Recognition results automatically pasted to cursor position

> **Tip**: If you press the hotkey without configuring API, the floating window will show "AI Not Set". Please complete configuration first.

### Tray Icon

- **Left Click**: Open main window (can be reopened via tray icon after closing)
- **Right Click**: Show menu (quit program)
- **Icon Color**: Gray=Ready, Red=Recording
- **Close Button**: Clicking the close button on the window only hides the window, the program continues running, and the tray icon remains

## Build Executable

Use PyInstaller to build:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name VoiceInput voiceinput/__main__.py
```

Built executable is in `dist/` directory.

## Project Structure

```
├── config/
│   └── config.example.json  # Example config file
├── locales/
│   └── translations.json    # Internationalization translations
├── voiceinput/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Command line entry point
│   ├── main.py              # Main program entry
│   ├── engine.py            # Voice input engine
│   ├── asr_providers.py     # ASR provider implementations
│   ├── audio_recorder.py    # Audio recording module
│   ├── gui.py               # GUI interface
│   ├── hotkey.py            # Hotkey monitoring
│   ├── tray_icon.py         # Tray icon
│   ├── config.py            # Configuration management
│   └── i18n.py              # Internationalization module
├── requirements.txt         # Python dependencies
└── .gitignore               # Git ignore rules
```

## FAQ

### 1. No sound during recording?

- Check if microphone is working properly
- Check system audio input settings
- Ensure `pyaudio` is properly installed

### 2. Recognition failed?

- Check if API keys are correct
- Check network connection
- Check error messages in log output

### 3. Auto paste not working?

- Ensure `pywin32` is installed
- Check if target application supports paste operation

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Contributing

Issues and Pull Requests are welcome!
