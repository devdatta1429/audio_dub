import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="XTTS Worker for AudioDub")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--reference", required=True, help="Path to reference audio file")
    parser.add_argument("--output", required=True, help="Path to output audio file")
    parser.add_argument("--language", default="hi", help="Language code")
    
    args = parser.parse_args()
    
    try:
        from TTS.api import TTS
    except ImportError:
        print("ERROR: TTS library not found. Are you running this in the .venv-xtts environment?")
        sys.exit(1)
        
    print(f"XTTS Worker: Loading model for {args.language}...")
    # Initialize TTS (will use cached model)
    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        progress_bar=False,
        gpu=False
    )
    
    print(f"XTTS Worker: Generating audio...")
    # Generate
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.reference,
        language=args.language,
        file_path=args.output
    )
    
    print(f"XTTS Worker: Success. Saved to {args.output}")

if __name__ == "__main__":
    main()
