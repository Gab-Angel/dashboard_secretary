import streamlit as st
import pandas as pd
from src.db.conection import get_vector_conn
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Tokens & Custos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONSTANTES DE PREÇO ====================
# GPT-4.1 - Preço por 1M tokens
PRICE_INPUT_PER_1M = 2.00   # USD
PRICE_OUTPUT_PER_1M = 8.00  # USD

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_usd_to_brl():
    """Obtém cotação USD -> BRL em tempo real"""
    try:
        response = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL", timeout=5)
        data = response.json()
        cotacao = float(data['USDBRL']['bid'])
        return cotacao
    except Exception as e:
        print(f"Erro ao obter cotação: {e}")
        return 5.00  # Fallback caso a API falhe

def calcular_custo(input_tokens: int, output_tokens: int, em_real: bool = True) -> float:
    """Calcula custo em USD ou BRL baseado nos tokens"""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    custo_usd = input_cost + output_cost
    
    if em_real:
        cotacao = get_usd_to_brl()
        return custo_usd * cotacao
    
    return custo_usd

# ==================== FUNÇÕES DE CONSULTA ====================

@st.cache_data(ttl=300)
def get_token_stats(em_real=True):
    """Retorna estatísticas gerais de tokens"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total de tokens
    cursor.execute("""
        SELECT 
            COALESCE(SUM(input_tokens), 0) as total_input,
            COALESCE(SUM(output_tokens), 0) as total_output,
            COALESCE(SUM(total_tokens), 0) as total_tokens
        FROM agent_token_usage
    """)
    result = cursor.fetchone()
    stats['total_input'] = int(result['total_input'])
    stats['total_output'] = int(result['total_output'])
    stats['total_tokens'] = int(result['total_tokens'])
    stats['total_cost'] = calcular_custo(stats['total_input'], stats['total_output'], em_real)
    
    # Tokens nas últimas 24h
    cursor.execute("""
        SELECT 
            COALESCE(SUM(input_tokens), 0) as input_24h,
            COALESCE(SUM(output_tokens), 0) as output_24h,
            COALESCE(SUM(total_tokens), 0) as total_24h
        FROM agent_token_usage
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    result = cursor.fetchone()
    stats['input_24h'] = int(result['input_24h'])
    stats['output_24h'] = int(result['output_24h'])
    stats['total_24h'] = int(result['total_24h'])
    stats['cost_24h'] = calcular_custo(stats['input_24h'], stats['output_24h'], em_real)
    
    cursor.close()
    conn.close()
    
    return stats

@st.cache_data(ttl=300)
def get_tokens_over_time(days=30, em_real=True):
    """Retorna consumo de tokens ao longo do tempo"""
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            DATE(created_at) as data,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(total_tokens) as total_tokens
        FROM agent_token_usage
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(created_at)
        ORDER BY data
    """ % days)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if results:
        df = pd.DataFrame(results)
        # Calcula custo por dia
        df['custo_diario'] = df.apply(
            lambda row: calcular_custo(row['input_tokens'], row['output_tokens'], em_real),
            axis=1
        )
        return df
    
    return pd.DataFrame()

# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Seletor de moeda
    moeda = st.radio(
        "Moeda:",
        options=["💵 Real (BRL)", "💲 Dólar (USD)"],
        index=0
    )
    usar_real = moeda.startswith("💵")
    
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
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💰 Sobre Custos")
    
    if usar_real:
        cotacao = get_usd_to_brl()
        st.info(f"""
        **Modelo:** GPT-4.1
        
        **Cotação USD/BRL:** R$ {cotacao:.2f}
        
        **Preços (por 1M tokens):**
        - Input: R$ {PRICE_INPUT_PER_1M * cotacao:.2f}
        - Output: R$ {PRICE_OUTPUT_PER_1M * cotacao:.2f}
        """)
    else:
        st.info(f"""
        **Modelo:** GPT-4.1
        
        **Preços (por 1M tokens):**
        - Input: ${PRICE_INPUT_PER_1M:.2f}
        - Output: ${PRICE_OUTPUT_PER_1M:.2f}
        """)

# ==================== INTERFACE PRINCIPAL ====================

st.title("💰 Dashboard - Tokens & Custos")
st.markdown("### Monitoramento de Consumo e Gastos")
st.markdown("---")

# ==================== MÉTRICAS PRINCIPAIS ====================

try:
    stats = get_token_stats(em_real=usar_real)
    simbolo = "R$" if usar_real else "$"
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="💰 Custo Total",
            value=f"{simbolo} {stats['total_cost']:.4f}",
            delta=f"{simbolo} {stats['cost_24h']:.4f} (24h)"
        )
    
    with col2:
        st.metric(
            label="🔢 Total de Tokens",
            value=f"{stats['total_tokens']:,}",
            delta=f"{stats['total_24h']:,} (24h)"
        )
    
    with col3:
        st.metric(
            label="📥 Input Tokens",
            value=f"{stats['total_input']:,}",
            delta=f"{stats['input_24h']:,} (24h)"
        )
    
    with col4:
        st.metric(
            label="📤 Output Tokens",
            value=f"{stats['total_output']:,}",
            delta=f"{stats['output_24h']:,} (24h)"
        )
    
    with col5:
        # Proporção Output/Input
        ratio = stats['total_output'] / stats['total_input'] if stats['total_input'] > 0 else 0
        st.metric(
            label="📊 Razão Output/Input",
            value=f"{ratio:.2f}x"
        )
    
    st.markdown("---")
    
    # ==================== GRÁFICOS ====================
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Consumo de Tokens ao Longo do Tempo")
        df_tokens = get_tokens_over_time(days, em_real=usar_real)
        
        if not df_tokens.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Tokens totais
            fig.add_trace(
                go.Scatter(
                    x=df_tokens['data'],
                    y=df_tokens['total_tokens'],
                    name="Total Tokens",
                    line=dict(color='#667eea', width=3),
                    fill='tonexty'
                ),
                secondary_y=False
            )
            
            # Input tokens
            fig.add_trace(
                go.Scatter(
                    x=df_tokens['data'],
                    y=df_tokens['input_tokens'],
                    name="Input",
                    line=dict(color='#48bb78', width=2, dash='dash')
                ),
                secondary_y=False
            )
            
            # Output tokens
            fig.add_trace(
                go.Scatter(
                    x=df_tokens['data'],
                    y=df_tokens['output_tokens'],
                    name="Output",
                    line=dict(color='#f093fb', width=2, dash='dot')
                ),
                secondary_y=False
            )
            
            fig.update_xaxes(title_text="Data")
            fig.update_yaxes(title_text="Tokens", secondary_y=False)
            
            fig.update_layout(
                hovermode='x unified',
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para o período selecionado")
    
    with col_right:
        st.subheader("💵 Custo Diário")
        
        if not df_tokens.empty:
            fig = go.Figure(data=[
                go.Bar(
                    x=df_tokens['data'],
                    y=df_tokens['custo_diario'],
                    marker_color='#764ba2',
                    text=df_tokens['custo_diario'].apply(lambda x: f"{simbolo} {x:.4f}"),
                    textposition='outside',
                    hovertemplate=f'<b>%{{x}}</b><br>Custo: {simbolo} %{{y:.4f}}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title=f"Custo ({simbolo})",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Info de custo médio
            custo_medio = df_tokens['custo_diario'].mean()
            st.info(f"💵 **Custo Médio Diário:** {simbolo} {custo_medio:.4f}")
        else:
            st.info("Sem dados de custo para o período selecionado")
    
    st.markdown("---")
    
    # ==================== DISTRIBUIÇÃO INPUT/OUTPUT ====================
    
    st.subheader("📊 Distribuição Input vs Output")
    
    col_pie1, col_pie2 = st.columns(2)
    
    with col_pie1:
        # Gráfico de pizza - Tokens
        fig_pie_tokens = go.Figure(data=[go.Pie(
            labels=['Input Tokens', 'Output Tokens'],
            values=[stats['total_input'], stats['total_output']],
            marker_colors=['#48bb78', '#f093fb'],
            hole=0.4,
            textinfo='label+percent',
            textfont_size=14
        )])
        
        fig_pie_tokens.update_layout(
            title="Distribuição de Tokens",
            height=350,
            showlegend=True
        )
        
        st.plotly_chart(fig_pie_tokens, use_container_width=True)
    
    with col_pie2:
        # Gráfico de pizza - Custo
        if usar_real:
            cotacao = get_usd_to_brl()
            input_cost = (stats['total_input'] / 1_000_000) * PRICE_INPUT_PER_1M * cotacao
            output_cost = (stats['total_output'] / 1_000_000) * PRICE_OUTPUT_PER_1M * cotacao
        else:
            input_cost = (stats['total_input'] / 1_000_000) * PRICE_INPUT_PER_1M
            output_cost = (stats['total_output'] / 1_000_000) * PRICE_OUTPUT_PER_1M
        
        fig_pie_cost = go.Figure(data=[go.Pie(
            labels=['Custo Input', 'Custo Output'],
            values=[input_cost, output_cost],
            marker_colors=['#48bb78', '#f093fb'],
            hole=0.4,
            textinfo='label+percent',
            textfont_size=14
        )])
        
        fig_pie_cost.update_layout(
            title="Distribuição de Custos",
            height=350,
            showlegend=True
        )
        
        st.plotly_chart(fig_pie_cost, use_container_width=True)

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.caption("Dashboard de Tokens & Custos | Atualizado em tempo real")