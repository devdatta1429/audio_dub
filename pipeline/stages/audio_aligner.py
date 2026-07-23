import subprocess
import json
from pathlib import Path

class AudioAligner:
    def __init__(self):
        pass

    def create_dialogue_track(self, timeline_path: Path, tts_dir: Path, output_audio_path: Path):
        """Places each TTS segment at its correct start timestamp."""
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)

        # Create a complex filter string for ffmpeg
        # ffmpeg -i audio1.wav -i audio2.wav -filter_complex "
        # [0]adelay=start1|start1[a0];
        # [1]adelay=start2|start2[a1];
        # [a0][a1]amix=inputs=2[out]
        # " -map "[out]" output.wav
        
        inputs = []
        delays = []
        mix_inputs = []
        
        valid_segments = []
        for s in timeline:
            if s.get("tts", {}).get("audio") or s.get("tts_audio"):
                valid_segments.append(s)
        
        if not valid_segments:
            # Create a silent audio file if no dialogue
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "1", str(output_audio_path)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_audio_path
            
        for i, segment in enumerate(valid_segments):
            audio_filename = segment.get("tts", {}).get("audio") or segment.get("tts_audio")
            audio_file = tts_dir / audio_filename
            inputs.extend(["-i", str(audio_file)])
            
            # Start time in milliseconds
            delay_ms = int(segment["start"] * 1000)
            delays.append(f"[{i}]adelay={delay_ms}|{delay_ms}[a{i}]")
            mix_inputs.append(f"[a{i}]")
            
        # Combine delays
        filter_str = ";".join(delays) + ";"
        # Combine mix
        filter_str += "".join(mix_inputs) + f"amix=inputs={len(valid_segments)}:duration=longest:dropout_transition=0[out]"
        
        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_str, "-map", "[out]", str(output_audio_path)]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_audio_path
