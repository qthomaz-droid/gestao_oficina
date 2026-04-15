import psycopg2
import streamlit as st
import bcrypt

# Função para ligar ao PostgreSQL na nuvem
def get_connection():
    conn_url = st.secrets["postgres"]["url"]
    return psycopg2.connect(conn_url)

# O cache_resource é a "mágica" que impede execuções simultâneas e duplas!
@st.cache_resource
def create_tables():
    conn = get_connection()
    c = conn.cursor()
    
    # Criando as tabelas
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
    
    # Gerando o hash do admin de forma segura
    senha_padrao = 'admin123'
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(senha_padrao.encode('utf-8'), salt).decode('utf-8')
    
    # O comando ON CONFLICT DO NOTHING resolve as colisões do PostgreSQL perfeitamente
    c.execute("""
        INSERT INTO usuarios (username, senha_hash, nome_completo) 
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ('admin', hash_senha, 'Administrador do Sistema'))
    
    conn.commit()
    conn.close()
    
    # Retornamos True para o Streamlit saber que o cache foi concluído com sucesso
    return True

@st.dialog("⚠️ Atenção: Confirmação de Exclusão")
def excluir_registro(tabela, id_registro):
    st.write("Você está prestes a apagar este registro permanentemente.")
    st.write("Tem certeza que deseja continuar?")
    
    col1, col2 = st.columns(2)
    if col1.button("✔️ Sim, Excluir", type="primary", use_container_width=True):
        conn = get_connection()
        c = conn.cursor()
        c.execute(f"DELETE FROM {tabela} WHERE id = %s", (id_registro,))
        conn.commit()
        conn.close()
        st.session_state['msg_sucesso'] = "Registro excluído com sucesso!"
        st.rerun()
        
    if col2.button("❌ Cancelar", use_container_width=True):
        st.rerun()

def exibir_notificacoes():
    if 'msg_sucesso' in st.session_state:
        st.success(st.session_state['msg_sucesso'])
        st.toast(st.session_state['msg_sucesso'], icon="✅")
        del st.session_state['msg_sucesso']