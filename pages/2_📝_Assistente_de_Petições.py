# pages/2_📝_Assistente_de_Petições.py
import streamlit as st
import sqlite3
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# --- Configuração ---
DB = "juris.db"
INDEX_FILE = "juris_index.faiss"
MAP_FILE = "id_map.pkl"

@st.cache_resource
def load_models():
    """Carrega modelos de embedding, índice FAISS e mapa de IDs"""
    st.info("Carregando modelos e índice...")
    model_embedding = SentenceTransformer('all-MiniLM-L6-v2')
    index = faiss.read_index(INDEX_FILE)
    with open(MAP_FILE, 'rb') as f:
        id_map = pickle.load(f)
    st.success("Modelos carregados!")
    return model_embedding, index, id_map

model_embedding, index, id_map = load_models()

# --- Funções ---
def semantic_search(query, top_k=3):
    if not query:
        return []
    
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

def format_jurisprudence(result):
    """Formata jurisprudência no padrão ABNT/CNJ com resumos estratégicos"""
    id_reg, tribunal, processo, data, ementa, tese, jurisprudencia_consolidada, link = result
    
    formatted_text = f"""
**Ementa:** {ementa.strip()}

**Tese:** {tese or 'Não disponível'}

**Jurisprudência Consolidada:** {jurisprudencia_consolidada or 'Não disponível'}

(APELAÇÃO CÍVEL - {tribunal} - PROCESSO: {processo})
"""
    return formatted_text

# --- Interface ---
st.set_page_config(layout="wide", page_title="Copiloto Jurídico AI - Petições")
st.title("📝 Assistente de Petições com IA")
st.write("Escreva a sua petição e a IA sugerirá jurisprudência relevante em tempo real.")

# Área de texto
if "petition_input" not in st.session_state:
    st.session_state.petition_input = ""

petition_text = st.text_area(
    "Escreva sua petição aqui:",
    value=st.session_state.petition_input,
    height=400,
    placeholder="Ex: A rescisão do contrato de compra e venda por atraso na entrega do imóvel é medida de justiça...",
    key="petition_input_area"
)

# Busca automática
if petition_text:
    if len(petition_text.split()) > 50:  # Gatinho: a cada 50 palavras, busca
        st.info("Analisando o texto para encontrar jurisprudência relevante...")
        
        last_sentence = petition_text.split('.')[-2].strip() + '.' if len(petition_text.split('.')) > 1 else petition_text
        
        relevant_juris = semantic_search(last_sentence)
        
        if relevant_juris:
            st.subheader("Sugestões de Jurisprudência:")
            for r in relevant_juris:
                with st.container():
                    formatted_text = format_jurisprudence(r)
                    st.markdown(formatted_text)
                    if st.button("Copiar para a petição", key=f"copy_button_{r[0]}"):
                        st.session_state.petition_input += "\n\n" + formatted_text
                        st.success("Copiado! Role para cima para ver a jurisprudência inserida.")
        else:
            st.warning("Nenhuma jurisprudência relevante encontrada para este trecho.")
