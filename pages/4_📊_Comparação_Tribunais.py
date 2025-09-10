# pages/4_📊_Comparação_Tribunais.py
import streamlit as st
import sqlite3

DB = "juris.db"

st.set_page_config(layout="wide", page_title="Comparação entre Tribunais")
st.title("📊 Comparação entre Tribunais")

tema = st.text_input("Digite o tema que deseja comparar:")

if st.button("Comparar"):
    if tema:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        tribunais = ['STF','STJ','TJ']
        for t in tribunais:
            cur.execute("SELECT processo, data, ementa, link FROM jurisprudencia WHERE tribunal=? AND ementa LIKE ? LIMIT 5", (t, f"%{tema}%"))
            results = cur.fetchall()
            st.subheader(f"Tribunal: {t}")
            if results:
                for r in results:
                    processo, data, ementa, link = r
                    st.markdown(f"**Processo:** {processo} | **Data:** {data}")
                    st.markdown(f"**Ementa:** {ementa}")
                    if link:
                        st.markdown(f"[Ver documento original]({link})")
            else:
                st.info(f"Nenhum resultado encontrado em {t}.")
        conn.close()
    else:
        st.error("Digite o tema para comparar.")
