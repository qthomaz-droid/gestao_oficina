import streamlit as st
from db import create_tables, exibir_notificacoes

from tela_login import render_login
from tela_estoque import render_estoque
from tela_movimentacao import render_movimentacao
from tela_os import render_os
from tela_orcamentos import render_orcamentos
from tela_usuarios import render_usuarios 
from tela_perfil import render_perfil

st.set_page_config(page_title="Sistema Interno", layout="wide")

create_tables()

if 'usuario_logado' not in st.session_state:
    render_login()
else:
    exibir_notificacoes()

    st.sidebar.markdown(f"Bem-vindo, **{st.session_state['nome_usuario']}**")
    
    if st.sidebar.button("Sair do Sistema", use_container_width=True):
        del st.session_state['usuario_logado']
        del st.session_state['nome_usuario']
        st.rerun()
        
    st.sidebar.divider()

    pagina_mov = st.Page(page=render_movimentacao, title="Retiradas e Devoluções")
    pagina_os = st.Page(page=render_os, title="Ordens de Serviço")
    pagina_estoque = st.Page(page=render_estoque, title="Gestão de Estoque")
    pagina_orc = st.Page(page=render_orcamentos, title="Orçamentos")
    pagina_usuarios = st.Page(page=render_usuarios, title="Gerenciar Usuários")
    pagina_perfil = st.Page(page=render_perfil, title="Meu Perfil")

    if st.session_state['usuario_logado'] == 'admin':
        menu_opcoes = {
            "Operacional": [pagina_estoque, pagina_mov, pagina_os, pagina_orc],
            "Administração": [pagina_usuarios],
            "Configurações": [pagina_perfil]
        }
    else:
        menu_opcoes = {
            "Operacional": [pagina_mov, pagina_os],
            "Configurações": [pagina_perfil]
        }

    pg = st.navigation(menu_opcoes)
    pg.run()