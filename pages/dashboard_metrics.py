import streamlit as st
import pandas as pd
from src.db.conection import get_vector_conn
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.pdf.metrics_pdf import create_pdf_report

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Agente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor visualização
st.markdown("""
    <style>
    /* Ajusta os cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Fundo dos cards de métricas */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Ajusta expanders */
    [data-testid="stExpander"] {
        background-color: rgba(102, 126, 234, 0.05);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 8px;
    }
    
    /* Melhora contraste dos gráficos */
    .js-plotly-plot {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES DE CONSULTA ====================

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_general_stats():
    """Retorna estatísticas gerais do sistema"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total de sessões únicas
    cursor.execute("SELECT COUNT(DISTINCT session_id) as total FROM chat_ia")
    stats['total_sessions'] = cursor.fetchone()['total']
    
    # Total de mensagens
    cursor.execute("SELECT COUNT(*) as total FROM chat_ia")
    stats['total_messages'] = cursor.fetchone()['total']
    
    # Total de usuários únicos
    cursor.execute("SELECT COUNT(*) as total FROM users")
    stats['total_users'] = cursor.fetchone()['total']
    
    # Mensagens nas últimas 24h
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM chat_ia 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    stats['messages_24h'] = cursor.fetchone()['total']
    
    # Sessões ativas (últimas 24h)
    cursor.execute("""
        SELECT COUNT(DISTINCT session_id) as total 
        FROM chat_ia 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    stats['active_sessions_24h'] = cursor.fetchone()['total']
    
    # Média de mensagens por sessão
    cursor.execute("""
        SELECT AVG(msg_count) as avg_messages
        FROM (
            SELECT session_id, COUNT(*) as msg_count
            FROM chat_ia
            GROUP BY session_id
        ) as session_counts
    """)
    result = cursor.fetchone()
    stats['avg_messages_per_session'] = float(result['avg_messages']) if result['avg_messages'] else 0
    
    cursor.close()
    conn.close()
    
    return stats

@st.cache_data(ttl=300)
def get_messages_over_time(days=30):
    """Retorna mensagens ao longo do tempo"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            DATE(created_at) as data,
            COUNT(*) as total_mensagens,
            COUNT(DISTINCT session_id) as sessoes_unicas
        FROM chat_ia
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(created_at)
        ORDER BY data
    """ % days)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return pd.DataFrame(results) if results else pd.DataFrame()

@st.cache_data(ttl=300)
def get_hourly_distribution():
    """Retorna distribuição de mensagens por hora do dia"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            EXTRACT(HOUR FROM created_at) as hora,
            COUNT(*) as quantidade
        FROM chat_ia
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY EXTRACT(HOUR FROM created_at)
        ORDER BY hora
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return pd.DataFrame(results) if results else pd.DataFrame()

@st.cache_data(ttl=60)
def get_recent_conversations(limit=20):
    """Retorna conversas recentes"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            c.session_id,
            u.nome,
            c.message,
            c.created_at
        FROM chat_ia c
        LEFT JOIN users u ON c.session_id = u.numero
        ORDER BY c.created_at DESC
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return results



# ==================== INTERFACE PRINCIPAL ====================

st.title("🤖 Dashboard - Agente de IA")
st.markdown("### Métricas e Análise de Performance")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Período de análise
    period_options = {
        "Últimos 7 dias": 7,
        "Últimos 30 dias": 30,
        "Últimos 90 dias": 90
    }
    selected_period = st.selectbox(
        "Período de análise:",
        options=list(period_options.keys()),
        index=1
    )
    days = period_options[selected_period]
    
    st.markdown("---")
    
    # Botão de atualização
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Sobre o Dashboard")
    st.info("""
    Este dashboard monitora em tempo real:
    - Volume de interações
    - Padrões de uso
    - Performance do agente
    """)

# =====================================================================
    
    st.markdown("---")
    st.header("📄 Relatórios")

    if st.button("📥 Gerar Relatório PDF", use_container_width=True):
        with st.spinner("Gerando relatório PDF..."):
            # Coleta os dados atuais
            stats_pdf = get_general_stats()
            df_messages_pdf = get_messages_over_time(days)
            df_hourly_pdf = get_hourly_distribution()
            conversations_pdf = get_recent_conversations(limit=20)

            # Gera o PDF
            pdf_buffer = create_pdf_report(
                stats=stats_pdf,
                df_messages=df_messages_pdf,
                df_hourly=df_hourly_pdf,
                conversations=conversations_pdf,
                period_days=days
            )

            # Guarda no session_state
            st.session_state["pdf_report"] = pdf_buffer
    if "pdf_report" in st.session_state:
        st.download_button(
            label="⬇️ Baixar PDF",
            data=st.session_state["pdf_report"],
            file_name=f"relatorio_agente_ia_{days}dias.pdf",
            mime="application/pdf",
            use_container_width=True
    )



# ==================== MÉTRICAS PRINCIPAIS ====================

try:
    stats = get_general_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💬 Total de Mensagens",
            value=f"{stats['total_messages']:,}",
            delta=f"{stats['messages_24h']} (24h)"
        )
    
    with col2:
        st.metric(
            label="🔄 Total de Conversas",
            value=f"{stats['total_sessions']:,}",
            delta=f"{stats['active_sessions_24h']} (24h)"
        )
    
    with col3:
        st.metric(
            label="👥 Usuários Cadastrados",
            value=f"{stats['total_users']:,}"
        )
    
    with col4:
        st.metric(
            label="📊 Média Msg/Conversa",
            value=f"{stats['avg_messages_per_session']:.1f}"
        )
    
    st.markdown("---")
    
    # ==================== GRÁFICOS ====================
    
    # Linha 1: Gráficos temporais
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Volume de Mensagens ao Longo do Tempo")
        df_messages = get_messages_over_time(days)
        
        if not df_messages.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(
                    x=df_messages['data'],
                    y=df_messages['total_mensagens'],
                    name="Mensagens",
                    line=dict(color='#667eea', width=3),
                    fill='tonexty'
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_messages['data'],
                    y=df_messages['sessoes_unicas'],
                    name="Conversas",
                    line=dict(color='#f093fb', width=2, dash='dash')
                ),
                secondary_y=True
            )
            
            fig.update_xaxes(title_text="Data")
            fig.update_yaxes(title_text="Mensagens", secondary_y=False)
            fig.update_yaxes(title_text="Conversas", secondary_y=True)
            
            fig.update_layout(
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para o período selecionado")
    
    with col_right:
        st.subheader("🕐 Distribuição por Hora do Dia")
        df_hourly = get_hourly_distribution()
        
        if not df_hourly.empty:
            # Formata as horas para melhor visualização
            df_hourly['hora_formatada'] = df_hourly['hora'].astype(int).apply(lambda x: f"{int(x):02d}:00")
            
            # Encontra o horário de pico
            max_hora = df_hourly.loc[df_hourly['quantidade'].idxmax(), 'hora']
            
            # Define cores: destaca o horário de pico
            colors = ['#764ba2' if h == max_hora else '#b19cd9' for h in df_hourly['hora']]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df_hourly['hora_formatada'],
                    y=df_hourly['quantidade'],
                    marker_color=colors,
                    text=df_hourly['quantidade'],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Mensagens: %{y}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                xaxis_title="Horário",
                yaxis_title="Quantidade de Mensagens",
                xaxis=dict(tickangle=-45),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Info do horário de pico
            pico_hora = f"{int(max_hora):02d}:00"
            pico_qtd = df_hourly.loc[df_hourly['quantidade'].idxmax(), 'quantidade']
            st.info(f"🔥 **Horário de Pico:** {pico_hora} com {pico_qtd} mensagens")
        else:
            st.info("Sem dados de distribuição horária")
    
    st.markdown("---")
    
    # ==================== CONVERSAS RECENTES ====================
    
    st.subheader("💬 Conversas Recentes")
    
    col_filter1, col_filter2 = st.columns([3, 1])
    with col_filter1:
        limit = st.slider("Número de mensagens para exibir:", 5, 25, 10)
    with col_filter2:
        filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "human", "ai"])
    
    conversations = get_recent_conversations(limit)
    
    if conversations:
        filtered_convs = conversations
        if filter_type != "Todos":
            filtered_convs = [c for c in conversations if c['message'].get('type') == filter_type]
        
        for conv in filtered_convs:
            msg_data = conv['message']
            tipo_msg = msg_data.get('type', 'unknown')
            conteudo = msg_data.get('content', '')
            
            icon = "👤" if tipo_msg == "human" else "🤖"
            nome = conv.get('nome', 'Usuário Desconhecido')
            timestamp = conv['created_at'].strftime("%d/%m/%Y %H:%M:%S")
            
            # Cor diferente para cada tipo
            border_color = "#667eea" if tipo_msg == "human" else "#764ba2"
            
            with st.expander(f"{icon} {nome} - {timestamp}"):
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding-left: 10px;">
                    <strong>Tipo:</strong> {tipo_msg}<br>
                    <strong>Session ID:</strong> {conv['session_id']}
                </div>
                """, unsafe_allow_html=True)
                
                st.text_area(
                    "Mensagem:",
                    conteudo,
                    height=100,
                    key=f"msg_{conv['session_id']}_{timestamp}",
                    disabled=True
                )
    else:
        st.info("Nenhuma conversa registrada ainda")

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.caption("Dashboard Genérico - Agente de IA | Atualizado em tempo real")