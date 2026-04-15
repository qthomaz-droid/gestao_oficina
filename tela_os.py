import streamlit as st
import pandas as pd
import json
from datetime import datetime
from db import get_connection, excluir_registro
from pdf_utils import gerar_pdf_os_modelo, gerar_pdf_tabela

def render_os():
    try:
        st.header("Central de Ordens de Serviço (O.S.)")
        
        tab1, tab2, tab3 = st.tabs(["Abrir Nova O.S. / Pedido", "Painel de Gerenciamento", "Relatório Geral"])

        with tab1:
            st.write("Preencha os dados abaixo para registrar um serviço ou solicitar materiais.")
            
            c1, c2 = st.columns([3, 1])
            tipo = c1.radio("O que você deseja fazer?", ["Ordem de Serviço", "Pedido de Material"], horizontal=True, key="os_tipo")
            data_doc = c2.date_input("Data de Abertura", key="os_data")
            
            with st.container(border=True):
                col_n, col_e, col_f = st.columns([2, 2, 1])
                nome_padrao = st.session_state.get('nome_usuario', '')
                nome = col_n.text_input("Nome/Solicitante:", value=nome_padrao, key="os_nome")
                setor = col_e.text_input("Setor:", key="os_setor")
                fone = col_f.text_input("Fone:", key="os_fone")
                
                col_c, col_m, col_cel = st.columns([2, 2, 1])
                cnpj = col_c.text_input("CNPJ/Matrícula:", key="os_cnpj")
                modelo = col_m.text_input("Equipamento/Modelo:", key="os_modelo")
                celular = col_cel.text_input("Celular:", key="os_celular")
                
            st.write("")
            
            if tipo == "Ordem de Serviço":
                st.write("**Descrição da Ordem de Serviço**")
                descricao_servico = st.text_area("Descreva detalhadamente o que precisa ser executado ou o problema relatado:", height=150, key="os_desc_servico")
            else:
                st.write("**Lista de Materiais Solicitados**")
                st.caption("Adicione as quantidades e os nomes dos materiais.")
                if 'df_os_base' not in st.session_state:
                    st.session_state.df_os_base = pd.DataFrame([{"Quant.": 1, "Discriminação": ""}])
                    
                df_editado = st.data_editor(
                    st.session_state.df_os_base,
                    num_rows="dynamic", 
                    use_container_width=True,
                    hide_index=True,
                    key="os_tabela_itens", 
                    column_config={
                        "Quant.": st.column_config.NumberColumn("Quant.", min_value=0, step=1),
                        "Discriminação": st.column_config.TextColumn("Discriminação", width="large")
                    }
                )
                df_editado["Quant."] = df_editado["Quant."].fillna(0)
            
            st.divider()
                
            if st.button("💾 Salvar Documento", type="primary", use_container_width=True):
                if nome.strip() == "":
                    st.error("O Nome do solicitante é obrigatório.")
                elif tipo == "Ordem de Serviço" and not st.session_state.get("os_desc_servico", "").strip():
                    st.error("A descrição do serviço não pode ficar vazia.")
                else:
                    if tipo == "Ordem de Serviço":
                        itens_json = json.dumps([{"Quant.": "-", "Discriminação": st.session_state["os_desc_servico"]}])
                    else:
                        itens_json = df_editado.to_json(orient='records')
                    
                    conn = get_connection()
                    c = conn.cursor()
                    # CORREÇÃO: Utilizando %s
                    c.execute('''INSERT INTO os_detalhada 
                                 (tipo, data, nome, endereco, fone, celular, cnpj, modelo, itens_json, mao_obra, pecas, total_geral, status) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', 
                              (tipo, data_doc.strftime("%d/%m/%Y"), nome, setor, fone, celular, cnpj, modelo, itens_json, 0.0, 0.0, 0.0, "Aberta"))
                    conn.commit()
                    conn.close()
                    
                    if 'df_os_base' in st.session_state:
                        st.session_state.df_os_base = pd.DataFrame([{"Quant.": 1, "Discriminação": ""}])
                    
                    chaves_para_limpar = ["os_nome", "os_setor", "os_fone", "os_cnpj", "os_modelo", "os_celular", "os_tabela_itens", "os_tipo", "os_desc_servico"]
                    for chave in chaves_para_limpar:
                        if chave in st.session_state:
                            del st.session_state[chave]
                            
                    st.session_state['msg_sucesso'] = f"{tipo} aberta com sucesso!"
                    st.rerun()

        with tab2:
            st.write("### Controle e Acompanhamento")
            
            eh_admin = st.session_state.get('usuario_logado') == 'admin'
            mostrar_apenas_meus = st.checkbox("Mostrar apenas meus registros", value=not eh_admin)
            
            conn = get_connection()
            try:
                if mostrar_apenas_meus:
                    nome_logado = st.session_state.get('nome_usuario', '')
                    # CORREÇÃO: Utilizando %s
                    df_historico = pd.read_sql_query("SELECT * FROM os_detalhada WHERE nome = %s ORDER BY id DESC", conn, params=(nome_logado,))
                else:
                    df_historico = pd.read_sql_query("SELECT * FROM os_detalhada ORDER BY id DESC", conn)
            except:
                df_historico = pd.DataFrame()
                
            if not df_historico.empty:
                df_abertas = df_historico[df_historico['status'] == 'Aberta']
                df_concluidas = df_historico[df_historico['status'] != 'Aberta']
                
                m1, m2, m3 = st.columns(3)
                m1.metric("🟡 Pendentes", len(df_abertas))
                m2.metric("🟢 Concluídas", len(df_concluidas))
                m3.metric("📋 Total de Registros", len(df_historico))
                
                st.write("")
                
                aba_pendentes, aba_concluidas = st.tabs(["🟡 Em Andamento", "🟢 Histórico Fechado"])
                
                with aba_pendentes:
                    if df_abertas.empty:
                        st.info("Tudo limpo! Não há documentos pendentes.")
                    else:
                        for _, row in df_abertas.iterrows():
                            with st.expander(f"🟡 Nº {row['id']} | {row['tipo']} | Solicitante: {row['nome']}"):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.write(f"**Data:** {row['data']} | **Setor:** {row['endereco']} | **Equip.:** {row['modelo']}")
                                    itens_recuperados = json.loads(row['itens_json'])
                                    df_exibicao = pd.DataFrame(itens_recuperados)
                                    if "Unit. R$" in df_exibicao.columns:
                                        df_exibicao = df_exibicao.drop(columns=["Unit. R$", "Total R$"])
                                    st.dataframe(df_exibicao, hide_index=True, use_container_width=True)
                                
                                with c2:
                                    pdf_file = gerar_pdf_os_modelo(row, itens_recuperados)
                                    st.download_button("🖨️ PDF Oficial", pdf_file, file_name=f"Doc_{row['id']}.pdf", key=f"p_ab_{row['id']}")
                                    if st.button("🗑️ Excluir", key=f"del_ab_{row['id']}"):
                                        excluir_registro('os_detalhada', row['id'])

                                if row['tipo'] == 'Ordem de Serviço':
                                    st.divider()
                                    st.subheader("Finalizar O.S.")
                                    mat_vinculados = pd.read_sql_query(f"SELECT m.id as mov_id, i.item, m.qtd as retirado, i.id as item_id FROM movimentacao m JOIN inventario i ON m.item_id = i.id WHERE m.os_id = {row['id']} AND m.status = 'Em Uso'", conn)
                                    
                                    if not mat_vinculados.empty:
                                        with st.form(f"fechar_os_{row['id']}"):
                                            st.info("Informe a quantidade usada para abater do estoque.")
                                            usados_dict = {}
                                            for _, mat in mat_vinculados.iterrows():
                                                usados_dict[mat['mov_id']] = st.number_input(f"Usado de '{mat['item']}' (Retirado: {mat['retirado']})", min_value=0, max_value=int(mat['retirado']), value=int(mat['retirado']), key=f"usado_{row['id']}_{mat['mov_id']}")
                                            
                                            if st.form_submit_button("✔️ Encerrar OS"):
                                                c = conn.cursor()
                                                for mov_id, qtd_usada in usados_dict.items():
                                                    mat_info = mat_vinculados[mat_vinculados['mov_id'] == mov_id].iloc[0]
                                                    sobra = int(mat_info['retirado']) - int(qtd_usada)
                                                    # CORREÇÃO: Utilizando %s
                                                    c.execute('UPDATE movimentacao SET status = %s, data_retorno = %s WHERE id = %s', (f"Usado {qtd_usada} (Sobra {sobra} devolvida)", datetime.now().strftime("%d/%m/%Y %H:%M"), int(mov_id)))
                                                    if sobra > 0:
                                                        c.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (sobra, int(mat_info['item_id'])))
                                                c.execute("UPDATE os_detalhada SET status = 'Finalizada' WHERE id = %s", (int(row['id']),))
                                                conn.commit()
                                                st.session_state['msg_sucesso'] = f"OS {row['id']} encerrada e estoque atualizado!"
                                                st.rerun()
                                    else:
                                        if st.button("Finalizar OS (Sem materiais vinculados)", key=f"fin_simples_{row['id']}"):
                                            c = conn.cursor()
                                            # CORREÇÃO: Utilizando %s
                                            c.execute("UPDATE os_detalhada SET status = 'Finalizada' WHERE id = %s", (int(row['id']),))
                                            conn.commit()
                                            st.session_state['msg_sucesso'] = f"OS {row['id']} finalizada!"
                                            st.rerun()

                                elif row['tipo'] == 'Pedido de Material':
                                    st.divider()
                                    st.subheader("Dar Entrada no Estoque")
                                    with st.form(f"receber_pedido_{row['id']}"):
                                        recebidos_dict = {}
                                        for i, item_req in enumerate(itens_recuperados):
                                            nome_item = item_req.get('Discriminação', '')
                                            qtd_solicitada = int(item_req.get('Quant.', 0) if item_req.get('Quant.', 0) != '-' else 0)
                                            if nome_item.strip():
                                                recebidos_dict[i] = {"nome": nome_item, "qtd": st.number_input(f"Recebido de '{nome_item}'", min_value=0, value=qtd_solicitada, key=f"rec_{row['id']}_{i}")}
                                        
                                        if st.form_submit_button("✔️ Receber Materiais"):
                                            c = conn.cursor()
                                            for idx, dados in recebidos_dict.items():
                                                if dados['qtd'] > 0:
                                                    # CORREÇÃO: Utilizando %s
                                                    c.execute("SELECT id FROM inventario WHERE LOWER(item) = LOWER(%s)", (dados['nome'].strip(),))
                                                    resultado = c.fetchone()
                                                    if resultado:
                                                        c.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (dados['qtd'], resultado[0]))
                                                    else:
                                                        c.execute('INSERT INTO inventario (item, qtd, tipo) VALUES (%s,%s,%s)', (dados['nome'].strip(), dados['qtd'], "Material/Consumível"))
                                            c.execute("UPDATE os_detalhada SET status = 'Recebido (Estoque Atualizado)' WHERE id = %s", (int(row['id']),))
                                            conn.commit()
                                            st.session_state['msg_sucesso'] = f"Entrada do pedido {row['id']} concluída!"
                                            st.rerun()

                with aba_concluidas:
                    if df_concluidas.empty:
                        st.info("Nenhum documento finalizado ainda.")
                    else:
                        for _, row in df_concluidas.iterrows():
                            with st.expander(f"🟢 Nº {row['id']} | {row['tipo']} | Solicitante: {row['nome']}"):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.write(f"**Data:** {row['data']} | **Setor:** {row['endereco']} | **Equip.:** {row['modelo']}")
                                    st.write(f"**Status Final:** {row['status']}")
                                    itens_recuperados = json.loads(row['itens_json'])
                                    df_exibicao = pd.DataFrame(itens_recuperados)
                                    if "Unit. R$" in df_exibicao.columns:
                                        df_exibicao = df_exibicao.drop(columns=["Unit. R$", "Total R$"])
                                    st.dataframe(df_exibicao, hide_index=True, use_container_width=True)
                                
                                with c2:
                                    pdf_file = gerar_pdf_os_modelo(row, itens_recuperados)
                                    st.download_button("🖨️ PDF Oficial", pdf_file, file_name=f"Doc_{row['id']}.pdf", key=f"p_fech_{row['id']}")
                                    if st.button("🗑️ Excluir", key=f"del_fech_{row['id']}"):
                                        excluir_registro('os_detalhada', row['id'])
            else:
                st.info("Nenhum documento encontrado.")
            conn.close()

        with tab3:
            st.write("### Relatório Resumo de Documentos")
            
            eh_admin_rel = st.session_state.get('usuario_logado') == 'admin'
            mostrar_meus_rel = st.checkbox("Mostrar apenas meus registros no relatório", value=not eh_admin_rel, key="filtro_relatorio")
            
            conn = get_connection()
            try:
                if mostrar_meus_rel:
                    nome_logado = st.session_state.get('nome_usuario', '')
                    # CORREÇÃO: Utilizando %s
                    df_relatorio = pd.read_sql_query('''
                        SELECT id as "Nº", tipo as "Tipo", data as "Data", 
                               nome as "Solicitante", endereco as "Setor", 
                               modelo as "Equipamento", status as "Status"
                        FROM os_detalhada WHERE nome = %s ORDER BY id DESC''', conn, params=(nome_logado,))
                else:
                    df_relatorio = pd.read_sql_query('''
                        SELECT id as "Nº", tipo as "Tipo", data as "Data", 
                               nome as "Solicitante", endereco as "Setor", 
                               modelo as "Equipamento", status as "Status"
                        FROM os_detalhada ORDER BY id DESC''', conn)
            except:
                df_relatorio = pd.DataFrame()
            
            if not df_relatorio.empty:
                st.dataframe(df_relatorio, use_container_width=True, hide_index=True)
                
                colunas = list(df_relatorio.columns)
                dados_pdf = [colunas] + df_relatorio.astype(str).values.tolist()
                
                if st.button("📄 Baixar PDF do Relatório"):
                    pdf = gerar_pdf_tabela(dados_pdf, "Relatório Geral de O.S. e Pedidos", modo_paisagem=True)
                    st.download_button(
                        label="Baixar Relatório PDF",
                        data=pdf,
                        file_name=f"relatorio_os_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.info("Nenhum documento encontrado para gerar relatório.")
            conn.close()

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a tela de OS: {e}")