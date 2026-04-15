import psycopg2
import streamlit as st
import bcrypt
import os

# Função para ligar ao PostgreSQL na nuvem
def get_connection():
    # No Streamlit Cloud, as credenciais ficam em st.secrets
    # Localmente, pode definir uma variável de ambiente ou usar o ficheiro secrets.toml
    conn_url = st.secrets["postgres"]["url"]
    return psycopg2.connect(conn_url)

def create_tables():
    conn = get_connection()
    c = conn.cursor()
    # No PostgreSQL usamos SERIAL em vez de AUTOINCREMENT e tipos de dados ligeiramente diferentes
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (id SERIAL PRIMARY KEY, item TEXT, qtd INTEGER, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimentacao 
                 (id SERIAL PRIMARY KEY, item_id INTEGER, usuario TEXT, 
                  qtd INTEGER, os_id INTEGER, data_saida TEXT, data_retorno TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS os_detalhada 
                 (id SERIAL PRIMARY KEY, tipo TEXT, data TEXT, nome TEXT, 
                  endereco TEXT, fone TEXT, celular TEXT, cnpj TEXT, modelo TEXT, 
                  itens_json TEXT, mao_obra REAL, pecas REAL, total_geral REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id SERIAL PRIMARY KEY, username TEXT UNIQUE, senha_hash TEXT, nome_completo TEXT)''')
    
    # Criar admin padrão
    c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        senha_padrao = 'admin123'
        salt = bcrypt.gensalt()
        hash_senha = bcrypt.hashpw(senha_padrao.encode('utf-8'), salt).decode('utf-8')
        c.execute("INSERT INTO usuarios (username, senha_hash, nome_completo) VALUES (%s,%s,%s)", 
                  ('admin', hash_senha, 'Administrador'))
    
    conn.commit()
    conn.close()

@st.dialog("Atenção: Confirmação de Exclusão")
def excluir_registro(tabela, id_registro):
    st.write("Deseja apagar este registro permanentemente?")
    col1, col2 = st.columns(2)
    if col1.button("Sim, Excluir", type="primary", use_container_width=True):
        conn = get_connection()
        c = conn.cursor()
        # No psycopg2 usamos %s como placeholder
        c.execute(f"DELETE FROM {tabela} WHERE id = %s", (id_registro,))
        conn.commit()
        conn.close()
        st.session_state['msg_sucesso'] = "Registro excluído!"
        st.rerun()
    if col2.button("Cancelar", use_container_width=True):
        st.rerun()

def exibir_notificacoes():
    if 'msg_sucesso' in st.session_state:
        st.success(st.session_state['msg_sucesso'])
        st.toast(st.session_state['msg_sucesso'], icon="✅")
        del st.session_state['msg_sucesso']