import os
import re
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

beneficiario_keywords = ['beneficiário', 'favorecido', 'recebedor', 'destinatário', 'para', 'a favor de']
comprovante_keywords = ['pix', 'transferência', 'comprovante']

def extrair_texto_de_pdf(pdf_path):
    try:
        imagens = convert_from_path(pdf_path, dpi=300)
        texto_total = ''
        for imagem in imagens:
            texto = pytesseract.image_to_string(imagem, lang='por')
            texto_total += texto + '\n'
        return texto_total
    except Exception as e:
        print(f"Erro ao converter PDF {pdf_path}: {e}")
        return ""

def extrair_texto_de_imagem(img_path):
    try:
        imagem = Image.open(img_path)
        texto = pytesseract.image_to_string(imagem, lang='por')
        return texto
    except Exception as e:
        print(f"Erro ao abrir imagem {img_path}: {e}")
        return ""

def buscar_info(texto):
    beneficiario = "DESCONHECIDO"
    valor = "0,00"
    data_pagamento = None
    tipo_doc = ""

    for palavra in beneficiario_keywords:
        padrao = re.compile(rf'{palavra}[:\-]?\s*([A-Z\s]{{2,}})', re.IGNORECASE)
        resultado = padrao.search(texto)
        if resultado:
            bruto = resultado.group(1).strip()
            # Remove palavras comuns como "NOME", "CPF", etc., e múltiplos espaços
            bruto = re.sub(r'\b(NOME|CPF|CNPJ|AGÊNCIA|CONTA)\b', '', bruto, flags=re.IGNORECASE)
            bruto = re.sub(r'\s+', ' ', bruto)
            beneficiario = bruto.strip().upper()
            break

    valor_match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
    if valor_match:
        valor = valor_match.group(1)

    data_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', texto)
    if data_match:
        try:
            data_pagamento = datetime.strptime(data_match.group(1).replace('-', '/'), "%d/%m/%Y")
        except ValueError:
            pass

    if any(k.lower() in texto.lower() for k in comprovante_keywords):
        tipo_doc = "C"

    return beneficiario, valor, data_pagamento, tipo_doc

def limpar_nome_arquivo(nome):
    return re.sub(r'[<>:"/\\|?*]', '', nome)

def renomear_arquivo(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()
    if extensao == ".pdf":
        texto = extrair_texto_de_pdf(caminho_arquivo)
    elif extensao in [".png", ".jpg", ".jpeg"]:
        texto = extrair_texto_de_imagem(caminho_arquivo)
    else:
        return

    beneficiario, valor, data_pagamento, tipo_doc = buscar_info(texto)

    data_str = data_pagamento.strftime('%d.%m.%Y') if data_pagamento else datetime.now().strftime('%d.%m.%Y')
    valor_str = valor

    nome_base = f"{data_str} - {beneficiario} - {valor_str}"
    if tipo_doc == "C":
        nome_base += "C"

    nome_base = limpar_nome_arquivo(nome_base)
    nova_extensao = os.path.splitext(caminho_arquivo)[1]
    novo_nome = f"{nome_base}{nova_extensao}"

    novo_caminho = os.path.join(os.path.dirname(caminho_arquivo), novo_nome)

    try:
        os.rename(caminho_arquivo, novo_caminho)
        print(f"Arquivo renomeado: {novo_nome}")
    except Exception as e:
        print(f"Erro ao renomear {caminho_arquivo}: {e}")

def processar_pasta(pasta):
    for arquivo in os.listdir(pasta):
        caminho_arquivo = os.path.join(pasta, arquivo)
        if os.path.isfile(caminho_arquivo):
            if arquivo.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                renomear_arquivo(caminho_arquivo)

pasta_alvo = r"C:\Users\Gabriel Almeida\OneDrive\Documentos\Projetos Python\RP\renomeio"
processar_pasta(pasta_alvo)
