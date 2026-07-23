import os
import shutil
from pathlib import Path
from services.file_service import FileService
from services.ffmpeg_service import FFmpegService
from pipeline.stages.transcriber import Transcriber
from pipeline.stages.translator import TranslatorService
from pipeline.stages.reference_extractor import ReferenceExtractor
from pipeline.stages.tts_generator import TTSGenerator
from pipeline.stages.timing_optimizer import TimingOptimizer
from pipeline.stages.audio_aligner import AudioAligner
from pipeline.stages.source_separator import SourceSeparator

class DubbingPipeline:
    def __init__(self, project_id=None):
        self.file_service = FileService(project_id)
        self.file_service.setup_project_directories()
        
    def run_phase_1(self, video_path: Path, tts_provider: str = "elevenlabs"):
        """Runs the pipeline including Source Separation."""
        print(f"Starting pipeline for project {self.file_service.project_id}")
        
        # 1. Save uploaded file
        input_video = self.file_service.save_uploaded_file(video_path, video_path.name)
        print("Video saved.")
        
        # 2. Extract Audio
        audio_path = self.file_service.get_path("audio", "original.wav")
        FFmpegService.extract_audio(input_video, audio_path)
        print("Audio extracted.")
        
        # 2b. Separate Audio (Demucs)
        separator = SourceSeparator()
        demucs_out_dir = self.file_service.dirs["audio"] / "demucs_output"
        print("Running Source Separation (this may take a few minutes)...")
        vocals_path, background_path = separator.separate(audio_path, demucs_out_dir)
        print("Source Separation complete.")

        # Copy background and vocals to standard paths
        final_background_path = self.file_service.get_path("audio", "background.wav")
        final_vocals_path = self.file_service.get_path("audio", "vocals.wav")
        shutil.copy(background_path, final_background_path)
        shutil.copy(vocals_path, final_vocals_path)
        
        # 3. Transcribe (Whisper) using vocals only
        transcriber = Transcriber()
        timeline_path = self.file_service.get_path("transcript", "master_timeline.json")
        transcriber.transcribe(final_vocals_path, timeline_path)
        print("Transcription complete.")
        
        # 3b. Extract References & Analyze Gender
        ref_extractor = ReferenceExtractor()
        ref_dir = self.file_service.dirs["audio"] / "references"
        ref_extractor.extract_references(timeline_path, final_vocals_path, ref_dir)
        
        # 4. Translate
        translator = TranslatorService()
        translated_timeline_path = self.file_service.get_path("translation", "hindi_translation.json")
        translator.translate_timeline(timeline_path, translated_timeline_path)
        print("Translation complete.")
            
        # 5. TTS Generator
        tts_generator = TTSGenerator(provider=tts_provider)
        tts_dir = self.file_service.dirs["tts"]
        tts_timeline_path = self.file_service.get_path("tts", "tts_timeline.json")
        tts_generator.process_timeline(translated_timeline_path, tts_dir, tts_timeline_path, vocals_path=final_vocals_path)
        print("TTS Generation complete.")
        
        # 5b. Timing Optimization (Output 8)
        optimizer = TimingOptimizer()
        optimized_timeline_path = self.file_service.get_path("tts", "optimized_timeline.json")
        optimizer.optimize_timeline(tts_timeline_path, tts_dir, optimized_timeline_path)
        print("Timing optimization complete.")
        
        # 6. Audio Aligner
        aligner = AudioAligner()
        hindi_dialogue_path = self.file_service.get_path("final_audio", "hindi_dialogue.wav")
        aligner.create_dialogue_track(optimized_timeline_path, tts_dir, hindi_dialogue_path)
        print("Audio alignment complete.")
        
        # 7. Mix Audio (Background + Hindi Dialogue)
        final_mix_path = self.file_service.get_path("final_audio", "final_mix.wav")
        FFmpegService.mix_audio(final_background_path, hindi_dialogue_path, final_mix_path)
        print("Audio Mixing complete.")
        
        # 8. Render Video
        output_video = self.file_service.get_path("output", "final_hindi_dubbed_video.mp4")
        FFmpegService.render_video(input_video, final_mix_path, output_video)
        print(f"Pipeline complete! Output video: {output_video}")
        
        return output_video
