import streamlit as st
import PyPDF2
import re
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import spacy

# Carregue o modelo de linguagem em português
nlp = spacy.load("pt_core_news_sm")

def detect_sensitive_data(text):
    doc = nlp(text)
    sensitive_data = []

    # Detectar entidades nomeadas
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC", "ORG"]:
            sensitive_data.append((ent.start_char, ent.end_char, ent.label_))

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
        matches = re.finditer(pattern, text)
        for match in matches:
            sensitive_data.append((match.start(), match.end(), data_type))

    return sensitive_data

def perform_ocr(image):
    return pytesseract.image_to_string(image, lang='por')

def anonymize_image(image, sensitive_data):
    img_np = np.array(image)
    for start, end, _ in sensitive_data:
        # Encontrar a posição aproximada no layout da imagem
        # Isso requer calibração cuidadosa baseada no seu layout específico
        y = start // 100  # Exemplo simplificado
        x = start % 100
        cv2.rectangle(img_np, (x, y), (x + 100, y + 20), (0, 0, 0), -1)
    return Image.fromarray(img_np)

def anonymize_pdf(input_pdf):
    pdf_bytes = input_pdf.read()
    images = convert_from_bytes(pdf_bytes)
    
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    
    for image in images:
        # Realizar OCR
        text = perform_ocr(image)
        
        # Detectar dados sensíveis
        sensitive_data = detect_sensitive_data(text)
        
        # Anonimizar a imagem
        anonymized_image = anonymize_image(image, sensitive_data)
        
        # Adicionar a imagem anonimizada ao novo PDF
        c.drawInlineImage(anonymized_image, 0, 0, width=letter[0], height=letter[1])
        c.showPage()
    
    c.save()
    output.seek(0)
    return output

def main():
    st.set_page_config(page_title="Cryptos", page_icon="🔒", layout="wide")
    
    st.title("Cryptos: Anonimização Avançada de PDF")
    st.markdown("### Proteja seus dados sensíveis com Cryptos")
    
    st.sidebar.image("https://via.placeholder.com/150?text=Cryptos", width=150)
    st.sidebar.title("Sobre o Cryptos")
    st.sidebar.info(
        "Cryptos é uma ferramenta avançada de anonimização de PDFs. "
        "Utilizamos tecnologia de ponta em OCR e processamento de linguagem natural "
        "para identificar e proteger dados sensíveis em seus documentos."
    )
    
    uploaded_file = st.file_uploader("Escolha um arquivo PDF para anonimizar", type="pdf")
    
    if uploaded_file is not None:
        st.success("Arquivo carregado com sucesso!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Opções de Anonimização:")
            anonimizar_nomes = st.checkbox("Nomes", value=True)
            anonimizar_cpf = st.checkbox("CPF", value=True)
            anonimizar_endereco = st.checkbox("Endereços", value=True)
            anonimizar_telefone = st.checkbox("Telefones", value=True)
        
        with col2:
            st.write("Visualização do PDF:")
            # Aqui você pode adicionar uma visualização do PDF original se desejar
        
        if st.button("Anonimizar PDF"):
            with st.spinner("Processando o PDF... Isso pode levar alguns minutos."):
                output_pdf = anonymize_pdf(uploaded_file)
            
            st.success("PDF anonimizado com sucesso!")
            st.download_button(
                label="Baixar PDF Anonimizado",
                data=output_pdf,
                file_name="documento_anonimizado_cryptos.pdf",
                mime="application/pdf"
            )
    
    st.markdown("---")
    st.markdown("© 2024 Cryptos. Todos os direitos reservados.")

if __name__ == "__main__":
    main()