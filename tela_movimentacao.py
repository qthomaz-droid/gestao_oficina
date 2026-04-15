import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_connection
from pdf_utils import gerar_pdf_tabela

def render_movimentacao():
    st.header("Controle de Movimentação")
    tab1, tab2, tab3 = st.tabs(["Nova Retirada", "Devoluções Pendentes", "Histórico Geral"])
    
    conn = get_connection()
    disponiveis = pd.read_sql_query('SELECT * FROM inventario WHERE qtd > 0', conn)
    
    try:
        os_abertas = pd.read_sql_query("SELECT id, nome || ' - ' || modelo as descricao FROM os_detalhada WHERE status = 'Aberta'", conn)
    except:
        os_abertas = pd.DataFrame(columns=['id', 'descricao'])
    
    with tab1:
        if not disponiveis.empty:
            with st.form("retirada", clear_on_submit=True):
                item_id = st.selectbox("Selecione o Item", options=disponiveis['id'], 
                                       format_func=lambda x: f"{disponiveis[disponiveis['id']==x]['item'].values[0]} (Estoque: {disponiveis[disponiveis['id']==x]['qtd'].values[0]})")
                
                item_selecionado = disponiveis[disponiveis['id'] == item_id].iloc[0]
                max_qtd = int(item_selecionado['qtd'])
                
                qtd_retirar = st.number_input("Quantidade a Retirar", min_value=1, max_value=max_qtd, value=1)
                user = st.text_input("Responsável pela retirada")
                
                opcoes_os = {"Nenhuma": None}
                for _, row in os_abertas.iterrows():
                    opcoes_os[f"OS {row['id']} - {row['descricao']}"] = row['id']
                
                os_selecionada = st.selectbox("Vincular à Ordem de Serviço (Opcional)", options=list(opcoes_os.keys()))
                
                if st.form_submit_button("Confirmar Saída"):
                    if user:
                        os_id = opcoes_os[os_selecionada]
                        c = conn.cursor()
                        c.execute('''INSERT INTO movimentacao (item_id, usuario, qtd, os_id, data_saida, status) 
                                     VALUES (?,?,?,?,?,?)''', 
                                  (item_id, user, qtd_retirar, os_id, datetime.now().strftime("%d/%m/%Y %H:%M"), "Em Uso"))
                        c.execute('UPDATE inventario SET qtd = qtd - ? WHERE id = ?', (qtd_retirar, item_id))
                        conn.commit()
                        st.session_state['msg_sucesso'] = f"Retirada de {qtd_retirar} un. registrada para {user}!"
                        st.rerun()
                    else:
                        st.error("Informe o responsável.")

    with tab2:
        st.subheader("Ferramentas em Uso (Pendentes de Devolução)")
        
        pendentes = pd.read_sql_query('''
            SELECT m.id, i.item, m.usuario, m.qtd, m.data_saida, i.id as item_id, m.os_id 
            FROM movimentacao m 
            JOIN inventario i ON m.item_id = i.id 
            WHERE m.status = 'Em Uso' AND i.tipo = 'Ferramenta' ''', conn)
        
        if not pendentes.empty:
            for _, row in pendentes.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                info_os = f" (OS {row['os_id']})" if pd.notna(row['os_id']) else ""
                c1.write(f"**{row['item']}** x{row['qtd']}{info_os}")
                c2.write(f"Responsável: {row['usuario']}")
                c3.write(f"Data: {row['data_saida']}")
                if c4.button("🔙 Devolver Total", key=f"dev_{row['id']}"):
                    c = conn.cursor()
                    c.execute('UPDATE movimentacao SET status = ?, data_retorno = ? WHERE id = ?', 
                              ("Devolvido", datetime.now().strftime("%d/%m/%Y %H:%M"), row['id']))
                    c.execute('UPDATE inventario SET qtd = qtd + ? WHERE id = ?', (row['qtd'], row['item_id']))
                    conn.commit()
                    st.session_state['msg_sucesso'] = f"Ferramenta devolvida ao estoque!"
                    st.rerun()
        else:
            st.info("Não existem ferramentas pendentes de devolução.")

    with tab3:
        st.subheader("Relatório de Movimentações")
        historico = pd.read_sql_query('''
            SELECT m.usuario as "Responsável", 
                   i.item as "Item", 
                   m.qtd as "Qtd", 
                   m.data_saida as "Data Saída", 
                   m.data_retorno as "Data Retorno",
                   m.status as "Situação"
            FROM movimentacao m 
            JOIN inventario i ON m.item_id = i.id 
            ORDER BY m.id DESC''', conn)
        
        st.dataframe(historico, use_container_width=True)
        
        if not historico.empty:
            colunas = list(historico.columns)
            dados_pdf = [colunas] + historico.astype(str).values.tolist()
            
            if st.button("📄 Gerar PDF de Retiradas"):
                pdf = gerar_pdf_tabela(dados_pdf, "Relatório Geral de Retiradas", modo_paisagem=True)
                st.download_button(
                    label="Baixar Relatório PDF",
                    data=pdf,
                    file_name=f"relatorio_movimentacao_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf"
                )
    
    conn.close()