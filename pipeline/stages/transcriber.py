# pyrefly: ignore [missing-import]
from faster_whisper import WhisperModel
from pathlib import Path
import json

class Transcriber:
    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: Path, output_json_path: Path):
        """Transcribes the audio and saves to JSON."""
        segments, info = self.model.transcribe(str(audio_path), word_timestamps=False, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
        
        result = []
        segment_id = 1
        for segment in segments:
            result.append({
                "segment_id": segment_id,
                "start": segment.start,
                "end": segment.end,
                "duration": segment.end - segment.start,
                "source_text": segment.text.strip(),
                "speaker": "SPEAKER_00", # default for single speaker
                "translated_text": "",
                "tts_audio": "",
                "tts_duration": None,
                "status": "pending"
            })
            segment_id += 1
            
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        return result
