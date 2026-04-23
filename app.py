import streamlit as st
import warnings

# Silencia o aviso do Pandas sobre o SQLAlchemy
warnings.filterwarnings('ignore', message='.*SQLAlchemy.*') 

from db import create_tables, exibir_notificacoes
from streamlit_cookies_controller import CookieController

from tela_login import render_login
from tela_estoque import render_estoque
from tela_movimentacao import render_movimentacao
from tela_os import render_os
from tela_orcamentos import render_orcamentos
from tela_usuarios import render_usuarios 
from tela_perfil import render_perfil
from tela_dashboard import render_dashboard 
from tela_frotas import render_frotas # IMPORTANDO O NOVO MÓDULO DE FROTAS

st.set_page_config(page_title="Sistema Interno", layout="wide")

# CSS Responsivo (Mobile-First) e Barra de Rolagem
st.markdown("""
    <style>
    /* Destrava a rolagem em tablets/Chromebooks */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
        overflow-y: auto !important;
        overscroll-behavior: auto !important;
        touch-action: pan-y !important;
    }
    .stApp { height: auto !important; }
    
    /* Customização da Barra de Rolagem */
    ::-webkit-scrollbar { width: 8px !important; height: 8px !important; background: transparent !important; }
    ::-webkit-scrollbar-track { background: #f1f1f1 !important; }
    ::-webkit-scrollbar-thumb { background: #c1c1c1 !important; border-radius: 10px !important; }
    ::-webkit-scrollbar-thumb:hover { background: #888 !important; }
    
    /* REGRAS PARA CELULARES E TABLETS (Responsividade Máxima) */
    @media (max-width: 768px) {
        [data-testid="stAppViewBlockContainer"] { padding: 1rem 0.5rem !important; }
        .stButton > button { width: 100% !important; margin-top: 5px; }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.2rem !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 0.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

create_tables()

# Inicializa o leitor de Cookies UMA ÚNICA VEZ
controller = CookieController()

if 'usuario_logado' not in st.session_state:
    cookie_user = controller.get('usuario_logado')
    cookie_nome = controller.get('nome_usuario')
    
    if cookie_user and cookie_nome:
        st.session_state['usuario_logado'] = cookie_user
        st.session_state['nome_usuario'] = cookie_nome

if 'usuario_logado' not in st.session_state:
    render_login(controller)
else:
    exibir_notificacoes()

    st.sidebar.markdown(f"Bem-vindo, **{st.session_state['nome_usuario']}**")
    
    if st.sidebar.button("Sair do Sistema", width="stretch"):
        controller.remove('usuario_logado')
        controller.remove('nome_usuario')
        del st.session_state['usuario_logado']
        del st.session_state['nome_usuario']
        st.rerun()
        
    st.sidebar.divider()

    # Configuração das Páginas do Menu
    pagina_dash = st.Page(page=render_dashboard, title="Dashboard", icon="📊")
    pagina_mov = st.Page(page=render_movimentacao, title="Retiradas e Devoluções", icon="🔑")
    pagina_os = st.Page(page=render_os, title="Ordens de Serviço", icon="📝")
    pagina_estoque = st.Page(page=render_estoque, title="Gestão de Estoque", icon="📦")
    pagina_orc = st.Page(page=render_orcamentos, title="Orçamentos", icon="💰")
    pagina_usuarios = st.Page(page=render_usuarios, title="Gerenciar Usuários", icon="👥")
    pagina_frotas = st.Page(page=render_frotas, title="Gestão de Frotas", icon="🚐") # NOVA PÁGINA ADICIONADA
    
    # Wrapper para o Perfil com Cookies
    def perfil_com_cookie():
        render_perfil(controller)
        
    pagina_perfil = st.Page(page=perfil_com_cookie, title="Meu Perfil", icon="🛡️")

    # Permissões do Menu
    if st.session_state['usuario_logado'] == 'admin':
        menu_opcoes = {
            "Diretoria": [pagina_dash],
            "Operacional": [pagina_estoque, pagina_mov, pagina_os, pagina_orc, pagina_frotas], # FROTAS AQUI
            "Administração": [pagina_usuarios],
            "Configurações": [pagina_perfil]
        }
    else:
        menu_opcoes = {
            "Operacional": [pagina_mov, pagina_os, pagina_frotas], # FROTAS AQUI TAMBÉM
            "Configurações": [pagina_perfil]
        }

    pg = st.navigation(menu_opcoes)
    pg.run()