from pypdf import PdfReader


def extrair_texto_pdf(arquivo_pdf) -> str:
    """
    Extrai todo o texto de um arquivo PDF.
    
    Args:
        arquivo_pdf: Objeto de arquivo PDF (pode ser do streamlit ou caminho)
    
    Returns:
        String com todo o texto extraído do PDF
    """
    try:
        # Cria o leitor de PDF
        reader = PdfReader(arquivo_pdf)
        
        # Extrai texto de todas as páginas
        texto_completo = []
        
        for pagina_num, pagina in enumerate(reader.pages, 1):
            texto = pagina.extract_text()
            if texto.strip():  # Só adiciona se tiver conteúdo
                texto_completo.append(texto)
        
        # Junta todo o texto
        texto_final = "\n\n".join(texto_completo)
        
        if not texto_final.strip():
            raise ValueError("PDF não contém texto extraível")
        
        return texto_final
    
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")


def extrair_texto_pdf_por_paginas(arquivo_pdf) -> list[dict]:
    """
    Extrai texto de um PDF separado por páginas.
    
    Args:
        arquivo_pdf: Objeto de arquivo PDF
    
    Returns:
        Lista de dicionários com {'pagina': int, 'texto': str}
    """
    try:
        reader = PdfReader(arquivo_pdf)
        
        paginas = []
        
        for pagina_num, pagina in enumerate(reader.pages, 1):
            texto = pagina.extract_text()
            if texto.strip():
                paginas.append({
                    "pagina": pagina_num,
                    "texto": texto
                })
        
        if not paginas:
            raise ValueError("PDF não contém texto extraível")
        
        return paginas
    
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")


def obter_info_pdf(arquivo_pdf) -> dict:
    """
    Obtém informações sobre o PDF.
    
    Args:
        arquivo_pdf: Objeto de arquivo PDF
    
    Returns:
        Dicionário com informações do PDF
    """
    try:
        reader = PdfReader(arquivo_pdf)
        
        info = {
            "num_paginas": len(reader.pages),
            "metadata": {}
        }
        
        # Tenta extrair metadados se disponíveis
        if reader.metadata:
            info["metadata"] = {
                "titulo": reader.metadata.get("/Title", "N/A"),
                "autor": reader.metadata.get("/Author", "N/A"),
                "assunto": reader.metadata.get("/Subject", "N/A"),
                "criador": reader.metadata.get("/Creator", "N/A"),
            }
        
        return info
    
    except Exception as e:
        return {
            "num_paginas": 0,
            "metadata": {},
            "erro": str(e)
        }