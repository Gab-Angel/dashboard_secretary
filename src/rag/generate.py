import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def gerar_embedding(texto: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texto,
        encoding_format="float"
    )
    return response.data[0].embedding