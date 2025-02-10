import streamlit as st
import json
import pandas as pd
import docx
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from transformers import T5Tokenizer, T5ForConditionalGeneration
import os

# Google Sheets Configuration
SPREADSHEET_ID = "1PZaFBsyUnaUbOwVOLU8XnOug4eGZNlMaGr561Ael6FM"
RANGE_NAME = "Sheet1!A1"
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "C:\\Projects\Infosys\\ai-driven-legal-analyzer-a469ea4bc49d.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Streamlit UI Configuration
st.set_page_config(page_title="Legal Document Risk Analysis Dashboard", layout="wide")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

st.sidebar.header("Email Configuration")
SENDER_EMAIL = st.sidebar.text_input("Sender Email", "example@email.com")
PASSWORD = st.sidebar.text_input("Sender Password", type="password")
RECEIVER_EMAIL = st.sidebar.text_input("Recipient Email", "receiver@email.com")

# Load FLAN-T5 Model
TOKENIZER = T5Tokenizer.from_pretrained("google/flan-t5-small")
MODEL = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")


# Function to Read Files
def read_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    return "Unsupported file type"


# Function to Generate Text using FLAN-T5
def generate_text(prompt):
    inputs = TOKENIZER(prompt, return_tensors="pt", truncation=True, padding=True, max_length=1024)
    outputs = MODEL.generate(inputs["input_ids"], min_length=50, max_length=200, num_beams=4, early_stopping=True)
    return TOKENIZER.decode(outputs[0], skip_special_tokens=True)


# Function to Update Google Sheets
def update_google_sheets(data):
    try:
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)

        # Convert dict_keys to a list
        values = [list(data.keys())] + [list(data.values())]

        body = {"values": values}

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="RAW",
            body=body,
        ).execute()

        return "✅ Google Sheets updated successfully."

    except Exception as e:
        return f"❌ Error updating Google Sheets: {e}"


# Function to Send Email Notification
def send_email():
    subject = "Legal Document Analysis Update"
    body = f"Legal Document Analysis update: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit?gid=0"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        return "📧 Email sent successfully."
    except Exception as e:
        return f"❌ Error sending email: {e}"


# Streamlit UI
st.title("📜 Legal Document Risk Analysis Dashboard")
st.subheader("📂 Upload a Legal Document")

uploaded_file = st.file_uploader("Upload your document (TXT, DOCX)", type=["txt", "docx"])

if uploaded_file is not None:
    st.success("✅ File uploaded successfully!")

    document_text = read_file(uploaded_file)

    st.markdown("### 🔍 Analyzing the document...")

    # Generate AI-based analysis
    summary = generate_text(f"summarize: {document_text}")
    risks = generate_text(f"Identify risks in: {document_text}")
    recommendations = generate_text(f"Provide recommendations for: {document_text}")

    # Display results
    st.markdown("### 📊 Results")

    df = pd.DataFrame({
        "Context": [document_text[:100] + "..."],
        "Risks": [risks],
        "Recommendations": [recommendations]
    })

    st.dataframe(df)

    # Store results in session state to use with the button
    if "analysis_data" not in st.session_state:
        st.session_state.analysis_data = None

    st.session_state.analysis_data = {
        "Summary": summary,
        "Risks": risks,
        "Recommendations": recommendations
    }

    # Button to Update Google Sheets
    if st.button("📤 Update Google Sheets"):
        if st.session_state.analysis_data:
            result = update_google_sheets(st.session_state.analysis_data)
            st.success(result)

    # Button to Send Email
    if st.button("📧 Send Email Notification"):
        email_result = send_email()
        st.success(email_result)
