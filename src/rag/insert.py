import os
from src.db.conection import get_vector_conn
from src.rag.generate import gerar_embedding



# ============================
# LEITURA DO TXT
# ============================

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TEXTO_PATH = os.path.join(BASE_PATH, "Texto.txt")

with open(TEXTO_PATH, "r", encoding="utf-8") as file:
    texto = file.read()


# ============================
# DIVIDE TEXTO EM BLOCOS
# ============================
def dividir_em_blocos(texto: str, tamanho=800):
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


# ============================
# INSERIR NO PGVECTOR
# ============================
def inserir_embeddings(textos: list[str], categoria: str):
    conn = get_vector_conn()
    cursor = conn.cursor()

    sql = """
        INSERT INTO rag_embeddings (content, categoria, embedding)
        VALUES (%s, %s, %s)
    """

    try:
        for i, texto in enumerate(textos, 1):
            print(f"⏳ Processando bloco {i}/{len(textos)}...")
            embedding = gerar_embedding(texto)
            cursor.execute(sql, (texto, categoria, embedding))

        conn.commit()
        print(f"✅ {len(textos)} embeddings inseridos com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao inserir embeddings: {e}")

    finally:
        cursor.close()
        conn.close()


# ============================
# EXECUÇÃO PRINCIPAL
# ============================
if __name__ == "__main__":
    CATEGORIA = input("Categoria: ")  # ← movi para cá

    blocos = dividir_em_blocos(texto, tamanho=800)

    print(f"📄 Total de blocos gerados: {len(blocos)}")

    inserir_embeddings(blocos, CATEGORIA)