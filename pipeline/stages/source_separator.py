import subprocess
from pathlib import Path

class SourceSeparator:
    def __init__(self, model_name="htdemucs"):
        self.model_name = model_name

    def separate(self, audio_path: Path, output_dir: Path):
        """
        Uses Demucs to separate the audio into vocals and background (no vocals).
        """
        # Command: demucs -n htdemucs --two-stems=vocals "audio.wav" -o "output_dir"
        cmd = [
            "demucs", "-n", self.model_name,
            "--two-stems=vocals",
            str(audio_path),
            "-o", str(output_dir)
        ]
        print(f"Running Demucs for separation: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Demucs creates output at: output_dir/htdemucs/original_filename/
        # e.g., output_dir/htdemucs/original/vocals.wav and no_vocals.wav
        base_name = audio_path.stem
        demucs_out_dir = output_dir / self.model_name / base_name
        
        vocals_path = demucs_out_dir / "vocals.wav"
        background_path = demucs_out_dir / "no_vocals.wav"
        
        return vocals_path, background_path
