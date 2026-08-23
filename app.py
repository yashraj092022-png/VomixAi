import streamlit as st
from google import genai
import subprocess
import os

st.set_page_config(page_title="Vomix AI - YouTube Video Editor", page_icon="🎬", layout="centered")

st.title("🎬 Vomix AI - Auto Subtitle & Video Editor")
st.write("यहाँ किसी भी YouTube वीडियो का लिंक डालें:")

# यूजर से यूट्यूब लिंक लेना
video_url = st.text_input("YouTube URL दर्ज करें:", placeholder="https://youtu.be/...")

if st.button("Process Video", type="primary"):
    if video_url:
        with st.spinner("वीडियो प्रोसेस हो रहा है... कृपया प्रतीक्षा करें"):
            try:
                # 1. YouTube वीडियो डाउनलोड
                st.info("1. YouTube वीडियो डाउनलोड हो रहा है...")
                subprocess.run(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" "{video_url}" -o input.mp4', shell=True, check=True)

                # 2. ऑडियो निकालना
                st.info("2. ऑडियो निकाला जा रहा है...")
                subprocess.run('ffmpeg -i input.mp4 -vn -acodec mp3 audio.mp3 -y', shell=True, check=True)

                # 3. Gemini AI से सबटाइटल्स जनरेट करना
                st.info("3. Gemini AI से सबटाइटल्स जनरेट हो रहे हैं...")
                client = genai.Client()
                audio_file = client.files.upload(file="audio.mp3")

                prompt = "इस ऑडियो को सुनें और केवल शुद्ध SRT सबटायटल फॉर्मेट में आउटपुट दें।"
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[audio_file, prompt]
                )

                with open("subtitles.srt", "w", encoding="utf-8") as f:
                    f.write(response.text)

                # 4. वीडियो एडिट और सबटायटल बर्न करना
                st.info("4. वीडियो एडिट और सबटाइटल्स बर्न हो रहे हैं...")
                ffmpeg_cmd = (
                    'ffmpeg -i input.mp4 -vf "crop=in_w*0.95:in_h*0.95,setpts=0.97*PTS,subtitles=subtitles.srt" '
                    '-filter:a "atempo=1.03" -y output_final.mp4'
                )
                subprocess.run(ffmpeg_cmd, shell=True, check=True)

                st.success("🎉 प्रक्रिया पूरी हुई! आपकी वीडियो तैयार है।")
                
                # तैयार वीडियो को वेबसाइट पर दिखाना और डाउनलोड का ऑप्शन देना
                if os.path.exists("output_final.mp4"):
                    st.video("output_final.mp4")
                    with open("output_final.mp4", "rb") as file:
                        st.download_button(
                            label="⬇️ Download Edited Video",
                            data=file,
                            file_name="output_final.mp4",
                            mime="video/mp4"
                        )

            except Exception as e:
                st.error(f"कोई गड़बड़ हुई: {e}")
            finally:
                # अस्थाई फाइलों की सफाई
                for temp_file in ["input.mp4", "audio.mp3", "subtitles.srt"]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
    else:
        st.warning("कृपया पहले एक YouTube URL दर्ज करें।")
