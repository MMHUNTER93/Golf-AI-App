import streamlit as st
from google import genai
import tempfile
import pandas as pd
import os

# Set up page layout
st.set_page_config(page_title="AI Golf Swing & Stats Lab", layout="wide")
st.title("⛳ AI Golf Performance Lab")

# Initialize Gemini Client (Requires GEMINI_API_KEY environment variable)
@st.cache_resource
def get_client():
    return genai.Client()

client = get_client()

# Navigation Tabs
tab1, tab2 = st.tabs(["📹 Video Swing Analysis", "📊 Round Stats Analysis"])

# --- TAB 1: SWING ANALYSIS ---
with tab1:
    st.header("Upload Swing Video")
    uploaded_video = st.file_uploader("Upload Down-the-Line (DTL) or Face-On video", type=["mp4", "mov", "avi"])
    
    col1, col2 = st.columns(2)
    with col1:
        camera_angle = st.selectbox("Camera View Angle", ["Down the Line (DTL)", "Face-On (Front)"])
        shot_shape = st.selectbox("Current Miss Pattern", ["Push / Block Right", "Pull / Hook Left", "Chunk / Heavy", "Thin / Top", "Solid Contact"])
    with col2:
        club_used = st.selectbox("Club Used", ["Driver", "Fairway Wood", "Mid/Long Iron", "Wedge"])
        target_focus = st.multiselect("Specific Focus Areas", ["Takeaway", "Backswing Depth", "Downswing Transition", "Impact / Shaft Lean", "Tempo"], default=["Downswing Transition"])

    if uploaded_video is not None:
        st.video(uploaded_video)
        
        if st.button("Analyze Swing Mechanics", type="primary"):
            with st.spinner("Processing video and evaluating swing mechanics..."):
                # Save video temporarily for API upload
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                    tmp_file.write(uploaded_video.read())
                    temp_path = tmp_file.name

                # Upload to Gemini File API
                video_file = client.files.upload(file=temp_path)
                
                system_instruction = """
                You are a master PGA Golf Teaching Professional. Analyze the provided swing video.
                Focus on mechanical efficiency, posture, shaft plane, body rotation, and contact position.
                Deliver structured, actionable, and encouraging feedback using standard golf teaching terminology.
                """

                prompt = f"""
                Analyze this golf swing with the following metadata:
                - View Angle: {camera_angle}
                - Club: {club_used}
                - Typical Miss: {shot_shape}
                - Key Focus: {', '.join(target_focus)}

                Please structure your response into:
                1. 🔍 **Key Observations**: Address, Top of Swing, Downswing Transition, and Impact.
                2. ⚠️ **Primary Mechanical Flaw**: Identify the single root cause issue (e.g., coming over the top, early extension, sway vs turn).
                3. 🛠️ **2 Actionable Drills**: Give step-by-step instructions for physical drills to fix the main issue.
                """

                # Generate response
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[video_file, prompt],
                    config={"system_instruction": system_instruction}
                )

                st.markdown("---")
                st.subheader("📋 Coach's Breakdown")
                st.write(response.text)
                
                # Cleanup temporary file
                os.remove(temp_path)

# --- TAB 2: STATS ANALYSIS ---
with tab2:
    st.header("Upload Round Statistics")
    uploaded_stats = st.file_uploader("Upload CSV or Excel file (Fairways, GIR, Putts, Penalties)", type=["csv", "xlsx"])

    if uploaded_stats is not None:
        if uploaded_stats.name.endswith('.csv'):
            df = pd.read_csv(uploaded_stats)
        else:
            df = pd.read_excel(uploaded_stats)
            
        st.dataframe(df.head())
        
        if st.button("Generate Strokes Gained & Focus Report"):
            with st.spinner("Analyzing stats trend..."):
                stats_summary = df.to_string()
                
                prompt = f"""
                Below is my recent round performance data:
                \n{stats_summary}\n
                Act as a golf performance analyst. Identify:
                1. Where I am losing the most strokes.
                2. My strongest area of play.
                3. Top 3 practice priorities for my next practice session.
                """
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                
                st.subheader("📈 Performance Breakdown")
                st.write(response.text)
              
