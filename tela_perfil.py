import streamlit as st
import bcrypt
from db import get_connection

# NOVO: Recebendo o controller para poder atualizar o cookie do navegador
def render_perfil(controller):
    st.header("Meu Perfil")
    st.write("Gerencie suas credenciais e dados pessoais.")

    # Dividindo a tela em abas para melhor organização
    tab_nome, tab_senha = st.tabs(["👤 Alterar Nome", "🔒 Mudar Senha"])

    # ==========================================
    # ABA 1: ALTERAR NOME
    # ==========================================
    with tab_nome:
        st.write("Atualize como você é chamado no menu do sistema.")
        with st.form("form_trocar_nome"):
            # Traz o nome atual do usuário já preenchido na caixa
            novo_nome = st.text_input("Seu Nome Completo", value=st.session_state.get('nome_usuario', ''))
            
            if st.form_submit_button("Atualizar Nome", type="primary", width="stretch"):
                if novo_nome.strip() == "":
                    st.error("O nome não pode ficar em branco.")
                elif novo_nome == st.session_state.get('nome_usuario'):
                    st.warning("O nome digitado é igual ao atual.")
                else:
                    username = st.session_state['usuario_logado']
                    conn = get_connection()
                    c = conn.cursor()
                    
                    # Atualiza o nome no banco de dados
                    c.execute("UPDATE usuarios SET nome_completo = %s WHERE username = %s", (novo_nome, username))
                    conn.commit()
                    conn.close()

                    # Atualiza a memória temporária (session_state)
                    st.session_state['nome_usuario'] = novo_nome
                    
                    # Atualiza o Cookie do navegador (para o nome não sumir no F5)
                    controller.set('nome_usuario', novo_nome, max_age=604800)

                    st.session_state['msg_sucesso'] = "Nome atualizado com sucesso!"
                    st.rerun()

    # ==========================================
    # ABA 2: MUDAR SENHA (Código que já tínhamos)
    # ==========================================
    with tab_senha:
        st.write("Por segurança, informe sua senha atual para criar uma nova.")
        with st.form("form_trocar_senha", clear_on_submit=True):
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha", type="password")

            if st.form_submit_button("Atualizar Senha", type="primary", width="stretch"):
                if senha_atual and nova_senha and confirma_senha:
                    if nova_senha != confirma_senha:
                        st.error("A nova senha e a confirmação não são iguais.")
                    else:
                        username = st.session_state['usuario_logado']
                        conn = get_connection()
                        c = conn.cursor()
                        
                        c.execute("SELECT senha_hash FROM usuarios WHERE username = %s", (username,))
                        resultado = c.fetchone()

                        if resultado:
                            senha_salva = resultado[0]
                            if bcrypt.checkpw(senha_atual.encode('utf-8'), senha_salva.encode('utf-8')):
                                salt = bcrypt.gensalt()
                                novo_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), salt).decode('utf-8')

                                c.execute("UPDATE usuarios SET senha_hash = %s WHERE username = %s", (novo_hash, username))
                                conn.commit()
                                
                                st.session_state['msg_sucesso'] = "Sua senha foi alterada com sucesso!"
                                st.rerun()
                            else:
                                st.error("A senha atual informada está incorreta.")
                        conn.close()
                else:
                    st.warning("Preencha todos os campos para alterar a senha.")