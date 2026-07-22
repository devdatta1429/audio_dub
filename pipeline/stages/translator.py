# pyrefly: ignore [missing-import]
from deep_translator import GoogleTranslator
import json
from pathlib import Path

class TranslatorService:
    def __init__(self):
        self.translator = GoogleTranslator(source='en', target='hi')

    def translate_timeline(self, timeline_path: Path, output_path: Path):
        """Translates all segments in the timeline to Hindi."""
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)
            
        for segment in timeline:
            if segment["source_text"]:
                try:
                    result = self.translator.translate(segment["source_text"])
                    segment["translated_text"] = result if result else segment["source_text"]
                except Exception as e:
                    print(f"Translation error for segment {segment['segment_id']}: {e}")
                    segment["translated_text"] = segment["source_text"] # fallback
                    
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
            
        return timeline
