import subprocess
import json
import os
from pathlib import Path
from services.ffmpeg_service import FFmpegService

class TimingOptimizer:
    def __init__(self):
        pass

    def optimize_timeline(self, timeline_path: Path, tts_dir: Path, output_timeline_path: Path):
        """
        Adjusts the speed of TTS segments to match original duration.
        Creates new optimized audio files and updates the timeline.
        """
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)

        optimized_dir = tts_dir / "optimized"
        optimized_dir.mkdir(exist_ok=True)

        for segment in timeline:
            tts_info = segment.get("tts", {})
            if not tts_info or not tts_info.get("audio"):
                # Support legacy flat format if it exists
                if not segment.get("tts_audio"):
                    continue
                audio_filename = segment["tts_audio"]
            else:
                audio_filename = tts_info["audio"]

            audio_path = tts_dir / audio_filename
            
            original_duration = segment["duration"]
            tts_duration = FFmpegService.get_duration(audio_path)
            
            if tts_duration == 0:
                continue

            optimized_filename = f"opt_{audio_filename}"
            optimized_path = optimized_dir / optimized_filename

            # Calculate the speed ratio needed
            # atempo = speed ratio. 1.0 is normal, 2.0 is 2x faster, 0.5 is 2x slower.
            # If TTS is 4 seconds and original is 2 seconds, we need it to be 2x faster (ratio = 4.0 / 2.0 = 2.0).
            ratio = tts_duration / original_duration

            # FFmpeg atempo filter accepts values between 0.5 and 100.0.
            # If ratio is outside this, we clamp it (or use multiple atempo filters, but clamping is safer for audio quality).
            # We don't want to slow down too much (e.g., if ratio < 0.8), we'll just keep it natural.
            # We mostly care about speeding up when TTS is too long.
            
            if ratio > 1.05: # Only compress if TTS is at least 5% longer
                speed_ratio = min(ratio, 2.5) # Don't speed up more than 2.5x
                cmd = [
                    "ffmpeg", "-y", "-i", str(audio_path),
                    "-filter:a", f"atempo={speed_ratio}",
                    str(optimized_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if "tts" in segment:
                    segment["tts"]["audio"] = f"optimized/{optimized_filename}"
                    segment["tts"]["duration"] = FFmpegService.get_duration(optimized_path)
                else:
                    segment["tts_audio"] = f"optimized/{optimized_filename}"
                    segment["tts_duration"] = FFmpegService.get_duration(optimized_path)
            else:
                # If it fits or is shorter, we just use the original TTS audio
                if "tts" in segment:
                    segment["tts"]["duration"] = tts_duration
                else:
                    segment["tts_duration"] = tts_duration

            segment["status"] = "timing_optimized"

        with open(output_timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)

        return timeline
