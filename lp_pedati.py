import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from io import BytesIO

# --- 1. CONFIGURATION ---
# Using your verified new API Key
#genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
# This fetches the key safely from your secrets file
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def find_working_model():
    """Universal loader to find a working model and avoid 404 version errors."""
    try:
        # This lists all models available to your specific API key/version
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        return "models/gemini-1.5-flash"  # Fallback
    return "models/gemini-1.5-flash"


selected_model_name = find_working_model()
model = genai.GenerativeModel(selected_model_name)


def generate_pedati_plan(topic, syllabus, extra_context):
    # Prompt specifically locked to English and PEDATI titles
    prompt = f"""
    Topic: {topic}. Syllabus Code: {syllabus}. Context: {extra_context}.
    Generate a lesson plan in English. 
    NO Malay terms. Use these exact stage names:
    P [Prior Knowledge], E [Engage], D [Develop], A [Apply], T [Test], I [Improve].

    Structure with these markers for boxing:
    SECTION: LESSON OBJECTIVES
    [4 points]
    SECTION: LESSON OUTCOMES
    [4 points]
    SECTION: SUCCESS CRITERIA
    [4 points]
    SECTION: PREREQUISITE
    [1 point]
    SECTION: KEYWORDS
    [6 items]
    SECTION: HOTS
    [any 4 main domains in the Bloom's taxonomy]
    SECTION: DIGITAL CITIZENSHIP
    [4 points on the use of online resources like youtube channel or canva application or use of chromebooks or use of digital devices]

    SECTION: PEDATI STAGES
    STAGE: P [Prior Knowledge] | SB: [Activity] | CB: [Activity]
    STAGE: E [Engage] | SB: [Activity] | CB: [Activity]
    STAGE: D [Develop] | SB: [Activity] | CB: [Activity]
    STAGE: A [Apply] | SB: [Activity] | CB: [Activity]
    STAGE: T [Test] | SB: [Activity] | CB: [Activity]
    STAGE: I [Improve] | SB: [Activity] | CB: [Activity]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"System Error: {str(e)}"


def create_word_export(topic, syllabus, text):
    doc = Document()
    doc.add_heading(f'Lesson Plan: {topic} ({syllabus})', 0)

    # 1. Admin Header Table (6-field layout)
    admin_table = doc.add_table(rows=3, cols=4);
    admin_table.style = 'Table Grid'
    labels = [["Week No :", "Date:"], ["No. of Students:", "Day:"], ["Venue / Lab No:", "Duration (mins):"]]
    for r in range(3):
        admin_table.cell(r, 0).text = labels[r][0]
        admin_table.cell(r, 2).text = labels[r][1]
    doc.add_paragraph()

    # 2. Resources Table
    doc.add_heading("Resources & Materials", level=1)
    res_table = doc.add_table(rows=1, cols=1);
    res_table.style = 'Table Grid'
    res_table.cell(0, 0).text = "Smart board, Chromebook, Writing table, Projector, Screen share with laptop"

    # 3. Content Parsing & Table Boxing
    sections = text.split('SECTION:')
    for section in sections:
        if not section.strip(): continue
        lines = section.strip().split('\n')
        title = lines[0].strip()
        content_lines = lines[1:]
        doc.add_heading(title.title(), level=1)

        if "|" in section and "PEDATI" in title.upper():
            table = doc.add_table(rows=1, cols=3);
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text, hdr[2].text = 'Stage (PEDATI)', 'Facilitator (SB)', 'Student (CB)'

            for line in content_lines:
                if "|" in line:
                    p = line.split("|")
                    row = table.add_row().cells
                    row[0].text = p[0].split(":")[-1].strip()
                    row[1].text = p[1].split(":")[-1].strip()
                    row[2].text = p[2].split(":")[-1].strip()
        else:
            table = doc.add_table(rows=1, cols=1);
            table.style = 'Table Grid'
            table.cell(0, 0).text = "\n".join([l.strip() for l in content_lines if l.strip()])

    # 4. HOD Approval Page
    doc.add_page_break()
    doc.add_heading("HOD Approval & Remarks", level=1)
    hod_table = doc.add_table(rows=3, cols=2);
    hod_table.style = 'Table Grid'
    hod_table.cell(0, 0).text = "Remark";
    hod_table.cell(0, 1).text = "Signature / Stamp"
    hod_table.rows[1].height = Pt(60)
    hod_table.cell(2, 0).text = "Date:";
    hod_table.cell(2, 1).text = "Name:"

    bio = BytesIO();
    doc.save(bio);
    bio.seek(0)
    return bio

#############################################################################
# --- 2. GUI SECTION ---
st.set_page_config(page_title="PEDATI Master Planner", layout="wide")

# --- NEW SIDEBAR CODE ---
with st.sidebar:
    st.title("📖 User Guide")
    st.info("How to use this portal:")
    
    st.markdown("""
    ### 1. Fill Details
    Enter your **Lesson Topic** and **Syllabus Code**. Use the **Context** box for specific requirements like "Group Work" or "Case Study" or "Youtube link" or "Online LMS"
    
    ### 2. Generate
    Click **🚀 GENERATE** and wait for the AI to draft your plan.
    
    ### 3. Review & Save
    Check the **AI Preview**. If it looks good, click **📥 Download Word** to get your professional doc.
    
    ---
    ### 💡 Pro-Tip
    If the AI gets cut off, try adding more specific keywords in the Context box to guide it!
    """)
    st.markdown("---")
    st.caption("App Version 2.0 | PTES Innovation")

# --- MAIN DASHBOARD (Restored from your original) ---
st.title("🎓 PEDATI Lesson Plan Generator")
st.info(f"System connected via: {selected_model_name}")

c1, c2 = st.columns(2)
with c1: u_topic = st.text_input("Lesson Topic:")
with c2: u_syllabus = st.text_input("Syllabus Code:")
u_extra = st.text_area("Specific Context/Keywords (Optional):")

if st.button("🚀 GENERATE PEDATI LESSON PLAN"):
    if u_topic and u_syllabus:
        with st.spinner("AI is building your PEDATI plan..."):
            result = generate_pedati_plan(u_topic, u_syllabus, u_extra)
            st.session_state['pedati_out'] = result

if 'pedati_out' in st.session_state:
    st.divider()
    st.text_area("AI Preview", st.session_state['pedati_out'], height=300)
    doc_file = create_word_export(u_topic, u_syllabus, st.session_state['pedati_out'])
    st.download_button("📥 Download Word (.docx)", doc_file, f"PEDATI_{u_topic}.docx")

# --- FOOTER SECTION ---
st.markdown("---") 
st.markdown(
    """
    <div style='text-align: center; color: grey; font-size: 0.8em;'>
        <p><b>Smart PEDATI Lesson Plan AI-Generator v2.0</b></p>
        <p>Developed & Conceptualized by: <b>Hajah Nurul Haziqah @ Hjh Hartini Hj Nordin</b></p>
        <p>© 2026 PTES Academic Innovation Computer Science</p>
    </div>
    """,
    unsafe_allow_html=True
)
#############################################################################

