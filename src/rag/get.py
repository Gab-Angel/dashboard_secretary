from src.rag.generate import gerar_embedding
from src.db.conection import get_vector_conn

def buscar_contexto_similar(
    pergunta: str,
    categoria: str | None = None,
    limite: int = 3,
    similaridade_minima: float = 0.7
) -> list[dict]:
    """
    Busca os textos mais similares à pergunta usando busca vetorial.
    
    Args:
        pergunta: A pergunta do usuário
        categoria: Filtro opcional por categoria
        limite: Número máximo de resultados
        similaridade_minima: Score mínimo de similaridade (0 a 1)
    
    Returns:
        Lista de dicionários com 'content', 'categoria' e 'similaridade'
    """
    
    # Gera embedding da pergunta
    embedding_pergunta = gerar_embedding(pergunta)
    
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        # SQL com busca vetorial por similaridade de cosseno
        if categoria:
            sql = """
                SELECT 
                    content,
                    categoria,
                    1 - (embedding <=> %s::vector) as similaridade
                FROM rag_embeddings
                WHERE categoria = %s
                    AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cursor.execute(sql, (
                embedding_pergunta, 
                categoria,
                embedding_pergunta,
                similaridade_minima,
                embedding_pergunta,
                limite
            ))
        else:
            sql = """
                SELECT 
                    content,
                    categoria,
                    1 - (embedding <=> %s::vector) as similaridade
                FROM rag_embeddings
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cursor.execute(sql, (
                embedding_pergunta,
                embedding_pergunta,
                similaridade_minima,
                embedding_pergunta,
                limite
            ))
        
        resultados = cursor.fetchall()
        
        return [
            {
                "content": row["content"],
                "categoria": row["categoria"],
                "similaridade": float(row["similaridade"])
            }
            for row in resultados
        ]
    
    except Exception as e:
        print(f"❌ Erro na busca semântica: {e}")
        return []
    
    finally:
        cursor.close()
        conn.close()


def formatar_contexto(resultados: list[dict]) -> str:
    """
    Formata os resultados da busca para envio ao LLM.
    """
    if not resultados:
        return "Nenhuma informação encontrada sobre esse assunto."
    
    contexto = "Informações encontradas:\n\n"
    
    for i, resultado in enumerate(resultados, 1):
        contexto += f"--- Informação {i} ---\n"
        contexto += f"{resultado['content']}\n\n"
    
    return contexto.strip()