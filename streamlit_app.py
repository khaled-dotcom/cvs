# ============================
# streamlit_app.py
# ============================

import os
import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from io import BytesIO

# ============================
# 1. Groq API Key (TEST ONLY)
# ============================
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
    if not name:
        st.error("Name is required!")
        st.stop()

    st.info("Generating professional resume...")

    # ============================
    # 3. AI Prompt
    # ============================
    cv_prompt = f"""
You are a professional resume writer.
Rewrite the following information into a clean, polished, well-structured resume.

FORMAT STRICTLY LIKE THIS:
Summary:
Experience:
Education:
Skills:
Contact:

Expand all points into strong professional sentences.
Do NOT add symbols or separators.
Do NOT use markdown.
Do NOT add colons at line beginnings except the section titles.

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
        temperature=0.4,
        max_completion_tokens=1500
    )
    ai_text = completion.choices[0].message.content.strip()

    # ============================
    # 5. Extract sections
    # ============================
    sections = {"Summary": [], "Experience": [], "Education": [], "Skills": []}
    current = None

    proxies = {
        "summary": "Summary",
        "professional summary": "Summary",
        "experience": "Experience",
        "work experience": "Experience",
        "education": "Education",
        "education background": "Education",
        "skills": "Skills",
        "technical skills": "Skills",
    }

    for line in ai_text.split("\n"):
        clean = line.strip().lower().replace(":", "")
        if clean in proxies:
            current = proxies[clean]
        elif clean != "" and current:
            sections[current].append(line.strip())

    # ============================
    # 6. Generate PDF
    # ============================
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height - 2.5*cm, name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 3.5*cm, title)

    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 4.3*cm, f"{email} | {phone}")

    c.line(2*cm, height - 4.8*cm, width - 2*cm, height - 4.8*cm)

    y = height - 6*cm
    line_height = 0.55*cm

    def draw_section(title, content, y):
        c.setFont("Helvetica-Bold", 15)
        c.drawString(2*cm, y, title)
        y -= line_height

        c.setFont("Helvetica", 11)
        for text in content:
            wrapped = simpleSplit(text, "Helvetica", 11, width - 4*cm)
            for w in wrapped:
                c.drawString(2.5*cm, y, w)
                y -= line_height
                if y < 2.5*cm:
                    c.showPage()
                    y = height - 3*cm
                    c.setFont("Helvetica", 11)

        y -= 0.7*cm
        return y

    # Draw sections
    for sec in sections:
        if sections[sec]:
            y = draw_section(sec, sections[sec], y)

    c.save()
    buffer.seek(0)

    # ============================
    # 7. Download
    # ============================
    st.success("Resume generated successfully!")
    st.download_button(
        label="Download PDF Resume",
        data=buffer,
        file_name=f"{name.replace(' ', '_')}_resume.pdf",
        mime="application/pdf"
    )
