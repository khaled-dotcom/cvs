# ============================
# streamlit_app.py
# ============================

import os
import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO

# ============================
# 1. Groq API Key
# ============================
# REMOVE before sharing publicly. Use Streamlit secrets for deployment
os.environ["GROQ_API_KEY"] = "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"
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ============================
# 2. Streamlit UI
# ============================
st.title("AI-Powered Resume Generator")

with st.form("cv_form"):
    name = st.text_input("Full Name")
    title = st.text_input("Job Title")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    experience = st.text_area("Experience (one per line)")
    education = st.text_area("Education (one per line)")
    skills = st.text_input("Skills (comma separated)")
    submit = st.form_submit_button("Generate Resume")

if submit:
    st.info("Generating professional resume...")

    # ============================
    # 3. Build AI Prompt
    # ============================
    cv_prompt = f"""
You are a professional resume writer.
Take the following raw information and generate a polished professional resume.
Expand short inputs into detailed sentences.
Separate sections clearly but not ---------: Contact Info, Summary, Experience, Education, Skills.
Do not use LaTeX. Keep it plain text ready for PDF.

Name: {name}
Title: {title}
Email: {email}
Phone: {phone}
Experience:
{experience}
Education:
{education}
Skills:
{skills}
"""

    # ============================
    # 4. Call Groq AI
    # ============================
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": cv_prompt}],
        temperature=0.7,
        max_completion_tokens=1500
    )
    ai_text = completion.choices[0].message.content.strip()

    # ============================
    # 5. Generate PDF
    # ============================
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height-3*cm, name)
    c.setFont("Helvetica-Oblique", 16)
    c.drawCentredString(width/2, height-4*cm, title)
    c.line(2*cm, height-4.5*cm, width-2*cm, height-4.5*cm)

    # Write AI text
    y = height-5.2*cm
    c.setFont("Helvetica", 12)
    section_spacing = 1*cm

    def draw_section(title, content_lines, y):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y, title)
        y -= 0.6*cm
        c.setFont("Helvetica", 12)
        for line in content_lines:
            c.drawString(2.5*cm, y, line)
            y -= 0.6*cm
            if y < 2*cm:
                c.showPage()
                y = height-2*cm
                c.setFont("Helvetica", 12)
        y -= section_spacing
        return y

    current_section = None
    section_lines = []
    for line in ai_text.split("\n"):
        line = line.strip()
        if line.lower().startswith(("summary", "experience", "education", "skills", "contact")):
            if current_section:
                y = draw_section(current_section, section_lines, y)
            current_section = line
            section_lines = []
        elif line != "":
            section_lines.append(line)
    if current_section:
        y = draw_section(current_section, section_lines, y)

    c.save()
    buffer.seek(0)

    # ============================
    # 6. Streamlit Download
    # ============================
    st.success("Resume generated successfully!")
    st.download_button(
        label="Download PDF Resume",
        data=buffer,
        file_name=f"{name.replace(' ','_')}_resume.pdf",
        mime="application/pdf"
    )
