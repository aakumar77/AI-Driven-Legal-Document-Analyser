import streamlit as st
from transformers import T5Tokenizer, T5ForConditionalGeneration
import docx
from langchain.embeddings import HuggingFaceEmbeddings
# Initialize the FLAN-T5 model and tokenizer
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")


# Function to read .txt or .docx files
def read_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return "Unsupported file type"


# Function to perform text generation or summarization using FLAN-T5
def generate_text(prompt):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True, max_length=20000)
    outputs = model.generate(inputs["input_ids"],min_length=100, max_length=200, num_beams=4, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Streamlit UI for file upload
st.title("File Upload & NLP with FLAN-T5")
uploaded_file = st.file_uploader("Choose a text file", type=["txt", "docx"])

if uploaded_file is not None:
    document_text = read_file(uploaded_file)


    # Use FLAN-T5 to summarize or generate text (example: summarization)
    prompt1 = f"summarize: {document_text}"
    summary = generate_text(prompt1)
    prompt2 = f"analyze: {document_text}"
    analysis = generate_text(prompt2)
    prompt3 = f"recommendation: {document_text}"
    recommendation = generate_text(prompt3)

    st.write("FLAN-T5 Summary:")
    st.write(summary)
    st.write("FLAN-T5 Analysis:")
    st.write(analysis)
    st.write("FLAN-T5 Recommendation:")
    st.write(recommendation)