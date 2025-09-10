# pages/5_🔍_Case_Analyzer.py
import streamlit as st
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

st.set_page_config(layout="wide", page_title="Case Analyzer")
st.title("🔍 Case Analyzer")
st.write("Envie o caso e a IA analisará o problema e sugerirá soluções baseadas em jurisprudência e legislação.")

if "case_analyzer_input" not in st.session_state:
    st.session_state.case_analyzer_input = ""

case_text = st.text_area(
    "Descreva o caso:",
    value=st.session_state.case_analyzer_input,
    height=400,
    placeholder="Ex: O cliente teve atraso na entrega do imóvel..."
)

if st.button("Analisar caso"):
    if case_text:
        model_name = "google/flan-t5-base"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

        prompt = f"""
        Analise o seguinte caso jurídico e forneça:
        1. Resumo da situação
        2. Possíveis soluções legais
        3. Jurisprudência relacionada
        Caso:
        {case_text}
        """
        analysis = generator(prompt, max_length=500, do_sample=False)[0]['generated_text']
        st.subheader("Análise do Caso")
        st.markdown(analysis)
    else:
        st.error("Descreva o caso para análise.")
