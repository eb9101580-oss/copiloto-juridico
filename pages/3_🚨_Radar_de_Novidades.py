# pages/3_🚨_Radar_de_Novidades.py
import streamlit as st
import sqlite3

DB = "juris.db"

st.set_page_config(layout="wide", page_title="Radar de Novidades")
st.title("🚨 Radar de Novidades")
st.write("Aqui você verá novas decisões relacionadas aos temas que acompanha.")

termos = st.text_input("Digite os temas ou palavras-chave separadas por vírgula:", placeholder="Ex: rescisão, dano moral, atraso obra")

if st.button("Ver novidades"):
    if termos:
        termos_list = [t.strip() for t in termos.split(",")]
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in termos_list)
        query_sql = f"""
        SELECT tribunal, processo, data, ementa, link 
        FROM jurisprudencia 
        WHERE {" OR ".join(["ementa LIKE ?"]*len(termos_list))} 
        ORDER BY data DESC LIMIT 10
        """
        cur.execute(query_sql, [f"%{t}%" for t in termos_list])
        results = cur.fetchall()
        conn.close()
        
        if results:
            for r in results:
                tribunal, processo, data, ementa, link = r
                with st.container():
                    st.markdown(f"**Processo:** {processo} | **Tribunal:** {tribunal} | **Data:** {data}")
                    st.markdown(f"**Ementa:** {ementa}")
                    if link:
                        st.markdown(f"[Ver documento original]({link})")
        else:
            st.warning("Nenhuma decisão nova encontrada para os termos informados.")
    else:
        st.error("Digite pelo menos um termo para continuar.")
