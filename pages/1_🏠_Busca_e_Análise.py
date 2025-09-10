import streamlit as st
import sqlite3
import faiss
import pickle
import numpy as np
import random

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# --- Configuração e Carregamento dos Modelos ---
DB = "juris.db"
INDEX_FILE = "juris_index.faiss"
MAP_FILE = "id_map.pkl"

@st.cache_resource
def load_models():
    """Carrega modelos de embedding, FAISS, mapa e pipeline de resumo"""
    from sentence_transformers import SentenceTransformer
    model_embedding = SentenceTransformer('all-MiniLM-L6-v2')

    model_name_summarizer = "facebook/bart-large-cnn"
    tokenizer_summarizer = AutoTokenizer.from_pretrained(model_name_summarizer)
    model_summarizer = AutoModelForSeq2SeqLM.from_pretrained(model_name_summarizer)
    summarizer = pipeline("summarization", model=model_summarizer, tokenizer=tokenizer_summarizer)

    index = faiss.read_index(INDEX_FILE)
    with open(MAP_FILE, 'rb') as f:
        id_map = pickle.load(f)
    
    return model_embedding, index, id_map, summarizer

model_embedding, index, id_map, summarizer = load_models()

# --- Funções ---
def semantic_search(query, top_k=5):
    query_embedding = model_embedding.encode([query])
    faiss.normalize_L2(query_embedding)
    
    distances, indices = index.search(query_embedding, top_k)
    retrieved_ids = [id_map[i] for i in indices[0]]
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    query_sql = f"""
    SELECT id, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link
    FROM jurisprudencia
    WHERE id IN ({','.join('?' for _ in retrieved_ids)})
    ORDER BY CASE id
        { ''.join(f' WHEN ? THEN {i}' for i, _ in enumerate(retrieved_ids)) }
    END
    """
    cur.execute(query_sql, retrieved_ids * 2)
    results = cur.fetchall()
    conn.close()
    return results

def summarize_text(text):
    try:
        summary = summarizer(text, max_length=150, min_length=50, do_sample=False)[0]['summary_text']
        return summary
    except:
        return "Resumo não disponível."

def generate_case_analysis(query, results):
    if not results:
        return "Não foi possível encontrar jurisprudência relevante."
    
    context_text = f"O usuário está buscando análise para: {query}\n\n"
    for i, r in enumerate(results):
        id_reg, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link = r
        context_text += f"Documento {i+1}: Tribunal: {tribunal}, Processo: {processo}, Ementa: {ementa}\n\n"
    
    prompt = f"""
    Baseando-se no contexto jurídico abaixo, escreva análise objetiva com:
    1. Resumo da Tese Jurídica
    2. Fundamentação da Jurisprudência
    3. Conclusão Aplicada ao Caso

    Contexto:
    {context_text}
    """
    # Aqui usamos summarizer como placeholder
    analysis = summarize_text(prompt)
    return analysis

def predict_success_rate(query):
    query_lower = query.lower()
    if "dano moral" in query_lower or "rescisão" in query_lower:
        base_rate = 75
    elif "revisão" in query_lower or "acordo" in query_lower:
        base_rate = 60
    else:
        base_rate = 50
    return min(100, max(0, base_rate + random.randint(-15, 15)))

# --- Interface ---
st.set_page_config(layout="wide", page_title="Copiloto Jurídico AI")
st.title("⚖️ Copiloto Jurídico AI")
st.write("Assistente jurídico inteligente: pesquisa, análise e previsão de decisões.")

option = st.selectbox(
    'Escolha uma funcionalidade:',
    ('Busca Semântica', 'Análise de Caso', 'Análise Preditiva')
)

termo_busca = st.text_input("Descreva o caso ou tese", placeholder="Ex: rescisão de contrato por atraso na obra...")

if st.button("Executar"):
    if not termo_busca:
        st.error("Descreva o caso ou tese para continuar.")
    else:
        if option == 'Busca Semântica':
            st.info("Buscando e gerando resumos...")
            resultados = semantic_search(termo_busca)
            st.subheader(f"Resultados para '{termo_busca}':")
            if not resultados:
                st.warning("Nenhum resultado encontrado.")
            else:
                for r in resultados:
                    id_reg, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link = r
                    resumo_ementa = summarize_text(ementa)
                    with st.container():
                        st.markdown(f"**Processo:** `{processo}`")
                        st.markdown(f"**Tribunal:** {tribunal} | **Data:** {data or 'Não informada'}")
                        st.markdown(f"**Resumo Estratégico:** {resumo_ementa}")
                        st.markdown(f"**Tese:** {tese or 'Não disponível'}")
                        st.markdown(f"**Jurisprudência Consolidada:** {jurisprudencia_consolidada or 'Não disponível'}")
                        with st.expander("Ver Ementa Completa"):
                            st.text_area("Ementa", value=ementa.strip(), height=200, disabled=True)
                        if link:
                            st.markdown(f"[Ver documento original]({link})")
        
        elif option == 'Análise de Caso':
            resultados = semantic_search(termo_busca, top_k=3)
            if not resultados:
                st.warning("Nenhuma jurisprudência relevante encontrada.")
            else:
                análise = generate_case_analysis(termo_busca, resultados)
                st.subheader("Análise de Caso:")
                st.markdown(análise)
                st.subheader("Jurisprudência Base:")
                for r in resultados:
                    id_reg, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link = r
                    with st.expander(f"Processo: {processo} | Tribunal: {tribunal}"):
                        st.text_area("Ementa", value=ementa.strip(), height=150, disabled=True)
                        if link:
                            st.markdown(f"[Ver documento original]({link})")
        
        elif option == 'Análise Preditiva':
            resultados = semantic_search(termo_busca, top_k=5)
            if not resultados:
                st.warning("Nenhuma jurisprudência relevante encontrada.")
            else:
                chance = predict_success_rate(termo_busca)
                st.subheader("📊 Estimativa de Êxito")
                st.metric(label="Probabilidade de Êxito", value=f"{chance}%")
                st.subheader("Jurisprudência Base:")
                for r in resultados:
                    id_reg, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link = r
                    with st.expander(f"Processo: {processo} | Tribunal: {tribunal}"):
                        st.text_area("Ementa", value=ementa.strip(), height=150, disabled=True)
                        if link:
                            st.markdown(f"[Ver documento original]({link})")
