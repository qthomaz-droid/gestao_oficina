import streamlit as st
import bcrypt
from db import get_connection

def render_perfil():
    st.header("Meu Perfil")
    st.write("Gerencie suas credenciais de segurança.")

    with st.container(border=True):
        st.subheader("Alterar Senha de Acesso")
        
        with st.form("form_trocar_senha", clear_on_submit=True):
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha", type="password")

            if st.form_submit_button("Atualizar Senha", type="primary", use_container_width=True):
                if senha_atual and nova_senha and confirma_senha:
                    if nova_senha != confirma_senha:
                        st.error("A nova senha e a confirmação não são iguais.")
                    else:
                        username = st.session_state['usuario_logado']
                        conn = get_connection()
                        c = conn.cursor()
                        
                        # Busca a senha atual criptografada no banco
                        c.execute("SELECT senha_hash FROM usuarios WHERE username = %s", (username,))
                        resultado = c.fetchone()

                        if resultado:
                            senha_salva = resultado[0]
                            
                            # Verifica se a senha atual digitada está correta
                            if bcrypt.checkpw(senha_atual.encode('utf-8'), senha_salva.encode('utf-8')):
                                # Criptografa a nova senha
                                salt = bcrypt.gensalt()
                                novo_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), salt).decode('utf-8')

                                # Atualiza no banco de dados
                                c.execute("UPDATE usuarios SET senha_hash = %s WHERE username = %s", (novo_hash, username))
                                conn.commit()
                                
                                st.session_state['msg_sucesso'] = "Sua senha foi alterada com sucesso!"
                                st.rerun()
                            else:
                                st.error("A senha atual informada está incorreta.")
                        conn.close()
                else:
                    st.warning("Preencha todos os campos para alterar a senha.")