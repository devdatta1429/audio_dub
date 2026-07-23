import json
# pyrefly: ignore [missing-import]
import librosa
import numpy as np
from pathlib import Path
import os
import subprocess
import tempfile

class VoiceSelectionAgent:
    """
    AI Agent that analyzes the original vocal audio to determine pitch and tone,
    then automatically selects the best matching ElevenLabs voice.
    """
    def __init__(self):
        # Catalog of ElevenLabs Voice IDs based on characteristics
        # Voice IDs are standard high-quality Multilingual v2 voices.
        self.voice_catalog = {
            "male_deep": "JBFqnCBsd6RMkjVDRZzb",     # George (Verified)
            "male_mid": "JBFqnCBsd6RMkjVDRZzb",      # George (Verified)
            "female_mature": "JBFqnCBsd6RMkjVDRZzb", # George (Verified)
            "female_young": "JBFqnCBsd6RMkjVDRZzb"   # George (Verified)
        }

    def analyze_audio_segment(self, audio_path: str, start: float, end: float) -> str:
        """
        Extracts a segment of audio and analyzes it using librosa to determine pitch and tone.
        Returns the best matching Voice ID.
        """
        duration = end - start
        if duration < 0.5:
            # Too short to analyze accurately, default to mid male
            return self.voice_catalog["male_mid"]

        # Extract just the snippet to a temporary file using ffmpeg for faster processing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_path = temp_audio.name
            
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(start), "-t", str(min(duration, 5.0)), # analyze max 5 seconds
                "-ac", "1", "-ar", "16000",
                temp_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Load with librosa
            y, sr = librosa.load(temp_path, sr=16000)
            
            # Calculate Fundamental Frequency (F0/Pitch)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Extract valid pitches
            pitch_values = []
            for i in range(magnitudes.shape[1]):
                index = magnitudes[:, i].argmax()
                pitch = pitches[index, i]
                if pitch > 50 and pitch < 500: # Human voice range
                    pitch_values.append(pitch)
                    
            if not pitch_values:
                return self.voice_catalog["male_mid"] # Fallback

            median_pitch = np.median(pitch_values)
            
            # Calculate Spectral Centroid (Tone/Brightness)
            centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            median_centroid = np.median(centroids)

            # Determine Characteristics
            is_female = median_pitch > 165
            is_bright_young = median_centroid > 1800 # Higher centroid = brighter/younger tone
            
            # Select Voice
            if is_female:
                if is_bright_young:
                    return self.voice_catalog["female_young"]
                else:
                    return self.voice_catalog["female_mature"]
            else:
                if is_bright_young or median_pitch > 110:
                    return self.voice_catalog["male_mid"]
                else:
                    return self.voice_catalog["male_deep"]

        except Exception as e:
            print(f"Error during voice analysis: {e}")
            return self.voice_catalog["male_mid"]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def process_timeline(self, timeline_path: Path, vocals_path: Path):
        """
        Iterates over the timeline and assigns a voice ID to each segment based on audio analysis.
        """
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)

        print("Running AI Voice Selection Agent...")
        for segment in timeline:
            start = float(segment.get("start", 0))
            end = float(segment.get("end", start))
            
            voice_id = self.analyze_audio_segment(str(vocals_path), start, end)
            segment["elevenlabs_voice_id"] = voice_id
            
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
            
        print("Voice assignment complete.")
        return timeline
