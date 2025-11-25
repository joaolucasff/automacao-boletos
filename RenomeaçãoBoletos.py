# ===============================================
# Automacao de Renomeacao de Boletos PDF - v10
# Extracao via Numero do Documento + Regex robusto
# Suporta: NOVAX, Capital RS, Credvale, Squid
# 100% a prova de erros!
# ===============================================

import os
import re
import shutil
import json
import time
import pdfplumber
from unidecode import unidecode
from typing import Tuple, Optional

# Importar configuração centralizada
from config import (
    PASTA_ENTRADA,
    PASTA_DESTINO,
    PASTA_NOTAS,
    ARQUIVO_LOG_RENOMEACAO as ARQUIVO_LOG
)

# Importar leitor de XMLs NFe
from xml_nfe_reader import indexar_xmls_por_nota
from difflib import SequenceMatcher
from decimal import Decimal

# Tentar importar Ollama (pode não estar instalado)
try:
    from ollama import Client
    OLLAMA_DISPONIVEL = True
except ImportError:
    OLLAMA_DISPONIVEL = False
    print("[AVISO] Biblioteca 'ollama' nao instalada. Usando apenas Regex.")
    print("        Para instalar: pip install ollama")

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

# ======== EXTRAÇÃO DE NÚMERO DA NOTA ======== #
def normalizar_cnpj(cnpj: str) -> str:
    """Remove pontuação do CNPJ, retorna só dígitos"""
    if not cnpj:
        return ""
    return re.sub(r'\D', '', cnpj)

def valor_to_cents(valor) -> int:
    """Converte valor para centavos para comparação exata"""
    if not valor:
        return 0

    # Se já é int ou float
    if isinstance(valor, (int, float)):
        return int(valor * 100)

    # Se é Decimal
    if isinstance(valor, Decimal):
        return int(valor * 100)

    # Se é string
    s = str(valor).replace("R$", "").replace(" ", "")
    # Tratar formato brasileiro (1.234,56)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return int(float(s) * 100)
    except:
        return 0

def calcular_similaridade(str1: str, str2: str) -> float:
    """Calcula similaridade entre duas strings (0.0 a 1.0)"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()

def extrair_cnpj_do_boleto(texto: str) -> str:
    """
    Extrai CNPJ do pagador do boleto.

    Suporta 4 formatos diferentes de FIDCs:
    - NOVAX: "Pagador: NOME CNPJ/ CPF : XX.XXX.XXX/XXXX-XX" (ficha de compensação)
    - SQUID: "Pagador ... - CNPJ: XX.XXX.XXX/XXXX-XX"
    - CAPITAL RS: "Pagador ... , CNPJ: XX.XXX.XXX/XXXX-XX"
    - CREDVALE: "Pagador ... - EPP - XX.XXX.XXX/XXXX-XX" (sem palavra CNPJ)
    """
    # TENTATIVA 1: Padrão específico NOVAX (mais confiável)
    # "Pagador: NOME CNPJ/ CPF : XX.XXX.XXX/XXXX-XX"
    match_novax = re.search(
        r'Pagador:\s*([A-Z\s]+)\s+CNPJ[\/\s]*CPF\s*[:\s]*(\d{2}\.\d{3}\.\d{3}\/\d{4}\-\d{2})',
        texto,
        re.IGNORECASE
    )

    if match_novax:
        cnpj_limpo = normalizar_cnpj(match_novax.group(2))
        if len(cnpj_limpo) == 14:
            return cnpj_limpo

    # TENTATIVA 2: Extrair seção do Pagador (outros FIDCs)
    # Buscar na segunda metade do documento primeiro (onde está ficha de compensação)
    meio = len(texto) // 2
    segunda_metade = texto[meio:]

    match_secao = re.search(
        r'Pagador[:\s]+(.*?)(?:Instruções|Autenticação|Demonstrativo|Sacador|Código de Baixa|Beneficiário Final|$)',
        segunda_metade,
        re.IGNORECASE | re.DOTALL
    )

    # Se não achar na segunda metade, buscar no documento inteiro
    if not match_secao:
        match_secao = re.search(
            r'Pagador[:\s]+(.*?)(?:Instruções|Autenticação|Demonstrativo|Sacador|Código de Baixa|Beneficiário Final|$)',
            texto,
            re.IGNORECASE | re.DOTALL
        )

    if not match_secao:
        return ""

    secao_pagador = match_secao.group(1)

    # Padrões em ordem de prioridade (mais específico primeiro)
    padroes = [
        # Padrão 1: "- CNPJ:" (SQUID)
        r'[-]\s*CNPJ[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        # Padrão 2: ", CNPJ:" (CAPITAL RS)
        r',\s*CNPJ[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        # Padrão 3: "- EPP -" (CREDVALE - sem palavra CNPJ)
        r'[-]\s*EPP\s*[-]\s*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        # Padrão 4: "CNPJ/ CPF :" (NOVAX - fallback)
        r'CNPJ[\/\s]*(?:CPF)?[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        # Padrão 5: Primeiro CNPJ encontrado na seção (fallback final)
        r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})'
    ]

    for padrao in padroes:
        match = re.search(padrao, secao_pagador, re.IGNORECASE)
        if match:
            cnpj_raw = match.group(1)
            cnpj_limpo = normalizar_cnpj(cnpj_raw)
            if len(cnpj_limpo) == 14:
                return cnpj_limpo

    return ""

def extrair_numero_nota_boleto(texto: str) -> str:
    """
    Extrai número da nota fiscal do próprio boleto PDF

    PRIORIDADE MÁXIMA: Campo "Número do Documento" é a fonte mais confiável!
    Se presente, este é o número CORRETO da nota fiscal.
    """
    # === PADRÃO 1: Número do Documento (MAIS CONFIÁVEL!) ===
    # Este é o campo oficial do boleto bancário
    # Formato: "Número do Documento: 310926" ou "Número do Documento\n310926/004"

    # PADRÃO 1A: Número seguido do valor na PRÓXIMA LINHA (mais comum)
    # Aceita qualquer variação de "Número do Documento" (com ou sem acentos, � no lugar de ú)
    pattern_multiline = r'N[u�úü]mero\s+do\s+Documento.*?\n\s*(\d{6}[/\d]*)'
    match = re.search(pattern_multiline, texto, re.IGNORECASE | re.DOTALL)
    if match:
        numero = match.group(1)
        # Se tiver barra, pegar apenas antes da barra
        if '/' in numero:
            numero = numero.split('/')[0]
        if len(numero) == 6:
            print(f"    [NUMERO-DOC] Número do documento encontrado: {numero}")
            return numero

    # PADRÃO 1B: Número na mesma linha
    patterns_sameline = [
        r'N[u�úü]mero\s+(?:do\s+)?Documento[:\s]*(\d{6})',  # Apenas 6 dígitos
        r'N[u�úü]mero\s+do\s+Documento[:\s]*(\d+)',  # Qualquer quantidade
    ]

    for pattern in patterns_sameline:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            numero = match.group(1)
            # Se tiver mais de 6 dígitos, pegar os primeiros 6 (antes da barra)
            if '/' in numero:
                numero = numero.split('/')[0]
            # Garantir que tem exatamente 6 dígitos
            if len(numero) >= 6:
                numero_6dig = numero[:6]  # Primeiros 6 dígitos
                print(f"    [NUMERO-DOC] Número do documento encontrado: {numero_6dig}")
                return numero_6dig

    # PADRÃO 1C: Campo "n° do documento" ou "n do documento" (variações)
    pattern_ndo_doc = r'n[º°]?\s+do\s+documento[:\s]*(\d{6})'
    match = re.search(pattern_ndo_doc, texto, re.IGNORECASE)
    if match:
        numero = match.group(1)
        print(f"    [NUMERO-DOC] Número do documento encontrado: {numero}")
        return numero

    # === PADRÃO 2: Outros padrões (fallback) ===
    patterns_fallback = [
        r'Nosso\s+N(?:úmero|umero)[:\s]*(?:\d+-)?(\d{6,})',
        r'Seu\s+N(?:úmero|umero)[:\s]*(\d{6,})',
        r'N[ºo°]\.?\s*Doc(?:umento)?[:\s]*(\d{6,})',
        r'Nota\s+Fiscal[:\s]*(\d{6,})',
        r'NF[:\s]*(\d{6,})',
    ]

    for pattern in patterns_fallback:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            numero = match.group(1)
            # Pegar primeiros 6 dígitos
            if len(numero) >= 6:
                return numero[:6]

    return ""

def converter_vencimento_para_data_xml(vencimento_str: str) -> str:
    """
    Converte vencimento DD-MM para formato YYYY-MM-DD do XML
    Assume ano atual (2025 se mês >= mês atual, senão 2026)
    """
    import datetime

    if not vencimento_str or vencimento_str == "SEM_VENCIMENTO":
        return ""

    # Formato: DD-MM
    match = re.match(r'(\d{2})-(\d{2})', vencimento_str)
    if not match:
        return ""

    dia = int(match.group(1))
    mes = int(match.group(2))

    # Determinar ano (assumir 2025 ou 2026)
    hoje = datetime.date.today()
    ano = 2025

    # Se o mês é menor que outubro (mês atual), assumir 2026
    if mes < 10:
        ano = 2026

    return f"{ano}-{mes:02d}-{dia:02d}"

def extrair_numero_nota_xml(cnpj_boleto: str, valor_boleto_cents: int, nome_boleto: str, vencimento_boleto: str, mapa_xmls: dict) -> tuple:
    """
    Extrai número da nota do XML fazendo match com dados do boleto

    PRIORIDADE 1 - Match por Duplicata (parcela):
    - CNPJ + Vencimento da duplicata + Valor da duplicata

    PRIORIDADE 2 - Match por Valor Total (fallback):
    - CNPJ + Valor total da nota
    - Nome similar + Valor total

    Retorna: (numero_nota, duplicata_dict|None)
    - numero_nota: string com número da nota (ex: "310886")
    - duplicata_dict: dict da duplicata que deu match, ou None se match foi por valor total
    """
    if not mapa_xmls:
        return ("", None)

    nome_boleto_norm = nome_boleto.upper().strip()
    vencimento_xml_format = converter_vencimento_para_data_xml(vencimento_boleto)

    # Tentar match com cada XML
    melhores_matches = []

    for numero_nota, dados_xml in mapa_xmls.items():
        if not dados_xml.get('xml_valido'):
            continue

        score = 0
        razoes = []
        tipo_match = ""  # "DUPLICATA" ou "TOTAL"
        duplicata_matched = None  # Guarda a duplicata que deu match

        cnpj_xml = dados_xml.get('cnpj', '')
        nome_xml = dados_xml.get('nome', '').upper().strip()

        # === PRIORIDADE 1: MATCH POR DUPLICATA ===
        duplicatas = dados_xml.get('duplicatas', [])
        match_duplicata = False

        if duplicatas and vencimento_xml_format:
            for dup in duplicatas:
                valor_dup_cents = int(dup['valor'] * 100) if dup['valor'] else 0
                venc_dup = dup['vencimento']

                # Match perfeito: CNPJ + Vencimento + Valor da duplicata
                if cnpj_boleto and cnpj_xml and cnpj_boleto == cnpj_xml:
                    if venc_dup == vencimento_xml_format:
                        if valor_dup_cents == valor_boleto_cents:
                            # Match PERFEITO por duplicata
                            score = 100  # Score máximo!
                            razoes = ["DUPLICATA_PERFEITA", f"Venc_{venc_dup}", f"Valor_R${dup['valor']}"]
                            tipo_match = "DUPLICATA"
                            match_duplicata = True
                            duplicata_matched = dup  # Guardar duplicata
                            break

        # === PRIORIDADE 2: MATCH POR VALOR TOTAL (fallback) ===
        if not match_duplicata:
            # Critério 1: CNPJ exato (+50 pontos)
            if cnpj_boleto and cnpj_xml and cnpj_boleto == cnpj_xml:
                score += 50
                razoes.append("CNPJ_MATCH")

            # Critério 2: Valor TOTAL EXATO (+40 pontos)
            valor_xml = dados_xml.get('valor_total', Decimal(0))
            valor_xml_cents = int(valor_xml * 100) if valor_xml else 0

            if valor_boleto_cents > 0 and valor_xml_cents > 0:
                if valor_xml_cents == valor_boleto_cents:
                    score += 40
                    razoes.append("VALOR_TOTAL")
                    tipo_match = "TOTAL"

            # Critério 3: Nome similar (+30 pontos)
            if nome_xml and nome_boleto_norm:
                similaridade = calcular_similaridade(nome_boleto_norm, nome_xml)
                if similaridade >= 0.85:
                    score += 30
                    razoes.append(f"NOME_MATCH_{similaridade:.0%}")
                elif similaridade >= 0.70:
                    score += 15
                    razoes.append(f"NOME_SIMILAR_{similaridade:.0%}")

        if score > 0:
            melhores_matches.append({
                'numero_nota': numero_nota,
                'score': score,
                'razoes': razoes,
                'tipo_match': tipo_match,
                'duplicata': duplicata_matched,  # None se match por total
                'dados': dados_xml
            })

    # Ordenar por score (maior primeiro)
    melhores_matches.sort(key=lambda x: x['score'], reverse=True)

    # Match por duplicata tem prioridade absoluta (score 100)
    # Match por valor total precisa score >= 70
    if melhores_matches:
        match = melhores_matches[0]

        if match['tipo_match'] == "DUPLICATA":
            # Match por duplicata - sempre aceitar
            print(f"    [XML-MATCH-DUPLICATA] Nota {match['numero_nota']} (score: {match['score']}, {', '.join(match['razoes'])})")
            return (match['numero_nota'], match['duplicata'])
        elif match['score'] >= 70:
            # Match por valor total - precisa score >= 70
            print(f"    [XML-MATCH-TOTAL] Nota {match['numero_nota']} (score: {match['score']}, {', '.join(match['razoes'])})")
            return (match['numero_nota'], None)
        else:
            # Score insuficiente
            print(f"    [XML-BAIXO-SCORE] Melhor match: Nota {match['numero_nota']} (score: {match['score']}, {', '.join(match['razoes'])}) - Insuficiente")

    return ("", None)

def obter_numero_nota(cnpj_boleto: str, valor_boleto: str, nome_boleto: str, vencimento_boleto: str, texto_boleto: str, mapa_xmls: dict) -> tuple:
    """
    Função orquestradora para obter número da nota com fallbacks

    Prioridade (À PROVA DE ERROS!):
    0. NÚMERO DO DOCUMENTO do boleto (fonte mais confiável!) + busca duplicata por vencimento
    1. XML via matching inteligente (CNPJ + vencimento + valor da duplicata)
    2. XML via fallback (CNPJ + valor total)
    3. Retorna "SEM_NOTA" se não encontrar

    Retorna: (numero_formatado, dados_xml|None, origem, duplicata|None)
    - numero_formatado: "NF 123456" ou "NF SEM_NOTA"
    - dados_xml: dict com dados completos do XML se encontrado, None caso contrário
    - origem: "NUMERO_DOC_BOLETO", "XML", "BOLETO" ou "NAO_ENCONTRADO"
    - duplicata: dict da duplicata que deu match (se match foi por duplicata), None caso contrário
    """
    # Converter valor para centavos para comparação
    valor_cents = valor_to_cents(valor_boleto)

    # === PRIORIDADE 0: NÚMERO DO DOCUMENTO DO BOLETO (FONTE MAIS CONFIÁVEL!) ===
    # O campo "Número do Documento" é o mais confiável pois vem direto do sistema emissor
    numero_doc_boleto = extrair_numero_nota_boleto(texto_boleto)

    if numero_doc_boleto and mapa_xmls:
        # Validar que este número existe nos XMLs
        if numero_doc_boleto in mapa_xmls:
            dados_xml = mapa_xmls[numero_doc_boleto]
            print(f"    [NUMERO-DOC-XML] XML encontrado para nota {numero_doc_boleto}")

            # Agora, buscar a duplicata correspondente por VENCIMENTO
            # Isso garante que pegamos o valor correto da parcela!
            vencimento_xml_format = converter_vencimento_para_data_xml(vencimento_boleto)
            duplicata_matched = None

            if vencimento_xml_format and dados_xml.get('duplicatas'):
                for dup in dados_xml['duplicatas']:
                    if dup['vencimento'] == vencimento_xml_format:
                        duplicata_matched = dup
                        print(f"    [DUPLICATA-VENC] Duplicata encontrada: venc={vencimento_boleto}, valor=R$ {dup['valor']}")
                        break

            # Se não encontrou duplicata, pode ser boleto de parcela única
            if not duplicata_matched and dados_xml.get('duplicatas'):
                # Se tem apenas 1 duplicata, usar ela
                if len(dados_xml['duplicatas']) == 1:
                    duplicata_matched = dados_xml['duplicatas'][0]
                    print(f"    [DUPLICATA-UNICA] Nota tem apenas 1 parcela: R$ {duplicata_matched['valor']}")

            return (f"NF {numero_doc_boleto}", dados_xml, "NUMERO_DOC_BOLETO", duplicata_matched)
        else:
            print(f"    [AVISO] Número do documento {numero_doc_boleto} não encontrado nos XMLs!")
            print(f"    [INFO] Tentando matching por outros critérios...")

    # === PRIORIDADE 1: MATCHING VIA XML (duplicatas + total) ===
    if mapa_xmls:
        numero, duplicata = extrair_numero_nota_xml(cnpj_boleto, valor_cents, nome_boleto, vencimento_boleto, mapa_xmls)
        if numero:
            # VALIDAÇÃO CRUZADA: Se tínhamos número do documento, verificar se bate!
            if numero_doc_boleto and numero_doc_boleto != numero:
                print(f"    [ALERTA] DIVERGENCIA DETECTADA!")
                print(f"    [ALERTA]    Numero do Documento: {numero_doc_boleto}")
                print(f"    [ALERTA]    Matching via XML: {numero}")
                print(f"    [DECISAO] Usando Numero do Documento (mais confiavel)")
                # Priorizar número do documento!
                if numero_doc_boleto in mapa_xmls:
                    return (f"NF {numero_doc_boleto}", mapa_xmls[numero_doc_boleto], "NUMERO_DOC_BOLETO", None)

            # Retornar dados do XML
            dados_xml = mapa_xmls.get(numero)
            return (f"NF {numero}", dados_xml, "XML", duplicata)

    # === PRIORIDADE 2: Apenas número do boleto (sem XML) ===
    if numero_doc_boleto:
        print(f"    [BOLETO-SEM-XML] Nota {numero_doc_boleto} extraída do boleto (XML não disponível)")
        return (f"NF {numero_doc_boleto}", None, "BOLETO", None)

    # === Não encontrou ===
    print(f"    [ERRO] Numero da nota nao encontrado!")
    return ("NF SEM_NOTA", None, "NAO_ENCONTRADO", None)

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
def extrair_valor_robusto(texto: str) -> str:
    """
    Extração de valor ULTRA ROBUSTA com múltiplos padrões

    Tenta extrair o valor do boleto em ordem de confiabilidade:
    1. Campo "Valor Documento" ou "(=) Valor Documento"
    2. Linha que contém número do documento + vencimento + valor
    3. Primeiro valor em formato R$ X.XXX,XX encontrado
    4. Valor do código de barras (posições 37-47)
    """
    # PADRÃO 1: (=) Valor Documento ou Valor Documento (mais confiável)
    padroes_valor_doc = [
        r'\(=\)\s*Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
        r'Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
        r'\(=\)\s*Valor\s+do\s+Documento\s+[\d/\s\w]+?\s+([\d\.\,]+)',  # CREDVALE
    ]

    for padrao in padroes_valor_doc:
        match = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
        if match:
            valor_str = match.group(1)
            # Validar formato
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

    # PADRÃO 2: Linha com estrutura "número_doc data valor"
    # Formato: "310926/004 17/02/2026 2.221,20"
    match_linha = re.search(r'\d{6}[/\d]*\s+\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
    if match_linha:
        valor_str = match_linha.group(1)
        if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
            print(f"    [VALOR-LINHA-DOC] Valor encontrado: R$ {valor_str}")
            return f"R$ {valor_str}"

    # PADRÃO 3: Vencimento seguido de valor
    # Formato: "17/02/2026 2.221,20"
    match_venc_valor = re.search(r'\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
    if match_venc_valor:
        valor_str = match_venc_valor.group(1)
        if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
            print(f"    [VALOR-APOS-VENC] Valor encontrado: R$ {valor_str}")
            return f"R$ {valor_str}"

    # PADRÃO 4: Qualquer R$ seguido de valor válido
    match_rs = re.search(r'R\$\s*([\d\.\,]+)', texto)
    if match_rs:
        valor_str = match_rs.group(1)
        if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
            return f"R$ {valor_str}"

    # PADRÃO 5: Código de barras (posições 37-47 contêm valor sem vírgula)
    # Formato: "23790.36706 40000.911947 49000.840501 3 13600000222120"
    #                                                       ^^^^^^^^^^^
    match_barras = re.search(r'\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+(\d{14})', texto)
    if match_barras:
        codigo_completo = match_barras.group(1)
        # Extrair valor (posições 3-13, últimos 10 dígitos do valor)
        valor_cents_str = codigo_completo[3:13]  # Exemplo: "0000222120" = R$ 2.221,20
        try:
            valor_cents = int(valor_cents_str)
            if valor_cents > 0:
                valor_reais = valor_cents / 100
                valor_formatado = f"{valor_reais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                print(f"    [VALOR-CODIGO-BARRAS] Valor extraído do código de barras: R$ {valor_formatado}")
                return f"R$ {valor_formatado}"
        except:
            pass

    return "SEM_VALOR"

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

    # Valor: usar extração robusta
    valor = extrair_valor_robusto(texto)

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
    # Aceita variações: CNPJ, CPF, CNPJ/, CNPJ/ CPF
    mp = re.search(r'Pagador:\s*([A-Z0-9][A-Z0-9\s\.\-&]+?)(?:\s+CNPJ[/\s]|\s+CPF)', compacto, re.IGNORECASE)
    if mp:
        pagador = mp.group(1).strip()

    # Vencimento: busca na área do cabeçalho
    md = re.search(r'Vencimento\s+(\d{2}/\d{2}/\d{4})', compacto, re.IGNORECASE)
    if md:
        vencimento = md.group(1)
        vencimento = vencimento[:5].replace("/", "-")

    # Valor: usar extração robusta
    valor = extrair_valor_robusto(texto)

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

    # Valor: usar extração robusta
    valor = extrair_valor_robusto(texto)

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

    # Valor: usar extração robusta
    valor = extrair_valor_robusto(texto)

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
    print("  AUTOMACAO DE RENOMEACAO DE BOLETOS - v10 (XML-Based)")
    print("=" * 70)

    # Verificar pasta de entrada
    if not os.path.exists(PASTA_ENTRADA):
        print(f"[ERRO] Pasta de entrada nao encontrada: {PASTA_ENTRADA}")
        return

    # Criar pasta de destino se não existir
    os.makedirs(PASTA_DESTINO, exist_ok=True)

    # Carregar XMLs das notas fiscais
    print(f"\n[XML] Carregando XMLs da pasta: {PASTA_NOTAS}")
    mapa_xmls = {}
    if os.path.exists(PASTA_NOTAS):
        mapa_xmls = indexar_xmls_por_nota(PASTA_NOTAS, max_emails=2)
        print(f"[XML] Total de XMLs carregados: {len(mapa_xmls)}")
    else:
        print(f"[AVISO] Pasta de notas nao encontrada: {PASTA_NOTAS}")
        print(f"[AVISO] Numero da nota sera extraido apenas do boleto")

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
    notas_encontradas_xml = 0
    notas_fallback_boleto = 0

    # Processar cada arquivo
    inicio_total = time.time()

    for idx, arquivo in enumerate(arquivos, 1):
        print(f"[{idx}/{total}] Processando: {arquivo}")
        origem = os.path.join(PASTA_ENTRADA, arquivo)

        try:
            # Extrair texto do PDF
            texto = extrair_texto_pdf(origem)

            # Extrair dados básicos (com IA + fallback)
            pagador, venc, valor, metodo = extrair_dados(texto)

            # Contar método usado
            if "IA" in metodo:
                metodos_usados["IA"] += 1
            else:
                metodos_usados["REGEX"] += 1

            # Extrair CNPJ do boleto para match com XML
            cnpj_boleto = extrair_cnpj_do_boleto(texto)
            if cnpj_boleto:
                print(f"  [CNPJ] {cnpj_boleto[:2]}.{cnpj_boleto[2:5]}.{cnpj_boleto[5:8]}/{cnpj_boleto[8:12]}-{cnpj_boleto[12:]}")

            # Obter número da nota (XML prioritário, fallback para boleto)
            numero_nf, dados_xml, origem_nota, duplicata_matched = obter_numero_nota(cnpj_boleto, valor, pagador, venc, texto, mapa_xmls)

            # Se encontrou match com XML, usar dados do XML ao invés do boleto
            if origem_nota == "XML" and dados_xml:
                notas_encontradas_xml += 1

                # Usar nome e valor do XML (mais confiável que o boleto)
                if dados_xml.get('nome'):
                    pagador = dados_xml['nome']
                    print(f"  [XML-NOME] Usando nome do XML: {pagador[:50]}...")

                # Escolher valor correto: duplicata (se match foi por duplicata) ou total (se match foi por total)
                if duplicata_matched:
                    # Match foi por DUPLICATA - usar valor da parcela
                    valor_duplicata = duplicata_matched['valor']
                    valor_xml_formatado = f"R$ {valor_duplicata:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    print(f"  [XML-VALOR-DUPLICATA] Usando valor da parcela: {valor_xml_formatado}")

                    # Verificar se o OCR extraiu valor diferente
                    valor_boleto_cents = valor_to_cents(valor)
                    valor_dup_cents = int(valor_duplicata * 100)

                    if valor_boleto_cents != valor_dup_cents:
                        print(f"  [CORRECAO] OCR extraiu valor errado! Corrigido: {valor} -> {valor_xml_formatado}")

                    valor = valor_xml_formatado

                elif dados_xml.get('valor_total') and dados_xml['valor_total'] > 0:
                    # Match foi por VALOR TOTAL
                    valor_xml_decimal = dados_xml['valor_total']
                    valor_xml_formatado = f"R$ {valor_xml_decimal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                    # Detectar se há diferença com o valor do boleto (juros/multa)
                    valor_boleto_cents = valor_to_cents(valor)
                    valor_xml_cents = int(valor_xml_decimal * 100)

                    if valor_boleto_cents != valor_xml_cents:
                        # Calcular diferença (juros/multa)
                        diferenca_cents = valor_boleto_cents - valor_xml_cents
                        diferenca_reais = diferenca_cents / 100.0

                        if diferenca_reais > 0:
                            print(f"  [ALERTA] Detectado juros/multa de R$ {diferenca_reais:.2f} no boleto!")
                            print(f"  [INFO] Valor NF: {valor_xml_formatado} | Valor Boleto: {valor}")
                        elif diferenca_reais < 0:
                            print(f"  [ALERTA] Valor do boleto MENOR que nota fiscal (R$ {abs(diferenca_reais):.2f})")
                            print(f"  [INFO] Valor NF: {valor_xml_formatado} | Valor Boleto: {valor}")

                    # SEMPRE usar valor original da nota fiscal (sem juros)
                    valor = valor_xml_formatado
                    print(f"  [XML-VALOR-TOTAL] Usando valor total da NF: {valor}")

            elif origem_nota == "BOLETO":
                notas_fallback_boleto += 1

            # Gerar nome do arquivo com número da nota
            novo = f"{safe_filename(pagador)} - {safe_filename(numero_nf)} - {safe_filename(venc)} - {safe_filename(valor)}.pdf"
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
    print(f"\nNumero da Nota:")
    print(f"  - Extraido do XML: {notas_encontradas_xml}")
    print(f"  - Fallback boleto: {notas_fallback_boleto}")
    print(f"\nTempo total:        {tempo_total:.1f}s")
    print(f"Tempo medio/boleto: {tempo_total/total:.1f}s" if total > 0 else "")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    processar_boletos()

    
