import asyncio
import edge_tts
import json
from pathlib import Path
from services.ffmpeg_service import FFmpegService

class TTSGenerator:
    def __init__(self, voice="hi-IN-MadhurNeural"):
        self.voice = voice

    async def generate_segment(self, text: str, output_path: Path):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))

    def process_timeline(self, timeline_path: Path, tts_dir: Path, output_timeline_path: Path):
        """Generates TTS for all segments in the timeline."""
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)

        for segment in timeline:
            text = segment["translated_text"]
            if not text:
                continue
                
            audio_filename = f"segment_{segment['segment_id']:04d}.wav"
            audio_path = tts_dir / audio_filename
            
            # Run async edge-tts
            asyncio.run(self.generate_segment(text, audio_path))
            
            segment["tts_audio"] = audio_filename
            segment["tts_duration"] = FFmpegService.get_duration(audio_path)
            segment["status"] = "tts_completed"

        with open(output_timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)

        return timeline
