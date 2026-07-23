from pathlib import Path
# pyrefly: ignore [missing-import]
from TTS.api import TTS

# Existing vocals extracted by your AudioDub pipeline
speaker_wav = Path(
    r"D:\10\proj\AudioDub\data\projects"
    r"\3bcfd629-4e22-48df-ad33-9be12fff40da"
    r"\audio\vocals.wav"
)

output_file = Path(
    r"D:\10\proj\AudioDub\xtts_test.wav"
)

text = "मैंने उन सभी को खो दिया है जो मेरे लिए मायने रखते हैं      हमारी प्रजा को तैयार करना राजा का कर्तव्य है  परलोक के लिए, मेरे पास मेरा है वकंडा के राजा अंबाकु।"

print("=" * 60)
print("XTTS VOICE CLONING TEST")
print("=" * 60)

# 1. Check reference
print(f"Reference voice: {speaker_wav}")

if not speaker_wav.exists():
    raise FileNotFoundError(
        f"Speaker WAV not found:\n{speaker_wav}"
    )

print("1. Speaker reference FOUND")

# 2. Load XTTS
print("\n2. Loading XTTS model...")

tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=True,
    gpu=False
)

print("3. XTTS MODEL LOADED")

# 3. Clone voice and speak Hindi
print("\n4. Generating cloned Hindi speech...")

tts.tts_to_file(
    text=text,
    speaker_wav=str(speaker_wav),
    language="hi",
    file_path=str(output_file)
)

# 4. Verify
if output_file.exists():
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print(f"Generated: {output_file}")
    print("=" * 60)
else:
    raise RuntimeError("XTTS did not create output audio.")