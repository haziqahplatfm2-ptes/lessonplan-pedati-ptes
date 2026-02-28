import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from io import BytesIO

# --- 1. AI CONFIGURATION ---
genai.configure(api_key="AIzaSyCSlDXoqhAVqCcQLEhxNywnyAtTzLXiRXo")

@st.cache_resource
def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods: return m.name
    except:
        return "models/gemini-1.5-flash"
    return "models/gemini-1.5-flash"


model = genai.GenerativeModel(get_working_model())


def generate_full_pedati_ai(topic, syllabus):
    # We strictly define the titles in the prompt to force English + Code
    prompt = f"""
    Topic: {topic}. Syllabus Code: {syllabus}.
    Generate a lesson plan. DO NOT use Malay terms. Use English.

    Structure the response with these EXACT markers:
    SECTION: OBJECTIVES
    [4 points]
    SECTION: OUTCOMES
    [4 points]
    SECTION: SUCCESS CRITERIA
    [4 points]
    SECTION: PREREQUISITE
    [1 point]
    SECTION: KEYWORDS
    [10 items]
    SECTION: HOTS
    [4 questions]

    SECTION: PEDATI STAGES
    STAGE: P [Prior Knowledge] | SB: [Activity] | CB: [Activity]
    STAGE: E [Engage] | SB: [Activity] | CB: [Activity]
    STAGE: D [Develop] | SB: [Activity] | CB: [Activity]
    STAGE: A [Apply] | SB: [Activity] | CB: [Activity]
    STAGE: T [Test] | SB: [Activity] | CB: [Activity]
    STAGE: I [Improve] | SB: [Activity] | CB: [Activity]
    """
    return model.generate_content(prompt).text


def create_word_export(topic, syllabus, text):
    doc = Document()
    doc.add_heading(f'Lesson Plan: {topic} ({syllabus})', 0)

    # 1. Header Table (6 Fields)
    admin_table = doc.add_table(rows=3, cols=4)
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

    # 3. Content Parsing (Boxing everything)
    sections = text.split('SECTION:')
    for section in sections:
        if not section.strip(): continue

        lines = section.strip().split('\n')
        title = lines[0].strip()
        content_lines = lines[1:]

        doc.add_heading(title.title(), level=1)

        if "PEDATI" in title.upper():
            # 3-Column Table
            table = doc.add_table(rows=1, cols=3);
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text, hdr[2].text = 'Stage', 'Smart Board (Facilitator)', 'Chromebook (Student)'
            for line in content_lines:
                if "|" in line:
                    p = line.split("|")
                    row = table.add_row().cells
                    row[0].text = p[0].replace("STAGE:", "").strip()
                    row[1].text = p[1].replace("SB:", "").strip()
                    row[2].text = p[2].replace("CB:", "").strip()
        else:
            # Single Cell Box
            table = doc.add_table(rows=1, cols=1);
            table.style = 'Table Grid'
            table.cell(0, 0).text = "\n".join([l.strip() for l in content_lines if l.strip()])

    # 4. HOD Table on Last Page
    doc.add_page_break()
    doc.add_heading("Principal / HOD Approval & Remarks", level=1)
    hod_table = doc.add_table(rows=3, cols=2);
    hod_table.style = 'Table Grid'
    hod_table.cell(0, 0).text = "Remark";
    hod_table.cell(0, 1).text = "Signature / Department Stamp"
    hod_table.rows[1].height = Pt(60)
    hod_table.cell(2, 0).text = "Date:";
    hod_table.cell(2, 1).text = "Name:"

    bio = BytesIO();
    doc.save(bio);
    bio.seek(0)
    return bio

# --- GUI ---
st.set_page_config(page_title="PEDATI Master Planner", layout="wide")
st.title(" PUSAT TINGKATAN ENAM SENGKURONG ")
st.title("🎓 LESSON PLAN with PEDATI pedagogy")

c1, c2 = st.columns(2)
with c1: u_topic = st.text_input("Lesson Topic:")
with c2: u_syllabus = st.text_input("Syllabus Code:")

if st.button("🚀 GENERATE FINAL LESSON PLAN"):
    if u_topic and u_syllabus:
        with st.spinner("Ensuring Layout and Lesson Plan are well organized..."):
            try:
                full_plan = generate_full_pedati_ai(u_topic, u_syllabus)
                st.session_state['master_plan'] = full_plan
                st.success("Lesson Plan Generated!")
                st.text_area("Preview Content Only ", full_plan, height=300)
            except Exception as e:
                st.error(f"Error: {e}")

if 'master_plan' in st.session_state:
    doc_file = create_word_export(u_topic, u_syllabus, st.session_state['master_plan'])
    st.download_button("📥 Download this Lesson plan in Word (.docx)", doc_file, f"PEDATI_{u_topic}.docx")

