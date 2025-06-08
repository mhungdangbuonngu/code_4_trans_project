import streamlit as st
import requests
import time
import tempfile
import os
import base64

st.set_page_config(page_title="🎬 Video Transcription", layout="centered")
st.title("🎥 Video Transcription with Subtitles")

# File uploader for MP4 video
video_file = st.file_uploader("Upload an MP4 video", type=["mp4"])
language = st.selectbox("Select language of the video",["English","France"])
lang_code = "eng" if language == "English" else "fra"
if st.button("Transcribe"):
    if video_file is None:
        st.error("Please upload a video file.")
    else:
        # Save uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(video_file.read())
            tmp_video_path = tmp_video.name

        st.info("Uploading and transcribing...")
        progress_bar = st.progress(0)

        try:
            # Send video file to transcription API
            with open(tmp_video_path, "rb") as f:
                files = {"file": f}
                data = {"language": lang_code}
                response = requests.post("http://localhost:5000/transcribe", files=files, data=data)

            # Simulate progress
            for i in range(10, 100, 10):
                progress_bar.progress(i)
                time.sleep(0.05)

            if response.status_code == 200:
                transcription_data = response.json()
                progress_bar.progress(100)
                st.success("Transcription completed.")

                # Generate VTT subtitle content
                vtt_content = "WEBVTT\n\n"
                for i, seg in enumerate(transcription_data):
                    start = time.strftime('%H:%M:%S.000', time.gmtime(seg["start"]))
                    end = time.strftime('%H:%M:%S.000', time.gmtime(seg["end"]))
                    vtt_content += f"{i+1}\n{start} --> {end}\n{seg['text']}\n\n"

                # Encode video and VTT in base64
                video_file.seek(0)  # Reset file pointer to start
                video_data = video_file.read()
                video_b64 = base64.b64encode(video_data).decode("utf-8")
                vtt_b64 = base64.b64encode(vtt_content.encode("utf-8")).decode("utf-8")

                # Display transcript
                st.markdown("### 🔊 Transcript")
                for seg in transcription_data:
                    st.markdown(f"**[{seg['start']}s - {seg['end']}s]:** {seg['text']}")

                # Display video with subtitles
                st.markdown("### 🎞️ Video with Subtitles")
                subtitle_label = "French" if lang_code == "fra" else "English"
                subtitle_lang = "fr" if lang_code == "fra" else "en"
                video_html = f"""
                <video width="700" controls>
                    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                    <track src="data:text/vtt;base64,{vtt_b64}" kind="subtitles" srclang="{subtitle_lang}" label="{subtitle_label}" default>
                    Your browser does not support the video tag.
                </video>
                """
                st.components.v1.html(video_html, height=500)

            else:
                st.error(f"Server error: {response.json().get('error', 'Unknown error')}")

        except Exception as e:
            st.error(f"Request failed: {str(e)}")

        finally:
            # Clean up temporary files
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)