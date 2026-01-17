import streamlit as st

# Configuração da página principal
st.set_page_config(
    page_title="Sistema de IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    /* Estilo para os cards de navegação */
    .nav-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 30px;
        border-radius: 15px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-color: rgba(102, 126, 234, 0.6);
    }
    
    .nav-icon {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    
    .nav-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 10px;
    }
    
    .nav-description {
        font-size: 0.9rem;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar com informações
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=Logo", width=150)
    st.title("Sistema de IA")
    st.markdown("---")
    
    st.markdown("### 📍 Navegação")
    st.info("""
    Use o menu abaixo para navegar entre as diferentes funcionalidades do sistema.
    """)
    
    st.markdown("---")
    st.markdown("### ℹ️ Sobre")
    st.markdown("""
    **Versão:** 1.0.0  
    **Desenvolvido por:** Sua Empresa  
    **Contato:** contato@empresa.com
    """)

# Header
st.title("🏠 Bem-vindo ao Sistema de IA")
st.markdown("### Central de Navegação")
st.markdown("Selecione uma das opções abaixo para acessar as funcionalidades do sistema.")
st.markdown("---")

# Cards de navegação
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">📊</div>
        <div class="nav-title">Dashboard de Métricas</div>
        <div class="nav-description">Visualize estatísticas, gráficos e análises de performance do agente de IA</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Acessar Dashboard", key="metrics", use_container_width=True):
        st.switch_page("pages/dashboard_metrics.py")

with col2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">🔤</div>
        <div class="nav-title">Gestão de Embeddings</div>
        <div class="nav-description">Insira, gerencie e visualize embeddings do sistema</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Acessar Embeddings", key="embeddings", use_container_width=True):
        st.switch_page("pages/dashboard_embeddings.py")

with col3:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">⚙️</div>
        <div class="nav-title">Configurações</div>
        <div class="nav-description">Configure parâmetros e preferências do sistema</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Acessar Configurações", key="settings", use_container_width=True):
        st.info("Página em desenvolvimento...")

st.markdown("---")

# Seção de estatísticas rápidas
st.markdown("### 📈 Visão Geral Rápida")

col1, col2, col3, col4 = st.columns(4)

# Aqui você pode adicionar métricas gerais rápidas se desejar
with col1:
    st.metric(label="Status do Sistema", value="🟢 Online")

with col2:
    st.metric(label="Páginas Disponíveis", value="2")

with col3:
    st.metric(label="Última Atualização", value="Hoje")

with col4:
    st.metric(label="Versão", value="1.0.0")

# Footer
st.markdown("---")
st.caption("Sistema de IA - Central de Navegação | © 2024 Sua Empresa")