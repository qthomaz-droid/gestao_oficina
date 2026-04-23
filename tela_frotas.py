import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_connection, excluir_registro

def render_frotas():
    st.header("🚐 Controle de Frotas")
    
    tab1, tab2, tab3 = st.tabs(["Frota Atual e Cadastro", "Reservas e Agendamentos", "Manutenções"])
    conn = get_connection()
    
    try:
        df_veiculos = pd.read_sql_query("SELECT * FROM veiculos ORDER BY modelo ASC", conn)
    except:
        df_veiculos = pd.DataFrame()

    # ==========================================
    # ABA 1: FROTA E CADASTRO
    # ==========================================
    with tab1:
        st.subheader("Veículos Cadastrados")
        
        if df_veiculos.empty:
            st.info("Nenhum veículo cadastrado na frota ainda.")
        else:
            for _, row in df_veiculos.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        cor = "🟢" if row['status'] == 'Disponível' else "🟡" if row['status'] == 'Em Uso' else "🔴"
                        st.markdown(f"**{row['modelo']}** - Placa: `{row['placa']}`")
                        st.caption(f"Status: {cor} **{row['status']}** | KM Atual: {row['km_atual']} | Próx. Revisão: {row['proxima_revisao']}")
                    with c2:
                        if st.button("🗑️ Excluir", key=f"del_veic_{row['id']}", width="stretch"):
                            excluir_registro('veiculos', row['id'])
                            
        st.divider()
        st.subheader("➕ Adicionar Novo Veículo")
        with st.form("form_novo_veiculo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            modelo = col1.text_input("Modelo/Marca (Ex: Fiat Uno 2020)")
            placa = col2.text_input("Placa").upper()
            
            col3, col4, col5 = st.columns(3)
            km = col3.number_input("KM Atual", min_value=0)
            ult_rev = col4.date_input("Última Revisão", format="DD/MM/YYYY")
            prox_rev = col5.date_input("Próxima Revisão", format="DD/MM/YYYY")
            
            if st.form_submit_button("Cadastrar Veículo", type="primary", width="stretch"):
                if modelo and placa:
                    try:
                        c = conn.cursor()
                        c.execute('''INSERT INTO veiculos (placa, modelo, km_atual, ultima_revisao, proxima_revisao, status) 
                                     VALUES (%s,%s,%s,%s,%s,%s)''', 
                                  (placa, modelo, km, ult_rev.strftime("%d/%m/%Y"), prox_rev.strftime("%d/%m/%Y"), "Disponível"))
                        conn.commit()
                        st.session_state['msg_sucesso'] = f"Veículo {modelo} cadastrado!"
                        st.rerun()
                    except Exception as e:
                        st.error("Erro ao cadastrar. Verifique se a placa já existe.")
                else:
                    st.warning("Preencha Modelo e Placa.")

    # ==========================================
    # ABA 2: AGENDAMENTOS E RESERVAS
    # ==========================================
    with tab2:
        st.subheader("Agendar Uso de Veículo")
        
        veiculos_disp = df_veiculos[df_veiculos['status'] == 'Disponível'] if not df_veiculos.empty else pd.DataFrame()
        
        if not veiculos_disp.empty:
            with st.form("form_agendamento", clear_on_submit=True):
                opcoes_veiculos = {f"{row['modelo']} ({row['placa']})": row['id'] for _, row in veiculos_disp.iterrows()}
                veic_selecionado = st.selectbox("Selecione o Veículo Disponível:", options=list(opcoes_veiculos.keys()))
                
                c1, c2 = st.columns(2)
                data_ret = c1.date_input("Data de Retirada", format="DD/MM/YYYY")
                data_dev = c2.date_input("Data de Devolução (Prevista)", format="DD/MM/YYYY")
                
                motivo = st.text_input("Destino / Motivo do Uso:")
                nome_padrao = st.session_state.get('nome_usuario', '')
                
                if st.form_submit_button("✔️ Confirmar Reserva", type="primary", width="stretch"):
                    if motivo:
                        id_v = opcoes_veiculos[veic_selecionado]
                        c = conn.cursor()
                        c.execute('''INSERT INTO agendamentos_frota (veiculo_id, usuario, data_retirada, data_devolucao, motivo, status) 
                                     VALUES (%s,%s,%s,%s,%s,%s)''', 
                                  (id_v, nome_padrao, data_ret.strftime("%d/%m/%Y"), data_dev.strftime("%d/%m/%Y"), motivo, "Em Andamento"))
                        c.execute("UPDATE veiculos SET status = 'Em Uso' WHERE id = %s", (id_v,))
                        conn.commit()
                        st.session_state['msg_sucesso'] = "Veículo reservado com sucesso!"
                        st.rerun()
                    else:
                        st.warning("Informe o destino/motivo.")
        else:
            st.info("🚗 Não há veículos disponíveis para agendamento no momento.")

        st.divider()
        st.subheader("Veículos em Uso (Devoluções Pendentes)")
        
        try:
            df_em_uso = pd.read_sql_query('''
                SELECT a.id, v.modelo, v.placa, a.usuario, a.data_retirada, a.motivo, a.veiculo_id 
                FROM agendamentos_frota a 
                JOIN veiculos v ON a.veiculo_id = v.id 
                WHERE a.status = 'Em Andamento' 
            ''', conn)
        except:
            df_em_uso = pd.DataFrame()

        if not df_em_uso.empty:
            for _, row in df_em_uso.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{row['modelo']}** (`{row['placa']}`)")
                        st.caption(f"👤 Motorista: {row['usuario']} | 📅 Retirado: {row['data_retirada']} | 📍 Destino: {row['motivo']}")
                    with c2:
                        if st.button("🔙 Registrar Devolução", key=f"dev_frota_{row['id']}", width="stretch"):
                            c = conn.cursor()
                            c.execute("UPDATE agendamentos_frota SET status = 'Concluído', data_devolucao = %s WHERE id = %s", (datetime.now().strftime("%d/%m/%Y"), row['id']))
                            c.execute("UPDATE veiculos SET status = 'Disponível' WHERE id = %s", (row['veiculo_id'],))
                            conn.commit()
                            st.session_state['msg_sucesso'] = "Veículo devolvido à frota!"
                            st.rerun()
        else:
            st.success("Nenhum veículo em uso no momento.")

    # ==========================================
    # ABA 3: MANUTENÇÕES
    # ==========================================
    with tab3:
        st.subheader("Controle de Manutenção e KM")
        st.write("Atualize a quilometragem e o status de manutenção dos veículos da frota.")
        
        if not df_veiculos.empty:
            opcoes_todos = {f"{row['modelo']} ({row['placa']}) - Atual: {row['status']}": row['id'] for _, row in df_veiculos.iterrows()}
            veic_manut = st.selectbox("Selecione o Veículo:", options=list(opcoes_todos.keys()))
            id_manut = opcoes_todos[veic_manut]
            veic_dados = df_veiculos[df_veiculos['id'] == id_manut].iloc[0]
            
            with st.form("form_manutencao"):
                st.write(f"**Atualizando: {veic_dados['modelo']}**")
                
                c1, c2 = st.columns(2)
                novo_km = c1.number_input("Atualizar KM Atual", min_value=0, value=int(veic_dados['km_atual']))
                novo_status = c2.selectbox("Alterar Status", ["Disponível", "Manutenção", "Em Uso"], index=["Disponível", "Manutenção", "Em Uso"].index(veic_dados['status']))
                
                c3, c4 = st.columns(2)
                
                try: ult_rev_date = datetime.strptime(veic_dados['ultima_revisao'], "%d/%m/%Y")
                except: ult_rev_date = datetime.now()
                try: prox_rev_date = datetime.strptime(veic_dados['proxima_revisao'], "%d/%m/%Y")
                except: prox_rev_date = datetime.now()
                
                nova_ult_rev = c3.date_input("Nova Última Revisão", value=ult_rev_date, format="DD/MM/YYYY")
                nova_prox_rev = c4.date_input("Nova Próxima Revisão", value=prox_rev_date, format="DD/MM/YYYY")
                
                if st.form_submit_button("💾 Salvar Atualizações", type="primary", width="stretch"):
                    c = conn.cursor()
                    c.execute('''UPDATE veiculos 
                                 SET km_atual = %s, status = %s, ultima_revisao = %s, proxima_revisao = %s 
                                 WHERE id = %s''', 
                              (novo_km, novo_status, nova_ult_rev.strftime("%d/%m/%Y"), nova_prox_rev.strftime("%d/%m/%Y"), id_manut))
                    conn.commit()
                    st.session_state['msg_sucesso'] = "Dados do veículo atualizados!"
                    st.rerun()
        else:
            st.info("Cadastre veículos na aba 'Frota Atual' primeiro.")

    conn.close()