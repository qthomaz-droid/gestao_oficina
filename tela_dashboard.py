import streamlit as st
import pandas as pd
from db import get_connection

def render_dashboard():
    st.header("📊 Dashboard Gerencial")
    st.write("Visão estratégica e indicadores em tempo real da sua oficina.")

    if st.session_state.get('usuario_logado') != 'admin':
        st.error("Acesso Negado. Apenas o administrador pode visualizar os gráficos gerenciais.")
        st.stop()

    conn = get_connection()
    try:
        df_os = pd.read_sql_query("SELECT * FROM os_detalhada", conn)
        df_inv = pd.read_sql_query("SELECT * FROM inventario", conn)
        df_mov = pd.read_sql_query("SELECT * FROM movimentacao", conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return
    finally:
        conn.close()

    if df_os.empty:
        st.info("Não há dados suficientes para gerar os gráficos ainda.")
        return

    # --- MÉTRICAS SUPERIORES ---
    col1, col2, col3, col4 = st.columns(4)
    total_os = len(df_os[df_os['tipo'] == 'Ordem de Serviço'])
    os_abertas = len(df_os[(df_os['tipo'] == 'Ordem de Serviço') & (df_os['status'] == 'Aberta')])
    total_pedidos = len(df_os[df_os['tipo'] == 'Pedido de Material'])
    ferramentas_uso = len(df_mov[df_mov['status'] == 'Em Uso'])

    col1.metric("🔧 O.S. Totais", total_os)
    col2.metric("🟡 O.S. Pendentes", os_abertas)
    col3.metric("📦 Pedidos de Compra", total_pedidos)
    col4.metric("🛠️ Ferramentas em Uso", ferramentas_uso)

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("O.S. por Status")
        status_count = df_os[df_os['tipo'] == 'Ordem de Serviço']['status'].value_counts()
        if not status_count.empty:
            st.bar_chart(status_count, color="#ff4b4b")

    with c2:
        st.subheader("O.S. por Setor")
        setor_count = df_os['endereco'].value_counts().head(5)
        if not setor_count.empty:
            st.bar_chart(setor_count, color="#0068c9")
            
    st.divider()
    
    st.subheader("📈 Top 5 Equipamentos com Mais Chamados")
    equip_count = df_os[df_os['modelo'] != '']['modelo'].value_counts().head(5)
    if not equip_count.empty:
        st.bar_chart(equip_count, horizontal=True)