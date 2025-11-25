# ===============================================
# 🔧 Automação de Renomeação de Boletos PDF - v9
# Extração via IA (Ollama + Mistral) com fallback para Regex
# Suporta: NOVAX, Capital RS, Credvale, Squid
# ===============================================

import os
import re
import shutil
import json
import time
import pdfplumber
from unidecode import unidecode
from typing import Tuple, Optional

# Tentar importar Ollama (pode não estar instalado)
try:
    from ollama import Client
    OLLAMA_DISPONIVEL = True
except ImportError:
    OLLAMA_DISPONIVEL = False
    print("[AVISO] Biblioteca 'ollama' nao instalada. Usando apenas Regex.")
    print("        Para instalar: pip install ollama")

# ======== CONFIG ======== #
PASTA_ENTRADA = r"C:\Users\User-OEM\Desktop\BoletosAutomação\BoletosEntrada"
PASTA_DESTINO = r"C:\Users\User-OEM\Desktop\BoletosAutomação\BoletosRenomeados"
ARQUIVO_LOG   = r"C:\Users\User-OEM\Desktop\BoletosAutomação\Logs\log_erros.txt"

# Configurações de IA
USAR_IA = False  # Desabilitado temporariamente - usando Regex (rapido e funcional)
MODELO_OLLAMA = "mistral"  # Modelo a ser usado
TIMEOUT_IA = 30  # Timeout em segundos para resposta da IA

# ======== UTILS ======== #
def safe_filename(nome: str) -> str:
    nome_limpo = unidecode(str(nome))
    nome_limpo = re.sub(r'[\\/*?:"<>|]', '-', nome_limpo)
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo).strip()
    return nome_limpo

def extrair_texto_pdf(caminho_pdf: str) -> str:
    with pdfplumber.open(caminho_pdf) as pdf:
        texto = ""
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto += t + "\n"
    return texto

def detectar_fidc(texto: str) -> str:
    u = texto.upper()
    if "CAPITAL RS FIDC" in u or "CAPITAL RS" in u:
        return "CAPITAL"
    if "NOVAX" in u:
        return "NOVAX"
    if "CREDVALE" in u:
        return "CREDVALE"
    if "SQUID" in u:
        return "SQUID"
    return "DESCONHECIDO"

# ------- normalizadores ------- #
def normaliza_valor_str(v: str) -> str:
    # remove espaços no meio do número (às vezes o PDF quebra milhares)
    v = re.sub(r'(?<=\d)\s+(?=\d)', '', v)
    # garante prefixo
    if not v.strip().startswith("R$"):
        v = "R$ " + v.strip()
    return v.strip()

def corta_apos_cnpj_ou_virgula(nome: str) -> str:
    """Remove CNPJ/CPF e tudo que vem depois do nome do pagador"""
    # Remove tudo após vírgula, "CNPJ", "CPF", ou "Beneficiario"
    nome = re.split(r',|CNPJ|CPF|Beneficiario', nome, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    # Remove " - " seguido de números (formato CNPJ: XX.XXX.XXX/XXXX-XX ou CPF: XXX.XXX.XXX-XX)
    nome = re.sub(r'\s*-\s*\d{2,3}[\.\s]*\d{3}[\.\s]*\d{3}[/-]?\d{0,4}[-]?\d{0,2}.*$', '', nome)

    return nome.strip()

# ------- validadores ------- #
def validar_dados_extraidos(pagador: str, vencimento: str, valor: str) -> bool:
    """Valida se os dados extraídos estão no formato esperado"""
    # Validar pagador: não pode ser vazio ou "SEM_PAGADOR"
    if not pagador or pagador == "SEM_PAGADOR" or len(pagador) < 3:
        return False

    # Validar vencimento: deve estar no formato DD-MM
    if not re.match(r'\d{2}-\d{2}', vencimento):
        return False

    # Validar valor: deve conter R$ e números
    if not valor or valor == "SEM_VALOR" or "R$" not in valor:
        return False

    return True

def formatar_vencimento(data_str: str) -> str:
    """Converte DD/MM/YYYY ou DD/MM para DD-MM"""
    # Extrai apenas DD/MM
    match = re.search(r'(\d{2})[/-](\d{2})', data_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return "SEM_VENCIMENTO"

def formatar_valor(valor_str: str) -> str:
    """Garante formato R$ X.XXX,XX"""
    # Remove espaços extras
    valor_str = re.sub(r'\s+', ' ', valor_str).strip()

    # Se já tem R$, retorna
    if valor_str.startswith("R$"):
        return valor_str

    # Adiciona R$ se não tiver
    return f"R$ {valor_str}"

# ======== EXTRATOR VIA IA ======== #
def extrair_dados_ia(texto: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extrai dados do boleto usando IA (Ollama + Mistral)
    Retorna: (pagador, vencimento, valor) ou (None, None, None) se falhar
    """
    if not OLLAMA_DISPONIVEL or not USAR_IA:
        return None, None, None

    try:
        # Limitar texto para não sobrecarregar o modelo (primeiros 2000 caracteres geralmente bastam)
        texto_resumido = texto[:2000]

        # Prompt estruturado para extração
        prompt = f"""Você é um especialista em análise de boletos bancários brasileiros.

Analise o texto abaixo e extraia EXATAMENTE as seguintes informações em formato JSON:

1. "razao_social_pagador": Nome completo da razão social do pagador/sacado (a empresa ou pessoa que vai pagar o boleto)
2. "data_vencimento": Data de vencimento no formato DD/MM/YYYY
3. "valor": Valor do documento no formato com vírgula (exemplo: 1.234,56)

IMPORTANTE:
- Procure por "Pagador:", "Sacado:" ou campos similares para encontrar o pagador
- A data de vencimento geralmente está em "Vencimento:" ou próxima ao topo do boleto
- O valor geralmente está em "(=)Valor Documento" ou "Valor:"
- Retorne APENAS o JSON, sem texto adicional
- Se não encontrar algum campo, use null

Texto do boleto:
{texto_resumido}

JSON:"""

        # Conectar ao Ollama
        client = Client(host='http://localhost:11434')

        # Fazer requisição com timeout
        inicio = time.time()
        response = client.generate(
            model=MODELO_OLLAMA,
            prompt=prompt,
            stream=False
        )
        tempo_decorrido = time.time() - inicio

        # Extrair resposta
        resposta_texto = response.get('response', '').strip()

        # Tentar parsear JSON (com limpeza de markdown se necessário)
        resposta_texto = resposta_texto.replace('```json', '').replace('```', '').strip()

        # Parsear JSON
        dados = json.loads(resposta_texto)

        # Extrair e validar campos
        pagador = dados.get('razao_social_pagador', '').strip()
        vencimento_raw = dados.get('data_vencimento', '')
        valor_raw = dados.get('valor', '')

        # Formatar campos
        vencimento = formatar_vencimento(str(vencimento_raw)) if vencimento_raw else None
        valor = formatar_valor(str(valor_raw)) if valor_raw else None

        # Validar resultado
        if pagador and vencimento and valor:
            if validar_dados_extraidos(pagador, vencimento, valor):
                print(f"    [IA-OK] Tempo: {tempo_decorrido:.1f}s")
                return pagador, vencimento, valor

        print(f"    [IA-INVALIDO] Dados extraidos nao passaram na validacao")
        return None, None, None

    except json.JSONDecodeError as e:
        print(f"    [IA-ERRO] Falha ao parsear JSON: {e}")
        return None, None, None
    except Exception as e:
        print(f"    [IA-ERRO] {type(e).__name__}: {str(e)[:100]}")
        return None, None, None

# ======== EXTRATORES REGEX (FALLBACK) ======== #
def extrair_dados_capital(texto: str):
    linhas = texto.splitlines()
    pagador = "SEM_PAGADOR"
    vencimento = "SEM_VENCIMENTO"
    valor = "SEM_VALOR"

    # Pagador: linha seguinte
    for i, linha in enumerate(linhas):
        if "Pagador" in linha:
            if i + 1 < len(linhas):
                pagador = linhas[i + 1].strip()
                pagador = corta_apos_cnpj_ou_virgula(pagador)
            break

    # Vencimento: mesma linha ou próxima
    for i, linha in enumerate(linhas):
        if "Vencimento" in linha:
            m = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if not m and i + 1 < len(linhas):
                m = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[i + 1])
            if m:
                vencimento = m.group(1)
                break

    # Valor: primeiro R$ encontrado
    mval = re.search(r'R\$\s*[\d\.\,]+', texto)
    if mval:
        valor = mval.group(0).strip()

    if vencimento != "SEM_VENCIMENTO":
        vencimento = vencimento[:5].replace("/", "-")

    return pagador, vencimento, valor

def extrair_dados_novax(texto: str):
    # texto compacto facilita pegar "mesma linha"
    compacto = re.sub(r'\s+', ' ', texto).strip()

    pagador = "SEM_PAGADOR"
    vencimento = "SEM_VENCIMENTO"
    valor = "SEM_VALOR"

    # Pagador: busca especificamente "Pagador:" seguido do nome até CNPJ/CPF
    mp = re.search(r'Pagador:\s*([A-Z][A-Z\s\.\-&]+?)(?:\s+CNPJ|\s+CPF)', compacto, re.IGNORECASE)
    if mp:
        pagador = mp.group(1).strip()

    # Vencimento: busca na área do cabeçalho
    md = re.search(r'Vencimento\s+(\d{2}/\d{2}/\d{4})', compacto, re.IGNORECASE)
    if md:
        vencimento = md.group(1)
        vencimento = vencimento[:5].replace("/", "-")

    # Valor Documento: captura o valor após os campos intermediários
    # Padrão: (=)Valor Documento Data N_Doc Tipo Aceite Data_Movto VALOR
    mv = re.search(r'\(=\)\s*Valor\s+Documento\s+\d{2}/\d{2}/\d{4}\s+\d+\s+\w+\s+\w+\s+\d{2}/\d{2}/\d{4}\s+(\d{1,3}(?:\.\d{3})*,\d{2})', compacto, re.IGNORECASE)
    if mv:
        valor = "R$ " + mv.group(1)

    return pagador, vencimento, valor

def extrair_dados_squid(texto: str):
    """Extrator específico para boletos SQUID"""
    linhas = texto.splitlines()
    pagador = "SEM_PAGADOR"
    vencimento = "SEM_VENCIMENTO"
    valor = "SEM_VALOR"

    # Pagador: procura pela linha "Pagador" EXATA e pega a próxima linha
    for i, linha in enumerate(linhas):
        # Procura linha que contenha APENAS "Pagador" (sem outras informações)
        if linha.strip() == "Pagador":
            if i + 1 < len(linhas):
                # Próxima linha tem o nome do pagador
                linha_pagador = linhas[i + 1].strip()
                # Valida que não é o código de barras (não começa com números seguidos)
                if not re.match(r'^\d{5}\.\d{5}\s+\d{5}', linha_pagador):
                    # Remove tudo após "CNPJ:" ou "CPF:" para pegar só o nome
                    pagador = corta_apos_cnpj_ou_virgula(linha_pagador)
                    break

    # Se não encontrou acima, tenta padrão alternativo com regex mais robusto
    if pagador == "SEM_PAGADOR":
        # Busca por "Pagador" em linha isolada, seguido do nome na próxima
        m = re.search(r'Pagador\s*\n\s*([A-ZÀ-Ú][A-ZÀ-Ú\s\.\-&]+?)\s*-\s*(?:CNPJ|CPF)', texto, re.IGNORECASE | re.MULTILINE)
        if m:
            pagador = m.group(1).strip()

    # Vencimento: procura "Vencimento" e a data
    for i, linha in enumerate(linhas):
        if "Vencimento" in linha:
            # Tentar na mesma linha
            m = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if not m and i + 1 < len(linhas):
                # Tentar na próxima linha
                m = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[i + 1])
            if m:
                vencimento = m.group(1)
                vencimento = vencimento[:5].replace("/", "-")
                break

    # Valor: procura por "(=) Valor documento" ou "(=)Valor Documento"
    # Padrão mais robusto para capturar o valor
    m_valor = re.search(r'\(=\)\s*Valor\s+[Dd]ocumento[^\d]+(R\$\s*[\d\.\,]+)', texto)
    if m_valor:
        valor = normaliza_valor_str(m_valor.group(1))
    else:
        # Fallback: procura primeiro R$ com valor válido
        m_valor = re.search(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', texto)
        if m_valor:
            valor = normaliza_valor_str(m_valor.group(0))

    return pagador, vencimento, valor

def extrair_dados_credvale(texto: str):
    """Extrator específico para boletos CREDVALE"""
    linhas = texto.splitlines()
    pagador = "SEM_PAGADOR"
    vencimento = "SEM_VENCIMENTO"
    valor = "SEM_VALOR"

    # Pagador: procura pela linha "Pagador" EXATA e pega a próxima linha
    for i, linha in enumerate(linhas):
        if linha.strip() == "Pagador":
            if i + 1 < len(linhas):
                linha_pagador = linhas[i + 1].strip()
                # Valida que não é o código de barras
                if not re.match(r'^\d{5}\.\d{5}\s+\d{5}', linha_pagador):
                    pagador = corta_apos_cnpj_ou_virgula(linha_pagador)
                    break

    # Padrão alternativo com regex mais robusto
    if pagador == "SEM_PAGADOR":
        m = re.search(r'Pagador\s*\n\s*([A-ZÀ-Ú][A-ZÀ-Ú\s\.\-&]+?)\s*-\s*(?:CNPJ|CPF)', texto, re.IGNORECASE | re.MULTILINE)
        if m:
            pagador = m.group(1).strip()

    # Vencimento: procura "Vencimento"
    for i, linha in enumerate(linhas):
        if "Vencimento" in linha:
            m = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if not m and i + 1 < len(linhas):
                m = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[i + 1])
            if m:
                vencimento = m.group(1)
                vencimento = vencimento[:5].replace("/", "-")
                break

    # Valor: Credvale tem padrão específico onde o valor vem DEPOIS de "Valor Documento"
    # Procura por linha: "CPF / CNPJ Vencimento Valor Documento" seguida de "[num doc] [data] [VALOR]"
    m_valor = re.search(r'CPF\s*/\s*CNPJ\s+Vencimento\s+Valor\s+Documento\s*\n\s*[\w/-]+\s+\d{2}/\d{2}/\d{4}\s+(\d{1,3}(?:\.\d{3})*,\d{2})', texto, re.IGNORECASE | re.MULTILINE)
    if m_valor:
        valor = "R$ " + m_valor.group(1)
    else:
        # Padrão alternativo: procura "(=) Valor do Documento" seguido do valor
        m_valor = re.search(r'\(=\)\s*Valor\s+do\s+Documento\s*\n.*?(\d{1,3}(?:\.\d{3})*,\d{2})', texto, re.IGNORECASE | re.MULTILINE)
        if m_valor:
            valor = "R$ " + m_valor.group(1)
        else:
            # Último fallback: pega valor na mesma linha do vencimento (formato: doc vencimento valor)
            m_valor = re.search(r'\d{2}/\d{2}/\d{4}\s+(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
            if m_valor:
                valor = "R$ " + m_valor.group(1)

    return pagador, vencimento, valor

def extrair_dados_regex(texto: str):
    """Extração via regex (método antigo) - usado como fallback"""
    fidc = detectar_fidc(texto)

    # Escolhe o extrator específico baseado no FIDC detectado
    if fidc == "NOVAX":
        p, v, val = extrair_dados_novax(texto)
    elif fidc == "SQUID":
        p, v, val = extrair_dados_squid(texto)
    elif fidc == "CREDVALE":
        p, v, val = extrair_dados_credvale(texto)
    elif fidc == "CAPITAL":
        p, v, val = extrair_dados_capital(texto)
    else:
        # FIDC desconhecido - tenta Capital como fallback
        p, v, val = extrair_dados_capital(texto)

    return p, v, val, fidc

def extrair_dados(texto: str) -> Tuple[str, str, str, str]:
    """
    Função principal de extração com fallback inteligente:
    1. Tenta IA (Ollama + Mistral) - funciona para todos os tipos de boletos
    2. Se falhar, usa Regex específico por FIDC

    Retorna: (pagador, vencimento, valor, metodo_usado)
    """
    metodo = "DESCONHECIDO"

    # Tentativa 1: Extração via IA (universal)
    if USAR_IA and OLLAMA_DISPONIVEL:
        print("    Tentando extracao via IA...")
        pagador, vencimento, valor = extrair_dados_ia(texto)

        if pagador and vencimento and valor:
            # IA teve sucesso!
            fidc = detectar_fidc(texto)
            return pagador, vencimento, valor, f"IA-{fidc}"

    # Tentativa 2: Fallback para Regex
    print("    Usando fallback Regex...")
    pagador, vencimento, valor, fidc = extrair_dados_regex(texto)

    return pagador, vencimento, valor, f"REGEX-{fidc}"

# ======== LOG ======== #
def registrar_erro(arquivo, mensagem):
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as log:
        log.write(f"Erro no arquivo {arquivo}: {mensagem}\n")

# ======== MAIN ======== #
def processar_boletos():
    """Processa todos os boletos da pasta de entrada"""
    print("=" * 70)
    print("  AUTOMACAO DE RENOMEACAO DE BOLETOS - v9 (IA + Regex)")
    print("=" * 70)

    # Verificar pasta de entrada
    if not os.path.exists(PASTA_ENTRADA):
        print(f"[ERRO] Pasta de entrada nao encontrada: {PASTA_ENTRADA}")
        return

    # Criar pasta de destino se não existir
    os.makedirs(PASTA_DESTINO, exist_ok=True)

    # Listar arquivos PDF
    arquivos = [f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(".pdf")]
    print(f"\n[INFO] Encontrados {len(arquivos)} boletos para processar.")

    # Status de configuração
    if USAR_IA and OLLAMA_DISPONIVEL:
        print(f"[INFO] Modo: IA (Ollama {MODELO_OLLAMA}) + Fallback Regex")
    else:
        print(f"[INFO] Modo: Apenas Regex (IA desabilitada)")

    print("\n" + "-" * 70 + "\n")

    # Estatísticas
    total = len(arquivos)
    sucesso = 0
    erros = 0
    metodos_usados = {"IA": 0, "REGEX": 0}

    # Processar cada arquivo
    inicio_total = time.time()

    for idx, arquivo in enumerate(arquivos, 1):
        print(f"[{idx}/{total}] Processando: {arquivo}")
        origem = os.path.join(PASTA_ENTRADA, arquivo)

        try:
            # Extrair texto do PDF
            texto = extrair_texto_pdf(origem)

            # Extrair dados (com IA + fallback)
            pagador, venc, valor, metodo = extrair_dados(texto)

            # Contar método usado
            if "IA" in metodo:
                metodos_usados["IA"] += 1
            else:
                metodos_usados["REGEX"] += 1

            # Gerar nome do arquivo
            novo = f"{safe_filename(pagador)} - {safe_filename(venc)} - {safe_filename(valor)}.pdf"
            destino = os.path.join(PASTA_DESTINO, novo)

            # Mover arquivo
            shutil.move(origem, destino)

            # Log de sucesso
            print(f"  [OK] [{metodo}] -> {novo}")
            sucesso += 1

        except Exception as e:
            # Log de erro
            registrar_erro(arquivo, str(e))
            print(f"  [ERRO] Falha ao processar: {str(e)[:100]}")
            erros += 1

        print()  # Linha em branco entre arquivos

    # Estatísticas finais
    tempo_total = time.time() - inicio_total

    print("-" * 70)
    print("\n[CONCLUIDO] Processamento finalizado!\n")
    print(f"Total processados:  {total}")
    print(f"Sucessos:           {sucesso} ({sucesso/total*100:.1f}%)" if total > 0 else "Sucessos: 0")
    print(f"Erros:              {erros}")
    print(f"\nMetodos utilizados:")
    print(f"  - IA (Ollama):    {metodos_usados['IA']}")
    print(f"  - Regex:          {metodos_usados['REGEX']}")
    print(f"\nTempo total:        {tempo_total:.1f}s")
    print(f"Tempo medio/boleto: {tempo_total/total:.1f}s" if total > 0 else "")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    processar_boletos()

    
