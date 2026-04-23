import streamlit as st
import pandas as pd
import bcrypt
from db import get_connection, excluir_registro

def render_usuarios():
    st.header("Gestão de Usuários e Acessos")

    if st.session_state.get('usuario_logado') != 'admin':
        st.error("Acesso Negado. Apenas o administrador do sistema pode ver esta página.")
        st.stop()

    tab1, tab2 = st.tabs(["Cadastrar Novo Usuário", "Usuários Ativos"])

    with tab1:
        st.write("Crie um login e senha para que seus funcionários possam acessar o sistema.")
        with st.form("form_novo_usuario", clear_on_submit=True):
            nome = st.text_input("Nome Completo do Funcionário", key="cad_nome")
            
            c1, c2 = st.columns(2)
            user = c1.text_input("Nome de Usuário (Ex: joao.silva)", key="cad_user")
            senha = c2.text_input("Senha Provisória", type="password", key="cad_senha")

            if st.form_submit_button("Cadastrar e Liberar Acesso", type="primary", use_container_width=True):
                if nome and user and senha:
                    conn = get_connection()
                    c = conn.cursor()
                    
                    c.execute("SELECT id FROM usuarios WHERE username = %s", (user.lower(),))
                    if c.fetchone():
                        st.error("Este Nome de Usuário já está em uso! Escolha outro.")
                    else:
                        salt = bcrypt.gensalt()
                        hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

                        c.execute("INSERT INTO usuarios (username, senha_hash, nome_completo) VALUES (%s,%s,%s)",
                                  (user.lower(), hash_senha, nome))
                        conn.commit()

                        for chave in ["cad_nome", "cad_user", "cad_senha"]:
                            if chave in st.session_state:
                                del st.session_state[chave]

                        st.session_state['msg_sucesso'] = f"Acesso liberado para '{nome}'!"
                        st.rerun()
                    conn.close()
                else:
                    st.warning("Preencha todos os campos para criar o acesso.")

    with tab2:
        st.write("Gerencie quem tem acesso à sua oficina.")
        conn = get_connection()
        df_users = pd.read_sql_query("SELECT id, username, nome_completo FROM usuarios", conn)

        with st.container(border=True):
            for _, row in df_users.iterrows():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{row['nome_completo']}**")
                c2.write(f"Login: `{row['username']}`")

                with c3:
                    if row['username'] == 'admin':
                        st.button("Admin (Protegido)", disabled=True, key=f"prot_{row['id']}", use_container_width=True)
                    else:
                        if st.button("🗑️ Remover Acesso", key=f"del_user_{row['id']}", use_container_width=True):
                            excluir_registro('usuarios', row['id'])
        conn.close()