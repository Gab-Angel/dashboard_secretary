from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import plotly.graph_objects as go
import io
from PIL import Image as PILImage

def create_pdf_report(stats, df_messages, df_hourly, conversations, period_days=30):
    """
    Gera um relatório PDF completo com as métricas do agente
    
    Args:
        stats: dicionário com estatísticas gerais
        df_messages: DataFrame com mensagens ao longo do tempo
        df_hourly: DataFrame com distribuição horária
        conversations: lista de conversas recentes
        period_days: período de análise em dias
    
    Returns:
        BytesIO object com o PDF
    """
    
    # Buffer para o PDF
    buffer = io.BytesIO()
    
    # Configuração do documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container para os elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo customizado para o título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
    )
    
    # ==== CABEÇALHO ====
    elements.append(Paragraph("Relatório das Métricas do Agente", title_style))
    
    # Data de geração
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    elements.append(Paragraph(f"Gerado em: {data_geracao}", normal_style))
    elements.append(Paragraph(f"Período de análise: Últimos {period_days} dias", normal_style))
    elements.append(Spacer(1, 20))
    
    # Linha separadora
    elements.append(Spacer(1, 12))
    
    # ==== MÉTRICAS PRINCIPAIS ====
    elements.append(Paragraph("📊 Métricas Principais", subtitle_style))
    
    metrics_data = [
        ['Métrica', 'Valor', 'Variação (24h)'],
        ['Total de Mensagens', f"{stats['total_messages']:,}", f"+{stats['messages_24h']}"],
        ['Total de Conversas', f"{stats['total_sessions']:,}", f"+{stats['active_sessions_24h']}"],
        ['Usuários Cadastrados', f"{stats['total_users']:,}", '-'],
        ['Média Msg/Conversa', f"{stats['avg_messages_per_session']:.1f}", '-'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#764ba2')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 20))
    
    # ==== GRÁFICO: MENSAGENS AO LONGO DO TEMPO ====
    if not df_messages.empty:
        elements.append(Paragraph("📈 Volume de Mensagens ao Longo do Tempo", subtitle_style))
        
        # Cria o gráfico com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_messages['data'],
            y=df_messages['total_mensagens'],
            mode='lines+markers',
            name='Mensagens',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Quantidade",
            height=300,
            width=600,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        # Salva como imagem
        img_bytes = fig.to_image(format="png", width=600, height=300)
        img_buffer = io.BytesIO(img_bytes)
        
        img = Image(img_buffer, width=5*inch, height=2.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 20))
    
    # ==== GRÁFICO: DISTRIBUIÇÃO HORÁRIA ====
    if not df_hourly.empty:
        elements.append(Paragraph("🕐 Distribuição por Hora do Dia", subtitle_style))
        
        # Formata as horas
        df_hourly['hora_formatada'] = df_hourly['hora'].astype(int).apply(lambda x: f"{int(x):02d}:00")
        max_hora = df_hourly.loc[df_hourly['quantidade'].idxmax(), 'hora']
        colors_bars = ['#764ba2' if h == max_hora else '#b19cd9' for h in df_hourly['hora']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=df_hourly['hora_formatada'],
                y=df_hourly['quantidade'],
                marker_color=colors_bars,
                text=df_hourly['quantidade'],
                textposition='outside',
            )
        ])
        
        fig.update_layout(
            xaxis_title="Horário",
            yaxis_title="Mensagens",
            height=300,
            width=600,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
        )
        
        # Salva como imagem
        img_bytes = fig.to_image(format="png", width=600, height=300)
        img_buffer = io.BytesIO(img_bytes)
        
        img = Image(img_buffer, width=5*inch, height=2.5*inch)
        elements.append(img)
        
        # Info do horário de pico
        pico_hora = f"{int(max_hora):02d}:00"
        pico_qtd = df_hourly.loc[df_hourly['quantidade'].idxmax(), 'quantidade']
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"🔥 Horário de Pico: {pico_hora} com {pico_qtd} mensagens", normal_style))
        elements.append(Spacer(1, 20))
    
    # ==== RODAPÉ ====
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Dashboard Genérico - Agente de IA | Relatório gerado automaticamente", footer_style))
    
    # Gera o PDF
    doc.build(elements)
    
    # Retorna o buffer
    buffer.seek(0)
    return buffer