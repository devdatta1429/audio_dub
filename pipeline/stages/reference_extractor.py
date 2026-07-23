import json
import os
import subprocess
from pathlib import Path

# Try importing the existing VoiceSelectionAgent from our project
try:
    from pipeline.stages.voice_selector import VoiceSelectionAgent
except ImportError:
    VoiceSelectionAgent = None

class ReferenceExtractor:
    """
    Analyzes the transcribed timeline and extracts a clean reference snippet
    for each distinct speaker, then determines their gender using VoiceSelectionAgent.
    """
    def __init__(self):
        self.voice_agent = VoiceSelectionAgent() if VoiceSelectionAgent else None

    def extract_references(self, timeline_path: Path, vocals_path: Path, ref_out_dir: Path):
        """
        Creates a 'references' folder, extracts audio clips per speaker, and updates the timeline.
        """
        print("Running Reference Extractor...")
        ref_out_dir.mkdir(parents=True, exist_ok=True)
        
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)

        # Build a dictionary of the longest segment per speaker
        # Format: { "SPEAKER_00": {"start": 0, "end": 5}, ... }
        best_segments = {}
        for segment in timeline:
            speaker_id = segment.get("speaker", {}).get("id", "SPEAKER_00")
            if type(segment.get("speaker")) is str:
                # Handle old format if it crept in
                speaker_id = segment["speaker"]
                segment["speaker"] = {"id": speaker_id}
                
            start = float(segment.get("start", 0))
            end = float(segment.get("end", start))
            duration = end - start
            
            # We want the longest clear segment, but cap it around 10s for XTTS
            if duration > 1.0:
                if speaker_id not in best_segments:
                    best_segments[speaker_id] = {"start": start, "end": end, "duration": duration}
                elif duration > best_segments[speaker_id]["duration"] and best_segments[speaker_id]["duration"] < 8.0:
                    best_segments[speaker_id] = {"start": start, "end": end, "duration": duration}

        # For each distinct speaker, extract their reference audio
        speaker_data = {}
        for speaker_id, times in best_segments.items():
            start = times["start"]
            end = times["end"]
            duration = min(times["duration"], 10.0) # Cap at 10s
            
            # Create a clean reference wav
            ref_path = ref_out_dir / f"{speaker_id}_reference.wav"
            
            cmd = [
                "ffmpeg", "-y", "-i", str(vocals_path),
                "-ss", str(max(0, start)), "-t", str(duration),
                "-ac", "1", "-ar", "22050",
                str(ref_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Analyze gender using our existing librosa logic (if available)
            gender = "unknown"
            if self.voice_agent:
                # analyze_audio_segment returns a voice ID from catalog, let's reverse engineer it
                voice_id = self.voice_agent.analyze_audio_segment(str(vocals_path), start, end)
                if voice_id in [self.voice_agent.voice_catalog.get("female_young"), self.voice_agent.voice_catalog.get("female_mature")]:
                    gender = "female"
                else:
                    gender = "male"
            
            speaker_data[speaker_id] = {
                "reference_path": str(ref_path.resolve()),
                "gender": gender
            }
            print(f"Extracted {speaker_id} ({gender}) -> {ref_path.name}")

        # Update the timeline with the extracted references
        for segment in timeline:
            speaker_id = segment.get("speaker", {}).get("id", "SPEAKER_00")
            data = speaker_data.get(speaker_id)
            if data:
                segment["speaker"]["gender"] = data["gender"]
                segment["voice_reference"] = data["reference_path"]
                
            # Ensure new format TTS block exists
            if "tts" not in segment:
                segment["tts"] = {
                    "provider": "pending",
                    "language": "hi",
                    "audio": "",
                    "duration": None
                }

        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)

        print("Reference Extraction complete.")
        return timeline
