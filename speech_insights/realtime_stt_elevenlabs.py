import asyncio
import base64
import json
import os
import queue
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import numpy as np
import sounddevice as sd
import websockets
from dotenv import load_dotenv


ELEVENLABS_REALTIME_WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    # 20ms @ 16kHz = 320 samples. Using 40ms for fewer websocket messages.
    blocksize: int = 640


def _b64_pcm16le(audio_i16: np.ndarray) -> str:
    # Ensure little-endian 16-bit PCM bytes for ElevenLabs.
    pcm_bytes = audio_i16.astype("<i2", copy=False).tobytes()
    return base64.b64encode(pcm_bytes).decode("ascii")


def _print_partial(line: str) -> None:
    # Overwrite the current console line for partial results.
    sys.stdout.write("\r" + line + " " * max(0, 10))
    sys.stdout.flush()

def _default_transcript_path() -> Path:
    out_dir = Path(__file__).resolve().parent / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return out_dir / f"{stamp}.txt"


async def _transcript_writer(
    *,
    committed: list[str],
    committed_lock: asyncio.Lock,
    out_path: Path,
    stop_event: asyncio.Event,
    flush_interval_secs: float,
) -> None:
    """
    Periodically append newly committed transcript lines to disk.
    """
    last_written = 0

    # Create/overwrite the file early so the user can see it immediately.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("", encoding="utf-8")

    while True:
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=flush_interval_secs)
        except asyncio.TimeoutError:
            pass

        async with committed_lock:
            new_lines = committed[last_written:]
            last_written = len(committed)

        if new_lines:
            with out_path.open("a", encoding="utf-8", newline="\n") as f:
                for line in new_lines:
                    if line:
                        f.write(line.rstrip() + "\n")
                f.flush()

        if stop_event.is_set():
            return


async def _receiver(ws, committed_out: list[str], committed_lock: asyncio.Lock) -> None:
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        mtype = msg.get("message_type")
        if mtype == "session_started":
            cfg = msg.get("config", {})
            model_id = cfg.get("model_id")
            _print_partial(f"[elevenlabs] session started (model_id={model_id})")
            continue

        if mtype == "partial_transcript":
            text = msg.get("text", "")
            _print_partial(text)
            continue

        if mtype in ("committed_transcript", "committed_transcript_with_timestamps"):
            text = msg.get("text", "")
            if text:
                async with committed_lock:
                    committed_out.append(text)
                sys.stdout.write("\r" + text + "\n")
                sys.stdout.flush()
            continue

        if mtype in (
            "error",
            "auth_error",
            "quota_exceeded",
            "rate_limited",
            "commit_throttled",
            "queue_overflow",
            "resource_exhausted",
            "session_time_limit_exceeded",
            "input_error",
            "chunk_size_exceeded",
            "insufficient_audio_activity",
            "transcriber_error",
            "unaccepted_terms",
        ):
            err = msg.get("error", "Unknown error")
            sys.stdout.write(f"\n[elevenlabs:{mtype}] {err}\n")
            sys.stdout.flush()
            continue


async def _sender(
    ws,
    audio_q: "queue.Queue[np.ndarray]",
    cfg: AudioConfig,
) -> None:
    loop = asyncio.get_running_loop()
    while True:
        # Pull audio from the thread-safe queue without blocking the event loop.
        chunk = await loop.run_in_executor(None, audio_q.get)
        if chunk is None:  # type: ignore[comparison-overlap]
            return

        payload = {
            "message_type": "input_audio_chunk",
            "audio_base_64": _b64_pcm16le(chunk),
            "commit": False,
            "sample_rate": cfg.sample_rate,
        }
        await ws.send(json.dumps(payload))


def _start_mic_stream(audio_q: "queue.Queue[np.ndarray]", cfg: AudioConfig) -> sd.InputStream:
    def callback(indata, frames, time, status):  # noqa: ANN001
        if status:
            # Non-fatal; keep streaming.
            pass
        # indata is float32 in [-1, 1]. Convert to int16 PCM.
        mono = indata[:, 0] if indata.ndim == 2 else indata
        clipped = np.clip(mono, -1.0, 1.0)
        audio_i16 = (clipped * 32767.0).astype(np.int16)
        audio_q.put(audio_i16)

    return sd.InputStream(
        samplerate=cfg.sample_rate,
        channels=cfg.channels,
        dtype="float32",
        blocksize=cfg.blocksize,
        callback=callback,
    )


async def run_realtime_transcription(
    *,
    # ElevenLabs Realtime STT guide uses Scribe Realtime v2.
    # https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/server-side-streaming
    model_id: str = "scribe_v2_realtime",
    language_code: Optional[str] = None,
    include_timestamps: bool = False,
    include_language_detection: bool = False,
    commit_strategy: str = "vad",
    vad_silence_threshold_secs: float = 1.0,
    vad_threshold: float = 0.4,
    min_speech_duration_ms: int = 100,
    min_silence_duration_ms: int = 100,
    enable_logging: bool = True,
    transcript_path: Optional[str] = None,
    flush_interval_secs: float = 10.0,
) -> None:
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY in environment (.env).")

    cfg = AudioConfig()
    audio_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=64)

    qs = {
        "model_id": model_id,
        # Optional; default is pcm_16000, but we set explicitly to match our mic stream.
        "audio_format": "pcm_16000",
        "include_timestamps": include_timestamps,
        "include_language_detection": include_language_detection,
        "commit_strategy": commit_strategy,
        "vad_silence_threshold_secs": str(vad_silence_threshold_secs),
        "vad_threshold": str(vad_threshold),
        "min_speech_duration_ms": min_speech_duration_ms,
        "min_silence_duration_ms": min_silence_duration_ms,
        "enable_logging": enable_logging,
    }
    if language_code:
        qs["language_code"] = language_code

    url = f"{ELEVENLABS_REALTIME_WS_URL}?{urlencode(qs)}"

    headers = {"xi-api-key": api_key}

    committed: list[str] = []
    committed_lock = asyncio.Lock()
    stop_event = asyncio.Event()

    out_path = Path(transcript_path) if transcript_path else _default_transcript_path()
    writer_task = asyncio.create_task(
        _transcript_writer(
            committed=committed,
            committed_lock=committed_lock,
            out_path=out_path,
            stop_event=stop_event,
            flush_interval_secs=flush_interval_secs,
        )
    )
    sys.stdout.write(f"Transcript file: {out_path}\n")
    sys.stdout.flush()

    try:
        async with websockets.connect(
            url, additional_headers=headers, ping_interval=20, ping_timeout=20
        ) as ws:
            # Wait for the initial session message before sending audio.
            # The ElevenLabs examples expect a `session_started` event before sending chunks.
            try:
                first = await asyncio.wait_for(ws.recv(), timeout=10.0)
                try:
                    data = json.loads(first)
                except json.JSONDecodeError:
                    data = {"message_type": "unknown", "raw": first}
                if isinstance(data, dict) and data.get("message_type") == "session_started":
                    cfg0 = data.get("config", {})
                    _print_partial(
                        f"[elevenlabs] session started (model_id={cfg0.get('model_id')})"
                    )
                else:
                    sys.stdout.write(f"[elevenlabs] first message: {data}\n")
                    sys.stdout.flush()
            except asyncio.TimeoutError:
                sys.stdout.write("[elevenlabs] timed out waiting for session_started\n")
                sys.stdout.flush()

            recv_task = asyncio.create_task(_receiver(ws, committed, committed_lock))
            send_task = asyncio.create_task(_sender(ws, audio_q, cfg))

            with _start_mic_stream(audio_q, cfg):
                sys.stdout.write("Listening… speak into your mic. Press Ctrl+C to stop.\n")
                sys.stdout.flush()
                await asyncio.gather(recv_task, send_task)
    except (asyncio.CancelledError, KeyboardInterrupt):
        # Allow graceful shutdown and final flush.
        raise
    finally:
        # Stop sender.
        try:
            audio_q.put(None)  # type: ignore[arg-type]
        except Exception:
            pass

        # Tell writer to flush and stop.
        stop_event.set()
        try:
            await writer_task
        except Exception:
            pass

        sys.stdout.write(f"\nSaved transcript to: {out_path}\n")
        sys.stdout.flush()


def main() -> None:
    try:
        asyncio.run(run_realtime_transcription())
    except KeyboardInterrupt:
        # `run_realtime_transcription` writes the transcript after the websocket context exits.
        sys.stdout.write("\nStopping…\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

