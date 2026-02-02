import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# Configurações da página
st.set_page_config(
    page_title="Dashboard de Processos Judiciais",
    page_icon="⚖️",
    layout="wide"
)

# --- SISTEMA DE LOGIN SIMPLES ---
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""

    def password_entered():
        """Verifica se a senha inserida é correta."""
        if (
            st.session_state["username"] == "admin"
            and st.session_state["password"] == "pedro2026"
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # remove a senha do estado
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primeira vez, mostra campos de login
        st.markdown("<center><h2>🔐 Acesso Restrito</h2></center>", unsafe_allow_html=True)
        st.text_input("Usuário", on_change=None, key="username")
        st.text_input("Senha", type="password", on_change=None, key="password")
        if st.button("Entrar", on_click=password_entered):
            if not st.session_state.get("password_correct", False):
                st.error("😕 Usuário ou senha incorretos")
        return False
    elif not st.session_state["password_correct"]:
        # Se errou, mostra campos novamente
        st.text_input("Usuário", on_change=None, key="username")
        st.text_input("Senha", type="password", on_change=None, key="password")
        if st.button("Entrar", on_click=password_entered):
            if not st.session_state.get("password_correct", False):
                st.error("😕 Usuário ou senha incorretos")
        return False
    else:
        # Senha correta
        return True

# Estilo CSS customizado (Rich Aesthetics)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    csv_path = 'processos_consolidados.csv'
    json_path = 'servico-busca-cpf.json'
    
    df = None
    all_searched_cpfs = []

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df['data_distribuicao_dt'] = pd.to_datetime(df['data_distribuicao'], format='%d/%m/%Y', errors='coerce')
        df['ano_distribuicao'] = df['ano_distribuicao'].astype(str).str.replace('.0', '', regex=False)
  
        df['valor_causa'] = df['valor_causa'].astype(str).str.replace(',', '.', regex=False)
        df['valor_causa'] = pd.to_numeric(df['valor_causa'], errors='coerce').fillna(0)
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            all_searched_cpfs = json.load(f)
            
    return df, all_searched_cpfs

def main():
    # Verifica login antes de mostrar o app
    if not check_password():
        st.stop()

    st.title("⚖️ Visualizador de Processos Judiciais")
    
    # Botão de Logout na Sidebar
    if st.sidebar.button("Sair / Logout"):
        del st.session_state["password_correct"]
        st.rerun()

    st.markdown("Navegue pelos dados consolidados de consultas processuais.")

    df, all_searched_cpfs = load_data()

    if df is None:
        st.error("Arquivo 'processos_consolidados.csv' não encontrado.")
        return

    # --- SIDEBAR (Filtros) ---
    st.sidebar.header("🔍 Filtros de Busca")
    
    search_cpf = st.sidebar.text_input("Buscar por CPF (Chave):")
    search_passivo = st.sidebar.text_input("Pesquisar no Polo Passivo:", placeholder="Ex: Estado de Goias")
    
    available_tribunals = sorted(df['tribunal'].unique().tolist())
    tribunais_init = ['TJGO'] if 'TJGO' in available_tribunals else []
    tribunais = st.sidebar.multiselect("Tribunal:", options=available_tribunals, default=tribunais_init)
    
    available_years = sorted(df['ano_distribuicao'].unique().tolist(), reverse=True)
    default_years = [y for y in ['2026', '2025', '2024', '2023', '2022', '2021', '2020'] if y in available_years]
    anos = st.sidebar.multiselect("Ano de Distribuição:", options=available_years, default=default_years)
    
    classes = st.sidebar.multiselect("Classe Processual:", options=sorted(df['classe'].dropna().unique().tolist()), default=[])
    
    top_assuntos = df['assunto'].value_counts().head(20).index.tolist()
    assuntos = st.sidebar.multiselect("Principais Assuntos:", options=top_assuntos, default=[])

    # --- APLICAÇÃO DOS FILTROS ---
    filtered_df = df.copy()
    if search_cpf:
        filtered_df = filtered_df[filtered_df['cpf_consulta'].str.contains(search_cpf, case=False, na=False)]
    if search_passivo:
        filtered_df = filtered_df[filtered_df['partes_polo_passivo'].str.contains(search_passivo, case=False, na=False)]
    if tribunais:
        filtered_df = filtered_df[filtered_df['tribunal'].isin(tribunais)]
    if anos:
        filtered_df = filtered_df[filtered_df['ano_distribuicao'].isin(anos)]
    if classes:
        filtered_df = filtered_df[filtered_df['classe'].isin(classes)]
    if assuntos:
        filtered_df = filtered_df[filtered_df['assunto'].isin(assuntos)]

    # --- KPI METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Processos", f"{len(filtered_df):,}")
    with col2:
        st.metric("CPFs Únicos (Filtrados)", f"{filtered_df['cpf_consulta'].nunique():,}")
    with col3:
        valor_total = filtered_df['valor_causa'].sum()
        st.metric("Valor Total das Causas", f"R$ {valor_total:,.2f}")
    with col4:
        st.metric("Tribunais", f"{filtered_df['tribunal'].nunique()}")

    # --- VISUALIZAÇÕES ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Distribuição por Tribunal")
        if not filtered_df.empty:
            fig_trib = px.pie(filtered_df, names='tribunal', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_trib, use_container_width=True)
    with c2:
        st.subheader("📈 Evolução Temporal")
        if not filtered_df.empty:
            evolucao = filtered_df['ano_distribuicao'].value_counts().sort_index().reset_index()
            evolucao.columns = ['Ano', 'Quantidade']
            fig_time = px.line(evolucao, x='Ano', y='Quantidade', markers=True, line_shape='spline', color_discrete_sequence=['#1e3a8a'])
            st.plotly_chart(fig_time, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("📋 Detalhes dos Dados")
    cols_to_show = ['cpf_consulta', 'numero_processo', 'assunto', 'classe', 'tribunal', 'data_distribuicao', 'valor_causa', 'partes_polo_passivo']
    st.dataframe(filtered_df[cols_to_show].sort_values('valor_causa', ascending=False), use_container_width=True, hide_index=True)

    # --- SEÇÃO DE CPFS SEM PROCESSOS ---
    st.markdown("---")
    st.header("🕵️ Análise de CPFs sem Processos")
    if all_searched_cpfs:
        cpfs_com_processo = set(df['cpf_consulta'].unique())
        cpfs_sem_processo = [cpf for cpf in all_searched_cpfs if cpf not in cpfs_com_processo]
        cpfs_no_tjgo = set(df[df['tribunal'] == 'TJGO']['cpf_consulta'].unique())
        cpfs_sem_tjgo = [cpf for cpf in all_searched_cpfs if cpf not in cpfs_no_tjgo]
        
        t1, t2 = st.tabs(["Nada Encontrado (Geral)", "Nada no TJGO"])
        with t1:
            st.write(f"Dos **{len(all_searched_cpfs)}** pesquisados, **{len(cpfs_sem_processo)}** sem processos.")
            st.dataframe(pd.DataFrame(cpfs_sem_processo, columns=["CPF"]), use_container_width=True, height=300)
        with t2:
            st.write(f"Dos **{len(all_searched_cpfs)}** pesquisados, **{len(cpfs_sem_tjgo)}** sem processos no **TJGO**.")
            st.dataframe(pd.DataFrame(cpfs_sem_tjgo, columns=["CPF"]), use_container_width=True, height=300)

    # Download
    st.markdown("---")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar dados da tabela acima (CSV)", data=csv, file_name='dados_filtrados.csv', mime='text/csv')

if __name__ == "__main__":
    main()
