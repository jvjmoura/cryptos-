import os
import re
import spacy
import pytesseract
import streamlit as st
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Configuração do Tesseract
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Carregar modelo de linguagem em português
nlp = spacy.load("pt_core_news_sm")

def extract_text_from_pdf(file_path):
    pdf = PdfFileReader(file_path)
    text = ""
    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        text += page.extract_text()
    return text

def detect_sensitive_data(text):
    doc = nlp(text)
    sensitive_data = []

    # Detectar entidades nomeadas
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC", "ORG"]:
            sensitive_data.append(ent.text)

    # Padrões regulares para outros tipos de dados sensíveis
    patterns = {
        'CPF': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'RG': r'\d{2}\.\d{3}\.\d{3}-\d{1}',
        'Email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'Telefone': r'\(\d{2}\)\s*\d{4,5}-\d{4}',
        'CEP': r'\d{5}-\d{3}',
        'Data': r'\d{2}/\d{2}/\d{4}',
    }

    for data_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        for match in matches:
            sensitive_data.append(match)

    return sensitive_data

def anonymize_text(text, sensitive_data):
    anonymized_text = text
    for data in sensitive_data:
        anonymized_text = anonymized_text.replace(data, "[ANONIMIZADO]")
    return anonymized_text

def create_anonymized_pdf(original_pdf_path, anonymized_text, output_pdf_path):
    # Converter texto anonímizado em PDF
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    lines = anonymized_text.split("\n")
    
    for line in lines:
        c.drawString(30, 750, line)
        c.showPage()

    c.save()
    output.seek(0)

    # Ler o PDF original
    original_pdf = PdfFileReader(original_pdf_path)
    output_pdf = PdfFileWriter()

    # Adicionar páginas anonimizadas ao novo PDF
    anonymized_pdf = PdfFileReader(output)
    for i in range(anonymized_pdf.getNumPages()):
        output_pdf.addPage(anonymized_pdf.getPage(i))

    # Escrever o novo PDF no arquivo de saída
    with open(output_pdf_path, 'wb') as f:
        output_pdf.write(f)

def main():
    st.title("Anonimização de PDF")
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    
    if uploaded_file is not None:
        with open("/mnt/data/sentença-8.pdf", "wb") as f:
            f.write(uploaded_file.read())
        
        st.success("Arquivo carregado com sucesso!")
        
        if st.button("Anonimizar PDF"):
            with st.spinner("Processando..."):
                original_pdf_path = "/mnt/data/sentença-8.pdf"
                output_pdf_path = "/mnt/data/sentenca_anonimizada.pdf"
                
                text = extract_text_from_pdf(original_pdf_path)
                sensitive_data = detect_sensitive_data(text)
                anonymized_text = anonymize_text(text, sensitive_data)
                create_anonymized_pdf(original_pdf_path, anonymized_text, output_pdf_path)
                
                st.success("PDF anonimizado com sucesso!")
                st.download_button("Baixar PDF Anonimizado", data=output_pdf_path, file_name="sentenca_anonimizada.pdf")

if __name__ == "__main__":
    main()
