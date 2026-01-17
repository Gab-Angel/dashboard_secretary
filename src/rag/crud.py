from src.db.conection import get_vector_conn


def listar_embeddings(categoria: str | None = None, limite: int = 100):
    """
    Lista embeddings do banco de dados.
    
    Args:
        categoria: Filtro opcional por categoria
        limite: Número máximo de resultados
    
    Returns:
        Lista de dicionários com dados dos embeddings
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        if categoria:
            sql = """
                SELECT id, content, categoria, created_at
                FROM rag_embeddings
                WHERE categoria = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(sql, (categoria, limite))
        else:
            sql = """
                SELECT id, content, categoria, created_at
                FROM rag_embeddings
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(sql, (limite,))
        
        resultados = cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "content": row["content"],
                "categoria": row["categoria"],
                "created_at": row["created_at"]
            }
            for row in resultados
        ]
    
    except Exception as e:
        print(f"❌ Erro ao listar embeddings: {e}")
        return []
    
    finally:
        cursor.close()
        conn.close()


def contar_embeddings(categoria: str | None = None):
    """
    Conta total de embeddings no banco.
    
    Args:
        categoria: Filtro opcional por categoria
    
    Returns:
        Número total de embeddings
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        if categoria:
            sql = "SELECT COUNT(*) as total FROM rag_embeddings WHERE categoria = %s"
            cursor.execute(sql, (categoria,))
        else:
            sql = "SELECT COUNT(*) as total FROM rag_embeddings"
            cursor.execute(sql)
        
        resultado = cursor.fetchone()
        return resultado["total"] if resultado else 0
    
    except Exception as e:
        print(f"❌ Erro ao contar embeddings: {e}")
        return 0
    
    finally:
        cursor.close()
        conn.close()


def listar_categorias():
    """
    Lista todas as categorias únicas no banco.
    
    Returns:
        Lista de strings com nomes das categorias
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT DISTINCT categoria 
            FROM rag_embeddings 
            ORDER BY categoria
        """
        cursor.execute(sql)
        
        resultados = cursor.fetchall()
        return [row["categoria"] for row in resultados]
    
    except Exception as e:
        print(f"❌ Erro ao listar categorias: {e}")
        return []
    
    finally:
        cursor.close()
        conn.close()


def deletar_embedding_por_id(embedding_id):
    """
    Deleta um embedding específico por ID.
    
    Args:
        embedding_id: ID do embedding a ser deletado (int ou UUID string)
    
    Returns:
        True se deletado com sucesso, False caso contrário
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        sql = "DELETE FROM rag_embeddings WHERE id = %s"
        cursor.execute(sql, (embedding_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao deletar embedding: {e}")
        return False
    
    finally:
        cursor.close()
        conn.close()


def deletar_embeddings_por_categoria(categoria: str):
    """
    Deleta todos os embeddings de uma categoria.
    
    Args:
        categoria: Nome da categoria a ser deletada
    
    Returns:
        Número de embeddings deletados
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        sql = "DELETE FROM rag_embeddings WHERE categoria = %s"
        cursor.execute(sql, (categoria,))
        conn.commit()
        
        return cursor.rowcount
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao deletar embeddings por categoria: {e}")
        return 0
    
    finally:
        cursor.close()
        conn.close()


def obter_estatisticas():
    """
    Obtém estatísticas gerais dos embeddings.
    
    Returns:
        Dicionário com estatísticas
    """
    conn = get_vector_conn()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT categoria) as total_categorias,
                MIN(created_at) as primeiro_registro,
                MAX(created_at) as ultimo_registro
            FROM rag_embeddings
        """
        cursor.execute(sql)
        
        resultado = cursor.fetchone()
        
        if resultado:
            return {
                "total": resultado["total"],
                "total_categorias": resultado["total_categorias"],
                "primeiro_registro": resultado["primeiro_registro"],
                "ultimo_registro": resultado["ultimo_registro"]
            }
        
        return {
            "total": 0,
            "total_categorias": 0,
            "primeiro_registro": None,
            "ultimo_registro": None
        }
    
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return {
            "total": 0,
            "total_categorias": 0,
            "primeiro_registro": None,
            "ultimo_registro": None
        }
    
    finally:
        cursor.close()
        conn.close()