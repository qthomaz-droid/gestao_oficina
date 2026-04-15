import streamlit as st
import pandas as pd
from db import get_connection, excluir_registro
from pdf_utils import gerar_pdf_tabela

def render_estoque():
    st.header("Gestão de Inventário")

    tab1, tab2, tab3 = st.tabs(["Visão Geral do Estoque", "Entrada de Material (Reposição)", "Cadastrar Novo Item"])

    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM inventario ORDER BY item ASC', conn)

    with tab1:
        st.subheader("Itens Atuais no Inventário")
        hide_zero = st.checkbox("Esconder itens sem estoque (zerados)")
        
        df_exibicao = df[df['qtd'] > 0] if hide_zero else df
            
        for index, row in df_exibicao.iterrows():
            c1, c2, c3, c4 = st.columns([1, 3, 2, 1])
            c1.text(row['id'])
            c2.text(row['item'])
            c3.text(f"{row['tipo']} | Qtd: {row['qtd']}")
            if c4.button("🗑️", key=f"del_inv_{row['id']}"):
                excluir_registro('inventario', row['id'])
        
        if not df_exibicao.empty:
            dados_pdf = [["ID", "Item", "Tipo", "Estoque Atual"]] + df_exibicao.astype(str).values.tolist()
            if st.button("📄 Relatório PDF de Estoque"):
                pdf = gerar_pdf_tabela(dados_pdf, "Relatório de Estoque")
                st.download_button("Baixar Relatório", pdf, file_name="estoque.pdf")

    with tab2:
        st.write("Use esta aba para **adicionar saldo** a ferramentas ou materiais que já estão cadastrados.")
        if not df.empty:
            with st.form("form_entrada", clear_on_submit=True):
                opcoes_itens = {f"{row['item']} (Saldo Atual: {row['qtd']})": row['id'] for _, row in df.iterrows()}
                
                item_selecionado = st.selectbox("Selecione o Item para Reposição", options=list(opcoes_itens.keys()))
                qtd_adicionar = st.number_input("Quantidade a Adicionar", min_value=1, step=1)
                
                if st.form_submit_button("✔️ Confirmar Entrada", type="primary"):
                    id_item = opcoes_itens[item_selecionado]
                    
                    c = conn.cursor()
                    # CORREÇÃO: Utilizando %s
                    c.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (qtd_adicionar, id_item))
                    conn.commit()
                    
                    st.session_state['msg_sucesso'] = f"Entrada de {qtd_adicionar} un. registrada com sucesso!"
                    st.rerun()
        else:
            st.info("Nenhum item cadastrado ainda. Vá para a aba 'Cadastrar Novo Item'.")

    with tab3:
        st.write("Use esta aba apenas para itens que **nunca foram cadastrados** antes no sistema.")
        with st.form("form_add", clear_on_submit=True):
            item = st.text_input("Nome do Novo Item", key="inv_nome")
            tipo = st.selectbox("Tipo", ["Ferramenta", "Material/Consumível"], key="inv_tipo")
            qtd = st.number_input("Quantidade Inicial", min_value=0, key="inv_qtd")
            
            if st.form_submit_button("Salvar Novo Item"):
                if item.strip() == "":
                    st.error("O nome do item é obrigatório.")
                else:
                    c = conn.cursor()
                    # CORREÇÃO: Utilizando %s
                    c.execute('INSERT INTO inventario (item, qtd, tipo) VALUES (%s,%s,%s)', (item, qtd, tipo))
                    conn.commit()
                    
                    for chave in ["inv_nome", "inv_tipo", "inv_qtd"]:
                        if chave in st.session_state:
                            del st.session_state[chave]
                            
                    st.session_state['msg_sucesso'] = f"Item '{item}' cadastrado com sucesso!"
                    st.rerun()
                    
    conn.close()