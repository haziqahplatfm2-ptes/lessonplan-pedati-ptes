import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from io import BytesIO

# --- 1. CONFIGURATION ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def find_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        return "models/gemini-1.5-flash"
    return "models/gemini-1.5-flash"

selected_model_name = find_working_model()
model = genai.GenerativeModel(selected_model_name)

def generate_pedati_plan(topic, syllabus, extra_context, links):
    # Prompt now includes Digital Citizenship and Resource Links logic
    prompt = f"""
    Topic: {topic}. Syllabus Code: {syllabus}. 
    Tutor Resources/Links: {links}.
    Context: {extra_context}.

    Generate a lesson plan in English. Use these exact stage names:
    P [Prior Knowledge], E [Engage], D [Develop], A [Apply], T [Test], I [Improve].

    REQUIRED SECTIONS:
    SECTION: OBJECTIVES
    SECTION: OUTCOMES
    SECTION: SUCCESS CRITERIA
    SECTION: KEYWORDS
    
    SECTION: DIGITAL CITIZENSHIP
    Based on the resources provided ({links}), generate 3-4 good digital habits 
    specifically for students using these tools (e.g., if using YouTube, mention copyright/distraction; 
    if using Canva, mention design ethics/originality).

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

def create_word_export(topic, syllabus, text, links):
    doc = Document()
    doc.add_heading(f'Lesson Plan: {topic} ({syllabus})', 0)

    # 1. Admin Header Table
    admin_table = doc.add_table(rows=3, cols=4)
    admin_table.style = 'Table Grid'
    labels = [["Week No :", "Date:"], ["No. of Students:", "Day:"], ["Venue / Lab No:", "Duration (mins):"]]
    for r in range(3):
        admin_table.cell(r, 0).text = labels[r][0]
        admin_table.cell(r, 2).text = labels[r][1]
    doc.add_paragraph()

    # 2. Resources Table (Updated to include tutor links)
    doc.add_heading("Resources & Online Links", level=1)
    res_table = doc.add_table(rows=1, cols=1)
    res_table.style = 'Table Grid'
    res_table.cell(0, 0).text = f"Hardware: Smart board, Chromebook, Projector.\nLinks/Resources: {links}"

    # 3. Content Parsing
    sections = text.split('SECTION:')
    for section in sections:
        if not section.strip(): continue
        lines = section.strip().split('\n')
        title = lines[0].strip()
        content_lines = lines[1:]
        
        doc.add_heading(title.title(), level=1)
        
        # SPECIAL BOXING: PEDATI STAGES
        if "|" in section and "PEDATI" in title.upper():
            table = doc.add_table(rows=1, cols=3)
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
        
        # SPECIAL BOXING: DIGITAL CITIZENSHIP
        elif "DIGITAL CITIZENSHIP" in title.upper():
            table = doc.add_table(rows=1, cols=1)
            table.style = 'Table Grid'
            # Apply light shading or bold for emphasis
            cell = table.cell(0,0)
            cell.text = "💡 Digital Habits for this Lesson:\n" + "\n".join([l.strip() for l in content_lines if l.strip()])

        # STANDARD BOXING: Others
        else:
            table = doc.add_table(rows=1, cols=1)
            table.style = 'Table Grid'
            table.cell(0, 0).text = "\n".join([l.strip() for l in content_lines if l.strip()])

    # 4. HOD Approval
    doc.add_page_break()
    doc.add_heading("HOD Approval & Remarks", level=1)
    hod_table = doc.add_table(rows=3, cols=2)
    hod_table.style = 'Table Grid'
    hod_table.cell(0, 0).text = "Remark"; hod_table.cell(0, 1).text = "Signature / Stamp"
    hod_table.rows[1].height = Pt(60)
    hod_table.cell(2, 0).text = "Date:"; hod_table.cell(2, 1).text = "Name:"

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GUI ---
st.set_page_config(page_title="PEDATI Master v2.0", layout="wide")
st.title("🎓 PEDATI Lesson Plan Generator v2.0")
st.markdown("---")

c1, c2 = st.columns(2)
with c1: u_topic = st.text_input("Lesson Topic:")
with c2: u_syllabus = st.text_input("Syllabus Code:")

# New Input Parameter for Resources
u_links = st.text_area("Online Resource Links (YouTube, Canva, Slides, etc.):", placeholder="Paste links here...")
u_extra = st.text_area("Extra Context (Optional):")

if st.button("🚀 GENERATE UPGRADED PLAN"):
    if u_topic and u_syllabus:
        with st.spinner("AI is crafting Digital Citizenship habits and PEDATI stages..."):
            result = generate_pedati_plan(u_topic, u_syllabus, u_extra, u_links)
            st.session_state['pedati_out'] = result

if 'pedati_out' in st.session_state:
    st.divider()
    st.text_area("AI Preview", st.session_state['pedati_out'], height=300)
    doc_file = create_word_export(u_topic, u_syllabus, st.session_state['pedati_out'], u_links)
    st.download_button("📥 Download Upgraded Word (.docx)", doc_file, f"PEDATI_V2_{u_topic}.docx")

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
