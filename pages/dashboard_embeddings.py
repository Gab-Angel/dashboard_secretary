import streamlit as st
import pandas as pd
from datetime import datetime

# Imports das funções
from src.rag.generate import gerar_embedding
from src.pdf.pdf_extractor import extrair_texto_pdf, obter_info_pdf
from src.rag.crud import (
    listar_embeddings,
    contar_embeddings,
    listar_categorias,
    deletar_embedding_por_id,
    deletar_embeddings_por_categoria,
    obter_estatisticas
)
from src.db.conection import get_vector_conn


# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Gerenciador de Embeddings RAG",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Gerenciador de Embeddings RAG")
st.markdown("---")


# ============================
# FUNÇÕES AUXILIARES
# ============================

def dividir_em_blocos(texto: str, tamanho: int = 800) -> list[str]:
    """Divide texto em blocos menores."""
    palavras = texto.split()
    blocos = []
    atual = []

    for palavra in palavras:
        atual.append(palavra)
        if len(" ".join(atual)) >= tamanho:
            blocos.append(" ".join(atual))
            atual = []

    if atual:
        blocos.append(" ".join(atual))

    return blocos


def inserir_embeddings_no_banco(textos: list[str], categoria: str) -> tuple[bool, str]:
    """Insere embeddings no banco de dados."""
    conn = get_vector_conn()
    cursor = conn.cursor()

    sql = """
        INSERT INTO rag_embeddings (content, categoria, embedding)
        VALUES (%s, %s, %s)
    """

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, texto in enumerate(textos, 1):
            status_text.text(f"⏳ Processando bloco {i}/{len(textos)}...")
            embedding = gerar_embedding(texto)
            cursor.execute(sql, (texto, categoria, embedding))
            progress_bar.progress(i / len(textos))

        conn.commit()
        progress_bar.empty()
        status_text.empty()
        
        return True, f"✅ {len(textos)} embeddings inseridos com sucesso!"

    except Exception as e:
        conn.rollback()
        return False, f"❌ Erro ao inserir embeddings: {e}"

    finally:
        cursor.close()
        conn.close()


# ============================
# ABAS DO STREAMLIT
# ============================

tab1, tab2, tab3 = st.tabs(["➕ Adicionar", "📊 Visualizar", "🗑️ Gerenciar"])


# ============================
# ABA 1: ADICIONAR
# ============================
with tab1:
    st.header("Adicionar Novos Embeddings")
    
    # Seletor de método
    metodo = st.radio(
        "Escolha o método de entrada:",
        ["📄 Upload de PDF", "✍️ Texto Manual"],
        horizontal=True
    )
    
    # Campo de categoria (comum para ambos)
    categoria_input = st.text_input(
        "Categoria *",
        placeholder="Ex: escola, produtos, regulamento...",
        help="Identifique o tipo de conteúdo para facilitar a organização"
    )
    
    st.markdown("---")
    
    # Upload de PDF
    if metodo == "📄 Upload de PDF":
        uploaded_file = st.file_uploader(
            "Faça upload do arquivo PDF",
            type=["pdf"],
            help="Formatos aceitos: PDF"
        )
        
        if uploaded_file:
            st.success(f"✅ Arquivo carregado: **{uploaded_file.name}**")
            
            # Mostra informações do PDF
            with st.expander("ℹ️ Informações do PDF"):
                info = obter_info_pdf(uploaded_file)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Número de Páginas", info.get("num_paginas", 0))
                with col2:
                    if info.get("metadata"):
                        st.write("**Metadados:**")
                        for key, value in info["metadata"].items():
                            st.text(f"{key}: {value}")
            
            # Configurações de processamento
            tamanho_bloco = st.slider(
                "Tamanho do bloco (caracteres)",
                min_value=400,
                max_value=1500,
                value=800,
                step=100,
                help="Quanto maior o bloco, mais contexto por embedding"
            )
            
            # Botão de processar
            if st.button("🚀 Processar PDF e Gerar Embeddings", type="primary"):
                if not categoria_input:
                    st.error("⚠️ Por favor, preencha a categoria!")
                else:
                    try:
                        with st.spinner("Extraindo texto do PDF..."):
                            uploaded_file.seek(0)  # Reset do ponteiro
                            texto = extrair_texto_pdf(uploaded_file)
                        
                        st.info(f"📝 Texto extraído: {len(texto)} caracteres")
                        
                        # Divide em blocos
                        blocos = dividir_em_blocos(texto, tamanho=tamanho_bloco)
                        st.info(f"📦 Total de blocos gerados: {len(blocos)}")
                        
                        # Insere no banco
                        sucesso, mensagem = inserir_embeddings_no_banco(blocos, categoria_input)
                        
                        if sucesso:
                            st.success(mensagem)
                            st.balloons()
                        else:
                            st.error(mensagem)
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao processar PDF: {e}")
    
    # Texto Manual
    else:
        texto_manual = st.text_area(
            "Digite ou cole o texto",
            height=300,
            placeholder="Cole aqui o conteúdo que deseja adicionar aos embeddings...",
            help="O texto será dividido em blocos automaticamente"
        )
        
        # Configurações de processamento
        tamanho_bloco = st.slider(
            "Tamanho do bloco (caracteres)",
            min_value=400,
            max_value=1500,
            value=800,
            step=100,
            help="Quanto maior o bloco, mais contexto por embedding"
        )
        
        # Botão de processar
        if st.button("🚀 Gerar Embeddings do Texto", type="primary"):
            if not categoria_input:
                st.error("⚠️ Por favor, preencha a categoria!")
            elif not texto_manual.strip():
                st.error("⚠️ Por favor, digite algum texto!")
            else:
                try:
                    st.info(f"📝 Texto digitado: {len(texto_manual)} caracteres")
                    
                    # Divide em blocos
                    blocos = dividir_em_blocos(texto_manual, tamanho=tamanho_bloco)
                    st.info(f"📦 Total de blocos gerados: {len(blocos)}")
                    
                    # Insere no banco
                    sucesso, mensagem = inserir_embeddings_no_banco(blocos, categoria_input)
                    
                    if sucesso:
                        st.success(mensagem)
                        st.balloons()
                    else:
                        st.error(mensagem)
                
                except Exception as e:
                    st.error(f"❌ Erro ao processar texto: {e}")


# ============================
# ABA 2: VISUALIZAR
# ============================
with tab2:
    st.header("Visualização de Embeddings")
    
    # Estatísticas gerais
    st.subheader("📈 Estatísticas Gerais")
    
    stats = obter_estatisticas()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Embeddings", stats["total"])
    
    with col2:
        st.metric("Total de Categorias", stats["total_categorias"])
    
    with col3:
        if stats["primeiro_registro"]:
            st.metric("Primeiro Registro", stats["primeiro_registro"].strftime("%d/%m/%Y"))
        else:
            st.metric("Primeiro Registro", "N/A")
    
    with col4:
        if stats["ultimo_registro"]:
            st.metric("Último Registro", stats["ultimo_registro"].strftime("%d/%m/%Y"))
        else:
            st.metric("Último Registro", "N/A")
    
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtrar Embeddings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        categorias_disponiveis = listar_categorias()
        categoria_filtro = st.selectbox(
            "Filtrar por Categoria",
            options=["Todas"] + categorias_disponiveis,
            index=0
        )
    
    with col2:
        limite_registros = st.number_input(
            "Limite de Registros",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )
    
    # Botão de atualizar
    if st.button("🔄 Atualizar Listagem"):
        st.rerun()
    
    st.markdown("---")
    
    # Listagem de embeddings
    st.subheader("📋 Embeddings Cadastrados")
    
    categoria_selecionada = None if categoria_filtro == "Todas" else categoria_filtro
    embeddings = listar_embeddings(categoria=categoria_selecionada, limite=limite_registros)
    
    if embeddings:
        # Converte para DataFrame
        df = pd.DataFrame(embeddings)
        
        # Formata a coluna de data
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
        
        # Trunca o conteúdo para exibição
        df["preview"] = df["content"].str[:100] + "..."
        
        # Reordena colunas
        df_display = df[["id", "categoria", "preview", "created_at"]]
        df_display.columns = ["ID", "Categoria", "Prévia do Conteúdo", "Data de Criação"]
        
        # Exibe tabela
        st.dataframe(
            df_display,
            width='stretch',
            hide_index=True
        )
        
        # Detalhes expandíveis
        with st.expander("🔍 Ver Conteúdo Completo de um Embedding"):
            id_selecionado = st.selectbox(
                "Selecione o ID do embedding:",
                options=df["id"].tolist()
            )
            
            embedding_selecionado = next((e for e in embeddings if e["id"] == id_selecionado), None)
            
            if embedding_selecionado:
                st.markdown(f"**Categoria:** {embedding_selecionado['categoria']}")
                st.markdown(f"**Data:** {embedding_selecionado['created_at']}")
                st.markdown("**Conteúdo Completo:**")
                st.text_area("Conteúdo", embedding_selecionado["content"], height=300, disabled=True, label_visibility="collapsed")
    
    else:
        st.info("ℹ️ Nenhum embedding encontrado com os filtros selecionados.")


# ============================
# ABA 3: GERENCIAR
# ============================
with tab3:
    st.header("Gerenciamento de Embeddings")
    
    st.warning("⚠️ **Atenção:** As operações de exclusão são permanentes e não podem ser desfeitas!")
    
    st.markdown("---")
    
    # Opção de gerenciamento
    opcao_gerenciamento = st.radio(
        "Escolha o tipo de exclusão:",
        ["🗑️ Deletar por ID", "🗂️ Deletar por Categoria"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Deletar por ID
    if opcao_gerenciamento == "🗑️ Deletar por ID":
        st.subheader("Deletar Embedding Específico")
        
        embeddings_list = listar_embeddings(limite=500)
        
        if embeddings_list:
            # Cria opções para o selectbox
            opcoes_embeddings = [
                f"ID: {e['id']} | {e['categoria']} | {e['content'][:50]}..."
                for e in embeddings_list
            ]
            
            embedding_selecionado = st.selectbox(
                "Selecione o embedding para deletar:",
                options=opcoes_embeddings,
                index=0
            )
            
            # Extrai o ID (pode ser UUID ou INT)
            id_para_deletar = embedding_selecionado.split(" | ")[0].replace("ID: ", "").strip()
            
            # Preview do que será deletado
            embedding_preview = next((e for e in embeddings_list if e["id"] == id_para_deletar), None)
            
            if embedding_preview:
                with st.expander("👁️ Preview do Embedding"):
                    st.markdown(f"**ID:** {embedding_preview['id']}")
                    st.markdown(f"**Categoria:** {embedding_preview['categoria']}")
                    st.markdown(f"**Data:** {embedding_preview['created_at']}")
                    st.text_area("Conteúdo completo:", embedding_preview["content"], height=150, disabled=True, label_visibility="visible")
            
            # Confirmação e botão de deletar
            col1, col2 = st.columns([3, 1])
            
            with col1:
                confirmar = st.checkbox("✅ Confirmo que quero deletar este embedding")
            
            with col2:
                if st.button("🗑️ Deletar", type="primary", disabled=not confirmar):
                    if deletar_embedding_por_id(id_para_deletar):
                        st.success(f"✅ Embedding ID {id_para_deletar} deletado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao deletar embedding.")
        
        else:
            st.info("ℹ️ Nenhum embedding disponível para deletar.")
    
    # Deletar por Categoria
    else:
        st.subheader("Deletar Todos os Embeddings de uma Categoria")
        
        categorias_disponiveis = listar_categorias()
        
        if categorias_disponiveis:
            categoria_deletar = st.selectbox(
                "Selecione a categoria para deletar:",
                options=categorias_disponiveis
            )
            
            # Mostra quantidade de embeddings na categoria
            total_categoria = contar_embeddings(categoria=categoria_deletar)
            st.warning(f"⚠️ Serão deletados **{total_categoria} embeddings** da categoria **{categoria_deletar}**")
            
            # Confirmação e botão de deletar
            col1, col2 = st.columns([3, 1])
            
            with col1:
                confirmar_categoria = st.checkbox(f"✅ Confirmo que quero deletar TODOS os embeddings da categoria '{categoria_deletar}'")
            
            with col2:
                if st.button("🗑️ Deletar Categoria", type="primary", disabled=not confirmar_categoria):
                    num_deletados = deletar_embeddings_por_categoria(categoria_deletar)
                    if num_deletados > 0:
                        st.success(f"✅ {num_deletados} embeddings da categoria '{categoria_deletar}' foram deletados!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao deletar embeddings.")
        
        else:
            st.info("ℹ️ Nenhuma categoria disponível para deletar.")


# ============================
# FOOTER
# ============================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        🧠 Gerenciador de Embeddings RAG | Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)