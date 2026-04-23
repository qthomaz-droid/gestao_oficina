import psycopg2
import streamlit as st
import bcrypt
from datetime import datetime

def get_connection():
    conn_url = st.secrets["postgres"]["url"]
    return psycopg2.connect(conn_url)

@st.cache_resource
def create_tables():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabelas Base
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
                 
    c.execute('''CREATE TABLE IF NOT EXISTS orçamentos 
                 (id SERIAL PRIMARY KEY, servico TEXT, materiais TEXT, valor REAL)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS comentarios 
                 (id SERIAL PRIMARY KEY, os_id INTEGER, usuario TEXT, data_hora TEXT, mensagem TEXT)''')
                 
    # NOVAS TABELAS: GESTÃO DE FROTAS
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos 
                 (id SERIAL PRIMARY KEY, placa TEXT UNIQUE, modelo TEXT, 
                  km_atual INTEGER, ultima_revisao TEXT, proxima_revisao TEXT, status TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos_frota 
                 (id SERIAL PRIMARY KEY, veiculo_id INTEGER, usuario TEXT, 
                  data_retirada TEXT, data_devolucao TEXT, motivo TEXT, status TEXT)''')
    
    # Migrations seguras (Adicionam colunas novas se não existirem)
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='inventario' AND column_name='estoque_minimo'")
    if not c.fetchone(): c.execute("ALTER TABLE inventario ADD COLUMN estoque_minimo INTEGER DEFAULT 0")

    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='os_detalhada' AND column_name='imagem_base64'")
    if not c.fetchone(): c.execute("ALTER TABLE os_detalhada ADD COLUMN imagem_base64 TEXT")
        
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='os_detalhada' AND column_name='parecer_tecnico'")
    if not c.fetchone(): c.execute("ALTER TABLE os_detalhada ADD COLUMN parecer_tecnico TEXT")
    
    # Usuário Admin Padrão
    senha_padrao = 'admin123'
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(senha_padrao.encode('utf-8'), salt).decode('utf-8')
    
    c.execute("""
        INSERT INTO usuarios (username, senha_hash, nome_completo) 
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ('admin', hash_senha, 'Administrador do Sistema'))
    
    conn.commit()
    conn.close()
    return True

@st.dialog("⚠️ Atenção: Confirmação de Exclusão")
def excluir_registro(tabela, id_registro):
    st.write("Você está prestes a apagar este registro permanentemente.")
    col1, col2 = st.columns(2)
    if col1.button("✔️ Sim, Excluir", type="primary", width="stretch"):
        conn = get_connection()
        c = conn.cursor()
        c.execute(f"DELETE FROM {tabela} WHERE id = %s", (id_registro,))
        
        # Apaga comentários vinculados se for uma O.S.
        if tabela == 'os_detalhada':
            c.execute("DELETE FROM comentarios WHERE os_id = %s", (id_registro,))
            
        conn.commit()
        conn.close()
        st.session_state['msg_sucesso'] = "Registro excluído com sucesso!"
        
        if 'view_os_id' in st.session_state:
            del st.session_state['view_os_id']
            
        st.rerun()
    if col2.button("❌ Cancelar", width="stretch"):
        st.rerun()

def exibir_notificacoes():
    if 'msg_sucesso' in st.session_state:
        st.success(st.session_state['msg_sucesso'])
        st.toast(st.session_state['msg_sucesso'], icon="✅")
        del st.session_state['msg_sucesso']