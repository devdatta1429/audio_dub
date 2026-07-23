# pyrefly: ignore [missing-import]
from faster_whisper import WhisperModel
from pathlib import Path
import json
import os

class Transcriber:
    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.hf_token = os.getenv("HF_TOKEN")
        self.pipeline = None
        
        if self.hf_token:
            try:
                from pyannote.audio import Pipeline
                print("Initializing Pyannote Speaker Diarization...")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
            except Exception as e:
                print(f"Warning: Failed to load Pyannote Pipeline: {e}")
                self.pipeline = None

    def _get_speaker_for_time(self, diarization, start_time, end_time):
        """Finds the dominant speaker in a given time window."""
        if not diarization:
            return "SPEAKER_00"
            
        # Find all speakers in this window
        speakers = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Calculate overlap
            overlap_start = max(start_time, turn.start)
            overlap_end = min(end_time, turn.end)
            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                speakers[speaker] = speakers.get(speaker, 0) + overlap_duration
                
        if not speakers:
            return "SPEAKER_00"
            
        # Return speaker with most overlap
        return max(speakers, key=speakers.get)

    def transcribe(self, audio_path: Path, output_json_path: Path):
        """Transcribes the audio, runs diarization (if available), and saves to nested JSON."""
        print("Transcribing audio with Whisper...")
        segments, info = self.model.transcribe(
            str(audio_path), 
            word_timestamps=False, 
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Run diarization if pipeline is loaded
        diarization = None
        if self.pipeline:
            print("Running Pyannote Speaker Diarization...")
            try:
                import torch
                # Suppress FutureWarning from torch.load used by Pyannote
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=FutureWarning)
                    diarization = self.pipeline(str(audio_path))
            except Exception as e:
                print(f"Diarization failed: {e}")
                diarization = None
        
        result = []
        segment_id = 1
        for segment in segments:
            # Determine speaker ID
            speaker_id = self._get_speaker_for_time(diarization, segment.start, segment.end)
            
            result.append({
                "segment_id": segment_id,
                "start": segment.start,
                "end": segment.end,
                "duration": segment.end - segment.start,
                "source_text": segment.text.strip(),
                "translated_text": "",
                "speaker": {
                    "id": speaker_id,
                    "gender": "unknown" # Filled by ReferenceExtractor
                },
                "voice_reference": "", # Filled by ReferenceExtractor
                "tts": {
                    "provider": "pending",
                    "language": "hi",
                    "audio": "",
                    "duration": None
                },
                "status": "pending"
            })
            segment_id += 1
            
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        return result
