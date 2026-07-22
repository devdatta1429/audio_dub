import streamlit as st
import tempfile
from pathlib import Path
import os
import sys

# Add root directory to path to allow absolute imports
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

from pipeline.dubbing_pipeline import DubbingPipeline

st.set_page_config(page_title="AI Video Dubbing", page_icon="🎬", layout="wide")

st.title("🎬 AI-Based English-to-Hindi Video Dubbing")

st.markdown("Upload an English video, and receive a Hindi-dubbed version!")

uploaded_file = st.file_uploader("Upload English Video (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Source Language", ["English"])
        st.selectbox("Target Language", ["Hindi"])
    with col2:
        st.selectbox("Text Source", ["Auto (Whisper)"])
        st.selectbox("TTS Provider", ["Edge-TTS (Local)"])

    if st.button("Start Dubbing", type="primary"):
        with st.spinner("Processing video... This may take a few minutes depending on the video length."):
            # Save uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_video_path = Path(tmp_file.name)
            
            try:
                pipeline = DubbingPipeline()
                output_video_path = pipeline.run_phase_1(tmp_video_path)
                
                st.success("Dubbing Complete!")
                st.video(str(output_video_path))
                
                with open(output_video_path, "rb") as file:
                    btn = st.download_button(
                        label="Download Dubbed Video",
                        data=file,
                        file_name="hindi_dubbed_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"An error occurred during dubbing: {str(e)}")
            finally:
                if tmp_video_path.exists():
                    os.remove(tmp_video_path)
