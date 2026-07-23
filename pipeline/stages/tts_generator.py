import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# pyrefly: ignore [missing-import]
import edge_tts

# pyrefly: ignore [missing-import]
from elevenlabs.client import ElevenLabs

from services.ffmpeg_service import FFmpegService


class TTSGenerator:
    """
    Generates Hindi TTS audio for translated dialogue segments.

    Supported providers:
        1. ElevenLabs
        2. Local Clone (XTTS/Chatterbox)
        3. Edge-TTS

    ElevenLabs is used by default if:
        - provider="elevenlabs"
        - ELEVENLABS_API_KEY exists

    Otherwise, the system automatically falls back to Edge-TTS.
    """

    def __init__(
        self,
        provider: str = "elevenlabs",
        voice: str = "hi-IN-MadhurNeural",
        default_elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL",
    ):
        self.provider = provider.lower().strip()

        # Edge-TTS voice
        self.voice = voice

        # ElevenLabs voice fallback
        self.default_elevenlabs_voice_id = default_elevenlabs_voice_id

        # ElevenLabs client
        self.client: Optional[ElevenLabs] = None

        # Read API key from environment
        self.elevenlabs_api_key = os.getenv(
            "ELEVENLABS_API_KEY"
        )

        # ------------------------------------------------------
        # Initialize ElevenLabs
        # ------------------------------------------------------

        if self.provider == "elevenlabs":

            if self.elevenlabs_api_key:

                try:

                    self.client = ElevenLabs(
                        api_key=self.elevenlabs_api_key
                    )

                    print(
                        "ElevenLabs TTS initialized successfully."
                    )

                except Exception as e:

                    print(
                        f"Failed to initialize ElevenLabs: {e}"
                    )

                    print(
                        "Falling back to Edge-TTS."
                    )

                    self.provider = "edge-tts"

            else:

                print(
                    "Warning: ELEVENLABS_API_KEY not found."
                )

                print(
                    "Falling back to Edge-TTS."
                )

                self.provider = "edge-tts"

        # ------------------------------------------------------
        # Initialize Local Clone
        # ------------------------------------------------------
        
        elif self.provider == "local_clone":
            print("Initializing Local Voice Clone (XTTSv2)...")
            try:
                # pyrefly: ignore [missing-import]
                from TTS.api import TTS
                # We load XTTSv2 which is capable of zero-shot voice cloning
                self.local_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
                print("Local Voice Clone model loaded successfully.")
            except ImportError:
                print("=====================================================")
                print("ERROR: Coqui TTS is not installed or not supported on this Python version.")
                print("Please downgrade to Python 3.11 and run: pip install TTS")
                print("Falling back to Edge-TTS.")
                print("=====================================================")
                self.provider = "edge-tts"

        # ------------------------------------------------------
        # Validate provider
        # ------------------------------------------------------

        elif self.provider != "edge-tts":

            print(
                f"Unknown TTS provider: {self.provider}"
            )

            print(
                "Falling back to Edge-TTS."
            )

            self.provider = "edge-tts"

        print(
            f"Active TTS provider: {self.provider}"
        )

    # ==========================================================
    # EDGE-TTS GENERATION
    # ==========================================================

    async def generate_segment_edge(
        self,
        text: str,
        output_path: Path
    ):
        """
        Generate Hindi speech using Microsoft Edge-TTS.
        """

        if not text.strip():

            raise ValueError(
                "Cannot generate TTS for empty text."
            )

        # Make sure directory exists

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print(
            f"Generating Edge-TTS: "
            f"{text[:60]}"
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice
        )

        await communicate.save(
            str(output_path)
        )

        # Validate generated file

        if not output_path.exists():

            raise RuntimeError(
                f"Edge-TTS failed to create file: "
                f"{output_path}"
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                f"Edge-TTS created an empty file: "
                f"{output_path}"
            )

    # ==========================================================
    # ELEVENLABS GENERATION
    # ==========================================================

    def generate_segment_elevenlabs(
        self,
        text: str,
        output_path: Path,
        voice_id: str = None
    ):
        """
        Generate Hindi speech using ElevenLabs.
        """
        
        target_voice_id = voice_id if voice_id else self.default_elevenlabs_voice_id

        if self.client is None:

            raise RuntimeError(
                "ElevenLabs client is not initialized. "
                "Check ELEVENLABS_API_KEY."
            )

        if not text.strip():

            raise ValueError(
                "Cannot generate TTS for empty text."
            )

        # Ensure directory exists

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print(
            f"Generating ElevenLabs TTS: "
            f"{text[:60]}"
        )

        # ------------------------------------------------------
        # Generate audio
        #
        # IMPORTANT:
        #
        # Correct parameters:
        #
        # voice_id=
        # model_id=
        #
        # NOT:
        #
        # voice=
        # model=
        # ------------------------------------------------------

        audio_generator = (
            self.client.text_to_speech.convert(

                voice_id=target_voice_id,

                text=text,

                model_id="eleven_multilingual_v2",

                output_format="mp3_44100_128"
            )
        )

        # Write generated MP3 chunks

        with open(
            output_path,
            "wb"
        ) as audio_file:

            for chunk in audio_generator:

                if chunk:

                    audio_file.write(chunk)

        # Validate output

        if not output_path.exists():

            raise RuntimeError(
                f"ElevenLabs failed to create file: "
                f"{output_path}"
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                f"ElevenLabs created an empty file: "
                f"{output_path}"
            )

    # ==========================================================
    # LOCAL CLONE GENERATION
    # ==========================================================

    def generate_segment_local_clone(
        self,
        text: str,
        output_path: Path,
        vocals_path: Path,
        start_time: float,
        end_time: float
    ):
        """
        Generate cloned speech using a local model (XTTS).
        Extracts a reference chunk from the vocals file.
        """
        if not hasattr(self, "local_tts"):
            raise RuntimeError("Local TTS model is not loaded.")
            
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Extract reference audio
        duration = end_time - start_time
        if duration < 1.0:
            # Need at least 1 second for reference, grab a slightly wider window if possible
            duration = 2.0
            
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_ref:
            ref_path = temp_ref.name
            
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(vocals_path),
                "-ss", str(max(0, start_time - 0.5)), "-t", str(min(duration, 10.0)),
                "-ac", "1", "-ar", "22050",
                ref_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"Generating Local Clone TTS: {text[:60]}")
            
            # 2. Generate speech
            self.local_tts.tts_to_file(
                text=text,
                speaker_wav=ref_path,
                language="hi",
                file_path=str(output_path)
            )
            
        finally:
            if os.path.exists(ref_path):
                os.remove(ref_path)

    # ==========================================================
    # GENERATE SINGLE SEGMENT
    # ==========================================================

    def generate_segment(
        self,
        text: str,
        output_path: Path,
        voice_id: str = None,
        vocals_path: Path = None,
        start_time: float = 0.0,
        end_time: float = 0.0
    ):
        """
        Generate one TTS segment using the selected provider.

        If ElevenLabs fails, automatically try Edge-TTS.
        """

        if self.provider == "elevenlabs":

            try:

                self.generate_segment_elevenlabs(
                    text=text,
                    output_path=output_path,
                    voice_id=voice_id
                )

                return

            except Exception as e:

                print(
                    f"ElevenLabs TTS failed: {e}"
                )

                print(
                    "Trying Edge-TTS fallback..."
                )

        elif self.provider == "local_clone":
            try:
                self.generate_segment_local_clone(
                    text=text,
                    output_path=output_path,
                    vocals_path=vocals_path,
                    start_time=start_time,
                    end_time=end_time
                )
                return
            except Exception as e:
                print(f"Local Clone TTS failed: {e}")
                print("Trying Edge-TTS fallback...")

        # ------------------------------------------------------
        # Edge-TTS
        # ------------------------------------------------------

        try:

            asyncio.run(
                self.generate_segment_edge(
                    text=text,
                    output_path=output_path
                )
            )

        except RuntimeError:

            # This handles cases where an event loop
            # already exists.

            loop = asyncio.new_event_loop()

            try:

                loop.run_until_complete(
                    self.generate_segment_edge(
                        text=text,
                        output_path=output_path
                    )
                )

            finally:

                loop.close()

    # ==========================================================
    # PROCESS COMPLETE TIMELINE
    # ==========================================================

    def process_timeline(
        self,
        timeline_path: Path,
        tts_dir: Path,
        output_timeline_path: Path,
        vocals_path: Path = None
    ):
        """
        Generate Hindi TTS for every translated dialogue segment.

        INPUT:

            hindi_translation.json

        Example segment:

            {
                "segment_id": 0,
                "start": 1.20,
                "end": 3.50,
                "source_text": "Hello everyone",
                "translated_text": "सभी को नमस्ते"
            }

        OUTPUT FILES:

            segment_0000.mp3
            segment_0001.mp3
            segment_0002.mp3

        OUTPUT TIMELINE:

            tts_timeline.json
        """

        print(
            "Starting TTS generation..."
        )

        print(
            f"TTS provider: {self.provider}"
        )

        # ------------------------------------------------------
        # Ensure directories exist
        # ------------------------------------------------------

        tts_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_timeline_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # ------------------------------------------------------
        # Validate timeline
        # ------------------------------------------------------

        if not timeline_path.exists():

            raise FileNotFoundError(
                f"Translation timeline not found: "
                f"{timeline_path}"
            )

        # ------------------------------------------------------
        # Load timeline
        # ------------------------------------------------------

        with open(
            timeline_path,
            "r",
            encoding="utf-8"
        ) as file:

            timeline = json.load(file)

        if not isinstance(
            timeline,
            list
        ):

            raise ValueError(
                "Timeline JSON must contain a list "
                "of dialogue segments."
            )

        print(
            f"Found {len(timeline)} "
            f"timeline segments."
        )

        completed_segments = 0

        skipped_segments = 0

        failed_segments = 0

        # ======================================================
        # PROCESS SEGMENTS
        # ======================================================

        for index, segment in enumerate(
            timeline
        ):

            # --------------------------------------------------
            # Segment ID
            # --------------------------------------------------

            segment_id = segment.get(
                "segment_id",
                index
            )

            # --------------------------------------------------
            # Get translated Hindi text
            # --------------------------------------------------

            text = str(
                segment.get(
                    "translated_text",
                    ""
                )
            ).strip()

            # --------------------------------------------------
            # Skip empty translations
            # --------------------------------------------------

            if not text:

                print(
                    f"Skipping segment "
                    f"{segment_id}: "
                    f"empty translated text."
                )

                segment[
                    "status"
                ] = "tts_skipped"

                skipped_segments += 1

                continue

            # --------------------------------------------------
            # IMPORTANT
            #
            # ElevenLabs output format is MP3. Local Clone is WAV.
            # 
            # We'll use .wav as the default container and let FFmpeg
            # figure it out during mixing if it's MP3 disguised as WAV.
            # --------------------------------------------------

            audio_filename = (
                f"segment_"
                f"{int(segment_id):04d}.wav"
            )

            audio_path = (
                tts_dir /
                audio_filename
            )

            print()

            print(
                "----------------------------------------"
            )

            print(
                f"Processing TTS segment "
                f"{segment_id}"
            )

            print(
                f"Text: {text[:100]}"
            )

            # --------------------------------------------------
            # Calculate original dialogue duration
            # --------------------------------------------------

            start_time = float(
                segment.get(
                    "start",
                    0
                )
            )

            end_time = float(
                segment.get(
                    "end",
                    start_time
                )
            )

            target_duration = max(
                0,
                end_time - start_time
            )

            # --------------------------------------------------
            # Get assigned voice ID
            # --------------------------------------------------
            assigned_voice_id = segment.get("elevenlabs_voice_id")

            # --------------------------------------------------
            # Generate speech
            # --------------------------------------------------

            try:

                self.generate_segment(
                    text=text,
                    output_path=audio_path,
                    voice_id=assigned_voice_id,
                    vocals_path=vocals_path,
                    start_time=start_time,
                    end_time=end_time
                )

                # --------------------------------------------------
                # Verify generated file
                # --------------------------------------------------

                if not audio_path.exists():

                    raise RuntimeError(
                        "TTS output file was not created."
                    )

                if audio_path.stat().st_size == 0:

                    raise RuntimeError(
                        "TTS output file is empty."
                    )

                # --------------------------------------------------
                # Get actual TTS duration
                # --------------------------------------------------

                tts_duration = (
                    FFmpegService.get_duration(
                        audio_path
                    )
                )

                # --------------------------------------------------
                # Update timeline
                # --------------------------------------------------

                segment[
                    "tts_audio"
                ] = audio_filename

                segment[
                    "tts_duration"
                ] = tts_duration

                segment[
                    "target_duration"
                ] = target_duration

                segment[
                    "tts_provider"
                ] = self.provider

                segment[
                    "status"
                ] = "tts_completed"

                completed_segments += 1

                print(
                    f"TTS completed."
                )

                print(
                    f"Target duration: "
                    f"{target_duration:.2f}s"
                )

                print(
                    f"Generated duration: "
                    f"{tts_duration:.2f}s"
                )

                # --------------------------------------------------
                # Timing warning
                # --------------------------------------------------

                if (
                    target_duration > 0
                    and
                    tts_duration > target_duration
                ):

                    difference = (
                        tts_duration -
                        target_duration
                    )

                    print(
                        f"Timing warning: "
                        f"TTS is "
                        f"{difference:.2f}s "
                        f"longer than target."
                    )

            except Exception as e:

                failed_segments += 1

                segment[
                    "status"
                ] = "tts_failed"

                segment[
                    "tts_error"
                ] = str(e)

                print(
                    f"TTS failed for segment "
                    f"{segment_id}: {e}"
                )

                # Re-raise because a missing dialogue
                # segment can break final dubbing quality.

                raise

        # ======================================================
        # SAVE UPDATED TIMELINE
        # ======================================================

        with open(
            output_timeline_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                timeline,
                file,
                ensure_ascii=False,
                indent=2
            )

        # ======================================================
        # SUMMARY
        # ======================================================

        print()

        print(
            "========================================"
        )

        print(
            "TTS GENERATION SUMMARY"
        )

        print(
            "========================================"
        )

        print(
            f"Completed: {completed_segments}"
        )

        print(
            f"Skipped:   {skipped_segments}"
        )

        print(
            f"Failed:    {failed_segments}"
        )

        print(
            f"Timeline:  {output_timeline_path}"
        )

        print(
            "========================================"
        )

        return timeline