import streamlit as st
import pandas as pd
from db import get_connection, excluir_registro
from pdf_utils import gerar_pdf_simples

def render_orcamentos():
    st.header("Orçamentos")
    with st.form("orc", clear_on_submit=True):
        serv = st.text_input("Serviço")
        mat = st.text_area("Materiais")
        val = st.number_input("Valor Estimado", min_value=0.0)
        if st.form_submit_button("Gerar Orçamento"):
            conn = get_connection()
            c = conn.cursor()
            # CORREÇÃO: Utilizando %s
            c.execute('INSERT INTO orçamentos (servico, materiais, valor) VALUES (%s,%s,%s)', (serv, mat, val))
            conn.commit()
            conn.close()
            
            st.session_state['msg_sucesso'] = "Orçamento gerado e salvo com sucesso!"
            st.rerun()
            
    conn = get_connection()
    df_orc = pd.read_sql_query('SELECT * FROM orçamentos', conn)
    for _, row in df_orc.iterrows():
        c1, c2, c3 = st.columns([4, 2, 2])
        c1.write(f"**{row['servico']}** - {row['materiais']}")
        c2.success(f"R$ {row['valor']:.2f}")
        
        with c3:
            linhas_pdf = [
                f"Orçamento: {row['servico']}",
                f"Materiais Necessários: {row['materiais']}",
                f"Valor Total Estimado: R$ {row['valor']:.2f}"
            ]
            pdf_orc = gerar_pdf_simples(f"Orçamento - {row['servico']}", linhas_pdf)
            st.download_button("🖨️ Imprimir", pdf_orc, file_name=f"Orcamento_{row['id']}.pdf", key=f"print_orc_{row['id']}")
            
            if st.button("🗑️ Excluir", key=f"del_orc_{row['id']}"):
                excluir_registro('orçamentos', row['id'])
    conn.close()