import streamlit as st
import pandas as pd
import json
import base64
from datetime import datetime
from db import get_connection, excluir_registro
from pdf_utils import gerar_pdf_os_modelo, gerar_pdf_tabela

def extrair_descricao(json_str):
    try:
        itens = json.loads(json_str)
        if itens and isinstance(itens, list):
            return str(itens[0].get('Discriminação', ''))
        return ""
    except:
        return ""

def render_os():
    try:
        st.header("Central de Ordens de Serviço (O.S.)")
        
        tab1, tab2, tab3 = st.tabs(["Abrir Nova O.S. / Pedido", "Painel de Gerenciamento", "Relatório Geral"])

        # =========================================================
        # ABA 1: CRIAÇÃO
        # =========================================================
        with tab1:
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
            img_b64 = None
            
            if tipo == "Ordem de Serviço":
                st.write("**Descrição do Chamado**")
                descricao_servico = st.text_area("Descreva o que precisa ser executado ou o defeito relatado:", height=100, key="os_desc_servico")
                foto = st.file_uploader("📸 Anexar Foto do Problema (Opcional)", type=['png', 'jpg', 'jpeg'])
                if foto:
                    img_b64 = base64.b64encode(foto.read()).decode('utf-8')
                    st.image(foto, caption="Preview da Imagem", width=200)
            else:
                st.write("**Lista de Materiais Solicitados**")
                if 'df_os_base' not in st.session_state:
                    st.session_state.df_os_base = pd.DataFrame([{"Quant.": 1, "Discriminação": ""}])
                df_editado = st.data_editor(st.session_state.df_os_base, num_rows="dynamic", use_container_width=True, hide_index=True, key="os_tabela_itens")
            
            st.divider()
                
            if st.button("💾 Salvar Documento", type="primary", width="stretch"):
                if nome.strip() == "":
                    st.error("O Nome do solicitante é obrigatório.")
                else:
                    if tipo == "Ordem de Serviço":
                        itens_json = json.dumps([{"Quant.": "-", "Discriminação": st.session_state.get("os_desc_servico", "")}])
                    else:
                        itens_json = df_editado.to_json(orient='records')
                    
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute('''INSERT INTO os_detalhada 
                                 (tipo, data, nome, endereco, fone, celular, cnpj, modelo, itens_json, mao_obra, pecas, total_geral, status, imagem_base64) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', 
                              (tipo, data_doc.strftime("%d/%m/%Y"), nome, setor, fone, celular, cnpj, modelo, itens_json, 0.0, 0.0, 0.0, "Aberta", img_b64))
                    conn.commit()
                    conn.close()
                    
                    if 'df_os_base' in st.session_state: st.session_state.df_os_base = pd.DataFrame([{"Quant.": 1, "Discriminação": ""}])
                    for chave in ["os_nome", "os_setor", "os_fone", "os_cnpj", "os_modelo", "os_celular", "os_tabela_itens", "os_tipo", "os_desc_servico"]:
                        if chave in st.session_state: del st.session_state[chave]
                            
                    st.session_state['msg_sucesso'] = f"{tipo} aberta com sucesso!"
                    st.rerun()

        # =========================================================
        # ABA 2: PAINEL E TELA DE DETALHES COM CHAT
        # =========================================================
        with tab2:
            conn = get_connection()
            
            # --- TELA EXPANDIDA DA O.S. ---
            if 'view_os_id' in st.session_state and st.session_state['view_os_id'] is not None:
                os_id = st.session_state['view_os_id']
                
                if st.button("⬅️ Voltar para a lista"):
                    st.session_state['view_os_id'] = None
                    st.rerun()
                
                try:
                    df_detalhe = pd.read_sql_query("SELECT * FROM os_detalhada WHERE id = %s", conn, params=(os_id,))
                    if df_detalhe.empty:
                        st.error("Documento não encontrado.")
                        st.stop()
                    row = df_detalhe.iloc[0]
                except Exception as e:
                    st.error(f"Erro ao carregar O.S.: {e}")
                    st.stop()

                cor_status = "🟡" if row['status'] == 'Aberta' else "🟢"
                st.subheader(f"{cor_status} {row['tipo']} Nº {row['id']} - {row['status']}")
                
                with st.container(border=True):
                    c_info1, c_info2 = st.columns([2, 1])
                    with c_info1:
                        st.write(f"**Solicitante:** {row['nome']}")
                        st.write(f"**Setor:** {row['endereco']}")
                        st.write(f"**Equipamento:** {row['modelo']}")
                        st.write(f"**Data de Abertura:** {row['data']}")
                    
                    with c_info2:
                        itens_recuperados = json.loads(row['itens_json'])
                        pdf_file = gerar_pdf_os_modelo(row, itens_recuperados)
                        st.download_button("🖨️ Imprimir PDF Oficial", pdf_file, file_name=f"Doc_{row['id']}.pdf", width="stretch")
                        if st.button("🗑️ Excluir O.S.", type="secondary", width="stretch"):
                            excluir_registro('os_detalhada', row['id'])
                
                st.write("**Descrição/Itens:**")
                st.dataframe(pd.DataFrame(itens_recuperados), hide_index=True, use_container_width=True)
                
                if row.get('imagem_base64'):
                    st.write("**Foto do Problema:**")
                    img_data = base64.b64decode(row['imagem_base64'])
                    st.image(img_data, width=300)
                
                if 'parecer_tecnico' in row and pd.notna(row['parecer_tecnico']) and row['parecer_tecnico'].strip() and row['parecer_tecnico'] != 'None':
                    st.success(f"📋 **Parecer Técnico Final:**\n\n{row['parecer_tecnico']}")
                
                st.divider()

                # --- CHAT / COMENTÁRIOS ---
                st.subheader("💬 Interações e Atualizações")
                df_comentarios = pd.read_sql_query("SELECT * FROM comentarios WHERE os_id = %s ORDER BY id ASC", conn, params=(os_id,))
                
                with st.container(border=True):
                    if df_comentarios.empty:
                        st.info("Ainda não há mensagens registradas nesta O.S.")
                    else:
                        for _, c_row in df_comentarios.iterrows():
                            remetente = "user" if c_row['usuario'] == row['nome'] else "assistant"
                            with st.chat_message(remetente):
                                st.markdown(f"**{c_row['usuario']}** - *{c_row['data_hora']}*")
                                st.write(c_row['mensagem'])
                    
                    st.write("")
                    with st.form("form_chat", clear_on_submit=True):
                        nova_msg = st.text_area("Escreva um comentário ou atualização para a equipe:")
                        if st.form_submit_button("Enviar Mensagem", width="stretch"):
                            if nova_msg.strip():
                                cur = conn.cursor()
                                remetente_atual = st.session_state.get('nome_usuario', 'Usuário Desconhecido')
                                dh_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                                cur.execute("INSERT INTO comentarios (os_id, usuario, data_hora, mensagem) VALUES (%s,%s,%s,%s)", 
                                            (os_id, remetente_atual, dh_agora, nova_msg))
                                conn.commit()
                                st.rerun()

                # --- MÓDULO DE FINALIZAÇÃO ---
                if row['status'] == 'Aberta':
                    st.divider()
                    if row['tipo'] == 'Ordem de Serviço':
                        st.subheader("🛠️ Painel de Resolução")
                        mat_vinculados = pd.read_sql_query(f"SELECT m.id as mov_id, i.item, m.qtd as retirado, i.id as item_id FROM movimentacao m JOIN inventario i ON m.item_id = i.id WHERE m.os_id = {row['id']} AND m.status = 'Em Uso'", conn)
                        
                        with st.form(f"fechar_os_{row['id']}"):
                            st.write("**Parecer Técnico / Resolução do Chamado:**")
                            parecer = st.text_area("Descreva qual foi o defeito constatado e como foi solucionado:")
                            
                            usados_dict = {}
                            if not mat_vinculados.empty:
                                st.write("**Materiais Vinculados (Abater do Estoque):**")
                                for _, mat in mat_vinculados.iterrows():
                                    usados_dict[mat['mov_id']] = st.number_input(f"Usado de '{mat['item']}' (Retirado: {mat['retirado']})", min_value=0, max_value=int(mat['retirado']), value=int(mat['retirado']), key=f"usado_{row['id']}_{mat['mov_id']}")
                            
                            if st.form_submit_button("✔️ Salvar Parecer e Encerrar O.S.", type="primary", width="stretch"):
                                if parecer.strip() == "":
                                    st.error("O Parecer Técnico é obrigatório para fechar o chamado.")
                                else:
                                    cur = conn.cursor()
                                    if not mat_vinculados.empty:
                                        for mov_id, qtd_usada in usados_dict.items():
                                            mat_info = mat_vinculados[mat_vinculados['mov_id'] == mov_id].iloc[0]
                                            sobra = int(mat_info['retirado']) - int(qtd_usada)
                                            cur.execute('UPDATE movimentacao SET status = %s, data_retorno = %s WHERE id = %s', (f"Usado {qtd_usada} (Sobra {sobra} devolvida)", datetime.now().strftime("%d/%m/%Y %H:%M"), int(mov_id)))
                                            if sobra > 0: cur.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (sobra, int(mat_info['item_id'])))
                                    
                                    cur.execute("UPDATE os_detalhada SET status = 'Finalizada', parecer_tecnico = %s WHERE id = %s", (parecer, int(row['id'])))
                                    conn.commit()
                                    st.session_state['msg_sucesso'] = f"OS {row['id']} encerrada com sucesso!"
                                    st.rerun()

                    elif row['tipo'] == 'Pedido de Material':
                        st.subheader("📦 Dar Entrada no Estoque")
                        with st.form(f"receber_pedido_{row['id']}"):
                            st.write("**Confirmar Recebimento:**")
                            recebidos_dict = {}
                            for i, item_req in enumerate(itens_recuperados):
                                nome_item = item_req.get('Discriminação', '')
                                qtd_solicitada = int(item_req.get('Quant.', 0) if item_req.get('Quant.', 0) != '-' else 0)
                                if nome_item.strip():
                                    recebidos_dict[i] = {"nome": nome_item, "qtd": st.number_input(f"Recebido de '{nome_item}'", min_value=0, value=qtd_solicitada, key=f"rec_{row['id']}_{i}")}
                            
                            if st.form_submit_button("✔️ Receber Materiais e Finalizar", type="primary", width="stretch"):
                                cur = conn.cursor()
                                for idx, dados in recebidos_dict.items():
                                    if dados['qtd'] > 0:
                                        cur.execute("SELECT id FROM inventario WHERE LOWER(item) = LOWER(%s)", (dados['nome'].strip(),))
                                        resultado = cur.fetchone()
                                        if resultado: cur.execute('UPDATE inventario SET qtd = qtd + %s WHERE id = %s', (dados['qtd'], resultado[0]))
                                        else: cur.execute('INSERT INTO inventario (item, qtd, tipo) VALUES (%s,%s,%s)', (dados['nome'].strip(), dados['qtd'], "Material/Consumível"))
                                cur.execute("UPDATE os_detalhada SET status = 'Recebido (Estoque Atualizado)' WHERE id = %s", (int(row['id']),))
                                conn.commit()
                                st.session_state['msg_sucesso'] = f"Entrada do pedido {row['id']} concluída!"
                                st.rerun()

            # --- LISTA RESPONSIVA EM CARTÕES ---
            else:
                c1, c2 = st.columns([1, 2])
                eh_admin = st.session_state.get('usuario_logado') == 'admin'
                mostrar_apenas_meus = c1.checkbox("Mostrar apenas meus registros", value=not eh_admin)
                filtro_texto = c2.text_input("🔍 Buscar por Solicitante, Equipamento ou Setor:")
                
                try:
                    if mostrar_apenas_meus:
                        nome_logado = st.session_state.get('nome_usuario', '')
                        df_historico = pd.read_sql_query("SELECT * FROM os_detalhada WHERE nome = %s ORDER BY id DESC", conn, params=(nome_logado,))
                    else:
                        df_historico = pd.read_sql_query("SELECT * FROM os_detalhada ORDER BY id DESC", conn)
                except:
                    df_historico = pd.DataFrame()
                    
                if not df_historico.empty and filtro_texto:
                    df_historico = df_historico[
                        df_historico['modelo'].str.contains(filtro_texto, case=False, na=False) | 
                        df_historico['endereco'].str.contains(filtro_texto, case=False, na=False) |
                        df_historico['nome'].str.contains(filtro_texto, case=False, na=False)
                    ]
                    
                if not df_historico.empty:
                    df_historico['Descrição'] = df_historico['itens_json'].apply(extrair_descricao)
                    
                    df_abertas = df_historico[df_historico['status'] == 'Aberta']
                    df_concluidas = df_historico[df_historico['status'] != 'Aberta']
                    
                    aba_pendentes, aba_concluidas = st.tabs([f"🟡 Em Andamento ({len(df_abertas)})", f"🟢 Histórico ({len(df_concluidas)})"])
                    
                    with aba_pendentes:
                        if df_abertas.empty: 
                            st.info("Tudo limpo! Não há documentos pendentes com esse filtro.")
                        else:
                            st.write("Selecione um chamado para gerenciar:")
                            for _, row in df_abertas.iterrows():
                                with st.container(border=True):
                                    col_info, col_btn = st.columns([3, 1])
                                    with col_info:
                                        st.markdown(f"**#{row['id']} - {row['nome']}**")
                                        desc_curta = row['Descrição'][:60] + "..." if len(row['Descrição']) > 60 else row['Descrição']
                                        st.caption(f"🔧 **{row['tipo']}** | {desc_curta}")
                                    with col_btn:
                                        if st.button("Abrir ➔", key=f"btn_abrir_{row['id']}", width="stretch"):
                                            st.session_state['view_os_id'] = row['id']
                                            st.rerun()

                    with aba_concluidas:
                        if df_concluidas.empty: 
                            st.info("Nenhum documento finalizado com esse filtro.")
                        else:
                            st.write("Histórico de atendimentos:")
                            for _, row in df_concluidas.iterrows():
                                with st.container(border=True):
                                    col_info, col_btn = st.columns([3, 1])
                                    with col_info:
                                        st.markdown(f"**#{row['id']} - {row['nome']}**")
                                        st.caption(f"✅ Status: **{row['status']}** | Tipo: {row['tipo']}")
                                    with col_btn:
                                        if st.button("Ver Histórico", key=f"btn_ver_{row['id']}", width="stretch"):
                                            st.session_state['view_os_id'] = row['id']
                                            st.rerun()
                else:
                    st.info("Nenhum documento encontrado com estes filtros.")
            conn.close()

        # =========================================================
        # ABA 3: RELATÓRIO
        # =========================================================
        with tab3:
            st.write("### Relatório Resumo de Documentos")
            eh_admin_rel = st.session_state.get('usuario_logado') == 'admin'
            mostrar_meus_rel = st.checkbox("Mostrar apenas meus registros no relatório", value=not eh_admin_rel, key="filtro_relatorio")
            
            conn = get_connection()
            try:
                if mostrar_meus_rel:
                    nome_logado = st.session_state.get('nome_usuario', '')
                    df_relatorio = pd.read_sql_query('SELECT id as "Nº", tipo as "Tipo", data as "Data", nome as "Solicitante", endereco as "Setor", modelo as "Equipamento", status as "Status" FROM os_detalhada WHERE nome = %s ORDER BY id DESC', conn, params=(nome_logado,))
                else:
                    df_relatorio = pd.read_sql_query('SELECT id as "Nº", tipo as "Tipo", data as "Data", nome as "Solicitante", endereco as "Setor", modelo as "Equipamento", status as "Status" FROM os_detalhada ORDER BY id DESC', conn)
            except:
                df_relatorio = pd.DataFrame()
            
            if not df_relatorio.empty:
                st.dataframe(df_relatorio, use_container_width=True, hide_index=True)
                colunas = list(df_relatorio.columns)
                dados_pdf = [colunas] + df_relatorio.astype(str).values.tolist()
                
                if st.button("📄 Baixar PDF do Relatório", width="stretch"):
                    pdf = gerar_pdf_tabela(dados_pdf, "Relatório Geral de O.S. e Pedidos", modo_paisagem=True)
                    st.download_button(label="Baixar Relatório PDF", data=pdf, file_name=f"relatorio_os_{datetime.now().strftime('%d_%m_%Y')}.pdf", mime="application/pdf")
            else:
                st.info("Nenhum documento encontrado para gerar relatório.")
            conn.close()

    except Exception as e:
        st.error(f"Erro: {e}")