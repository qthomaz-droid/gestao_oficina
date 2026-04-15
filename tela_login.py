import streamlit as st
import bcrypt
from db import get_connection

def render_login():
    st.markdown("<h1 style='text-align: center;'>Sistema de Gestão</h1>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.container(border=True):
            st.subheader("Acesso Restrito")
            
            with st.form("form_login"):
                username = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
                    if username and senha:
                        conn = get_connection()
                        c = conn.cursor()
                        # CORREÇÃO: Utilizando %s
                        c.execute("SELECT senha_hash, nome_completo FROM usuarios WHERE username = %s", (username,))
                        resultado = c.fetchone()
                        conn.close()
                        
                        if resultado:
                            senha_salva = resultado[0]
                            nome_usuario = resultado[1]
                            
                            if bcrypt.checkpw(senha.encode('utf-8'), senha_salva.encode('utf-8')):
                                st.session_state['usuario_logado'] = username
                                st.session_state['nome_usuario'] = nome_usuario
                                st.rerun() 
                            else:
                                st.error("Senha incorreta.")
                        else:
                            st.error("Usuário não encontrado.")
                    else:
                        st.warning("Preencha todos os campos.")