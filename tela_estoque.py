import streamlit as st
import pandas as pd
from db import get_connection, excluir_registro
from pdf_utils import gerar_pdf_tabela

def render_estoque():
    st.header("Gestão de Inventário")

    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM inventario ORDER BY item ASC', conn)

    # --- ALERTA DE ESTOQUE MÍNIMO ---
    if not df.empty:
        df_alerta = df[df['qtd'] <= df['estoque_minimo']]
        if not df_alerta.empty:
            st.error("🚨 **Atenção! Os seguintes itens estão no estoque mínimo ou esgotados e precisam de reposição:**")
            st.dataframe(df_alerta[['item', 'qtd', 'estoque_minimo', 'tipo']], hide_index=True, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Visão Geral do Estoque", "Entrada de Material (Reposição)", "Cadastrar Novo Item"])

    with tab1:
        st.subheader("Itens Atuais no Inventário")
        hide_zero = st.checkbox("Esconder itens zerados")
        
        df_exibicao = df[df['qtd'] > 0] if hide_zero else df
            
        for index, row in df_exibicao.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    status_estoque = "🔴 Baixo" if row['qtd'] <= row['estoque_minimo'] else "🟢 OK"
                    st.markdown(f"**{row['item']}**")
                    st.caption(f"ID: {row['id']} | Tipo: {row['tipo']} | Qtd: **{row['qtd']}** (Mín: {row['estoque_minimo']}) | {status_estoque}")
                with c2:
                    if st.button("🗑️ Excluir", key=f"del_inv_{row['id']}", width="stretch"):
                        excluir_registro('inventario', row['id'])
        
        if not df_exibicao.empty:
            dados_pdf = [["ID", "Item", "Tipo", "Estoque", "Mínimo"]] + df_exibicao[['id','item','tipo','qtd','estoque_minimo']].astype(str).values.tolist()
            if st.button("📄 Relatório PDF de Estoque", width="stretch"):
                pdf = gerar_pdf_tabela(dados_pdf, "Relatório de Estoque")
                st.download_button("Baixar Relatório", pdf, file_name="estoque.pdf")

    with tab2:
        st.write("Adicione saldo a itens existentes.")
        if not df.empty:
            with st.form("form_entrada", clear_on_submit=True):
                opcoes_itens = {f"{row['item']} (Saldo: {row['qtd']})": row['id'] for _, row in df.iterrows()}
                item_selecionado = st.selectbox("Selecione o Item", options=list(opcoes_itens.keys()))
                qtd_adicionar = st.number_input("Quantidade a Adicionar", min_value=1, step=1)
                
                if st.form_submit_button("✔️ Confirmar Entrada", type="primary", width="stretch"):
                    id_item = opcoes_itens[item_selecionado]
                    c = conn.cursor()
                    c.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (qtd_adicionar, id_item))
                    conn.commit()
                    st.session_state['msg_sucesso'] = f"Entrada registrada com sucesso!"
                    st.rerun()
        else:
            st.info("Nenhum item cadastrado.")

    with tab3:
        st.write("Cadastre novos itens no inventário.")
        with st.form("form_add", clear_on_submit=True):
            item = st.text_input("Nome do Novo Item", key="inv_nome")
            c1, c2, c3 = st.columns(3)
            tipo = c1.selectbox("Tipo", ["Ferramenta", "Material/Consumível"], key="inv_tipo")
            qtd = c2.number_input("Quantidade Inicial", min_value=0, key="inv_qtd")
            estoque_min = c3.number_input("Estoque Mínimo Ideal", min_value=0, value=0, key="inv_min")
            
            if st.form_submit_button("Salvar Novo Item", width="stretch"):
                if item.strip() == "":
                    st.error("O nome é obrigatório.")
                else:
                    c = conn.cursor()
                    c.execute('INSERT INTO inventario (item, qtd, tipo, estoque_minimo) VALUES (%s,%s,%s,%s)', (item, qtd, tipo, estoque_min))
                    conn.commit()
                    for chave in ["inv_nome", "inv_tipo", "inv_qtd", "inv_min"]:
                        if chave in st.session_state: del st.session_state[chave]
                            
                    st.session_state['msg_sucesso'] = f"Item cadastrado com sucesso!"
                    st.rerun()
                    
    conn.close()