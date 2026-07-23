import subprocess
from pathlib import Path
import json

class FFmpegService:
    @staticmethod
    def extract_audio(video_path: Path, output_audio_path: Path):
        """Extract original audio from the video as WAV."""
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path), 
            "-q:a", "0", "-map", "a", str(output_audio_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_audio_path

    @staticmethod
    def get_duration(file_path: Path) -> float:
        """Get the duration of an audio or video file in seconds."""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", str(file_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0

    @staticmethod
    def mix_audio(background_path: Path, dialogue_path: Path, output_path: Path):
        """Mix background audio and dialogue audio with sidechain compression (ducking)."""
        # [0:a] is background, [1:a] is dialogue
        # sidechaincompress ducks [0:a] based on the volume of [1:a]
        # Then we amix the ducked background with the original dialogue
        filter_complex = (
            "[0:a][1:a]sidechaincompress=threshold=0.05:ratio=4.0:attack=5:release=200[bg];"
            "[bg][1:a]amix=inputs=2:duration=longest:dropout_transition=2[out]"
        )
        
        cmd = [
            "ffmpeg", "-y", 
            "-i", str(background_path), 
            "-i", str(dialogue_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    @staticmethod
    def render_video(video_path: Path, audio_path: Path, output_path: Path):
        """Combine original video with new mixed audio."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",   # don't re-encode video
            "-c:a", "aac",    # encode audio to aac
            "-map", "0:v:0",  # use video from first input
            "-map", "1:a:0",  # use audio from second input
            "-shortest",      # finish encoding when the shortest input stream ends
            str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
