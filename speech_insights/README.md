# Speech Insights

## Realtime Speech-to-Text (ElevenLabs)

This module streams microphone audio to ElevenLabs Realtime STT and prints:

- partial transcripts (updated in-place)
- committed transcripts (printed as new lines)

### Setup

1) Ensure `.env` contains `ELEVENLABS_API_KEY=...`

2) Install Python (3.10+ recommended) and create a venv:

```bash
python -m venv .venv
```

3) Activate venv:

- PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

4) Install deps:

```bash
pip install -r requirements.txt
```

### Run

```bash
python speech_insights/realtime_stt_elevenlabs.py
```

If you get microphone/PortAudio errors on Windows, install a working audio backend (common fix: reinstall `sounddevice` after installing a PortAudio-enabled Python distribution).

