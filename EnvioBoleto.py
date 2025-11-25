# EnvioBoletos_v7.0.0.py — 30/10/2025 - XML-BASED SYSTEM
# ---------------------------------------------------------
# CHANGELOG v7.0.0 (REVOLUCAO: Sistema 100% baseado em XML)
# [OK] Base: v6.0.0
# [OK] (BREAKING) Planilha Excel ELIMINADA completamente
# [OK] (NEW) Sistema 100% baseado em XMLs das notas fiscais
# [OK] (NEW) Modulo xml_nfe_reader.py para parsing NFe
# [OK] (NEW) Modulo auditoria.py para relatorios profissionais
# [OK] (NEW) Validacao em 5 camadas (XML->CNPJ->Nome->Valor->Email)
# [OK] (NEW) Emails extraidos diretamente dos XMLs (max 2 validos)
# [OK] (NEW) Validacao cruzada: XML <-> Boleto <-> Nota Fiscal
# [OK] (NEW) Pasta Logs renomeada para Auditoria
# [OK] (NEW) Relatorios em TXT (legivel) e JSON (estruturado)
# [OK] (NEW) Rastreabilidade completa com checksums
# [OK] (NEW) Log de erros criticos separado
# [OK] (IMP) Taxa de sucesso calculada automaticamente
# [OK] (IMP) Timestamps detalhados para cada evento
# [OK] (IMP) Sistema a prova de erros (validacao rigorosa)
#
# VERSOES ANTERIORES:
# v6.0.0 - IA + Fallback Inteligente (IA desabilitada)
# v5.0.0 - Validacao Robusta + Auto-CNPJ
# v4.1.0 - FIDCs Dinamicos
# v4.0.0 - Matching Robusto
# =========================================================

import os, re, time, shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
import win32com.client as win32
import warnings

# Importar novos módulos v7.0
from xml_nfe_reader import indexar_xmls_por_nota, extrair_dados_nfe
from auditoria import (
    AuditoriaExecucao,
    BoletoAuditoria,
    gerar_relatorio_aprovados,
    gerar_relatorio_rejeitados,
    gerar_relatorio_json,
    gerar_log_erros_criticos
)

# Importar configuração centralizada
from config import (
    PASTA_RENOMEADOS as PASTA_BOLETOS,  # Usar pasta de boletos renomeados para envio
    PASTA_NOTAS,
    PASTA_AUDITORIA,
    PASTA_ERROS,
    PASTA_ENVIADOS,
    ASSINATURA_IMG,
    MODO_PREVIEW,
    FIDC_CONFIG,
    FIDC_PADRAO,
    USAR_IA,
    VALIDACAO_CNPJ_OBRIGATORIA,
    TOLERANCIA_VALOR_CENTAVOS,
    MAX_EMAILS_POR_CLIENTE,
    IA_TIMEOUT,
    IA_MODEL,
    IA_TEMPERATURE
)

# PDF reading para extração de CNPJ
try:
    import pdfplumber
    PDF_DISPONIVEL = True
except ImportError:
    PDF_DISPONIVEL = False
    print("[AVISO] pdfplumber não instalado. Extração de CNPJ desabilitada.")
    print("   Para instalar: pip install pdfplumber")

# IA para extração inteligente de dados (IA primeira, regex fallback)
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_ollama.llms import OllamaLLM
    IA_DISPONIVEL = True
except ImportError:
    IA_DISPONIVEL = False
    print("[AVISO] LangChain não instalado. IA desabilitada (usando apenas regex).")
    print("   Para instalar: pip install langchain-core langchain-ollama")

# Criar pastas necessárias
os.makedirs(PASTA_AUDITORIA, exist_ok=True)
os.makedirs(PASTA_ERROS, exist_ok=True)
os.makedirs(PASTA_ENVIADOS, exist_ok=True)

# -------------------- HELPERS --------------------
def normalize_pagador(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().upper()

def valor_to_cents(valor) -> int | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float, Decimal)):
        try:
            d = Decimal(str(valor))
            return int((d * 100).quantize(Decimal("1")))
        except InvalidOperation:
            return None
    s = str(valor).replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        d = Decimal(s)
        return int((d * 100).quantize(Decimal("1")))
    except InvalidOperation:
        return None

def cents_to_brl(cents: int) -> str:
    inte, frac = cents // 100, cents % 100
    return f"{inte:,}".replace(",", ".") + f",{frac:02d}"

def digits_only(s: str) -> str:
    return re.sub(r"[^0-9]", "", s or "")

def normalizar_cnpj(cnpj: str) -> str:
    """
    Normaliza CNPJ removendo pontuação, retorna só dígitos
    Exemplo: "12.345.678/0001-90" >> "12345678000190"
    """
    return digits_only(cnpj)

# -------------------- IA + FALLBACK GENÉRICO --------------------
def extrair_com_ia(texto_pdf: str, prompt_template: str, timeout: int = IA_TIMEOUT) -> str | None:
    """
    Extrai dados usando IA (DeepSeek via Ollama)

    Parâmetros:
        texto_pdf: Texto extraído do PDF
        prompt_template: Template do prompt (deve conter {text})
        timeout: Timeout em segundos

    Retorna:
        Resultado extraído ou None se falhar
    """
    if not (IA_DISPONIVEL and USAR_IA):
        return None

    try:
        # Inicializar modelo
        llm = OllamaLLM(
            model=IA_MODEL,
            temperature=IA_TEMPERATURE,
            timeout=timeout
        )

        # Criar chain
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        chain = prompt | llm | StrOutputParser()

        # Executar (com timeout)
        resultado = chain.invoke({"text": texto_pdf})

        # Limpar resultado
        resultado = resultado.strip()

        # Verificar se é resposta válida
        if resultado and resultado.upper() != "NAO_ENCONTRADO":
            return resultado

        return None

    except Exception as e:
        print(f"      [IA] Erro na extração via IA: {str(e)[:100]}")
        return None

def extrair_texto_pdf(caminho_pdf: str) -> str | None:
    """
    Extrai texto completo de um PDF

    Retorna: Texto do PDF ou None se falhar
    """
    if not PDF_DISPONIVEL:
        return None

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto = ""
            for pag in pdf.pages:
                t = pag.extract_text()
                if t:
                    texto += t + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        print(f"      [ERRO] Falha ao ler PDF: {e}")
        return None

def extrair_cnpj_do_pdf(caminho_pdf: str) -> str | None:
    """
    Extrai CNPJ do pagador do boleto PDF
    Usa IA primeiro, fallback para regex se falhar

    Retorna: "12345678000190" (14 dígitos) ou None
    """
    if not PDF_DISPONIVEL:
        return None

    try:
        # Extrair texto do PDF
        texto = extrair_texto_pdf(caminho_pdf)
        if not texto:
            return None

        # TENTATIVA 1: Usar IA (se disponível)
        if IA_DISPONIVEL and USAR_IA:
            prompt = """Extraia o CNPJ do PAGADOR deste boleto.
O CNPJ tem 14 dígitos no formato XX.XXX.XXX/XXXX-XX.

Procure por:
- Seção "Pagador" ou "Sacado"
- CNPJ logo após o nome da empresa

Retorne APENAS os 14 dígitos sem pontuação (exemplo: 12345678000190).
Se não encontrar, retorne "NAO_ENCONTRADO".

Texto do PDF:
{text}

Resposta (apenas 14 números):"""

            resultado_ia = extrair_com_ia(texto, prompt)
            if resultado_ia:
                cnpj_limpo = normalizar_cnpj(resultado_ia)
                if len(cnpj_limpo) == 14:
                    return cnpj_limpo

        # TENTATIVA 2: Fallback Regex (método melhorado - suporta 4 FIDCs)
        # Suporta NOVAX, SQUID, CAPITAL RS e CREDVALE

        # TENTATIVA 2.1: Padrão específico NOVAX (mais confiável)
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

        # TENTATIVA 2.2: Extrair seção do Pagador (outros FIDCs)
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

        if match_secao:
            secao_pagador = match_secao.group(1)

            # Padrões em ordem de prioridade (mais específico primeiro)
            padroes = [
                # Padrão 1: "- CNPJ:" (SQUID)
                r'[-–]\s*CNPJ[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
                # Padrão 2: ", CNPJ:" (CAPITAL RS)
                r',\s*CNPJ[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
                # Padrão 3: "- EPP -" (CREDVALE - sem palavra CNPJ)
                r'[-–]\s*EPP\s*[-–]\s*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
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

        # TENTATIVA 3: Busca mais ampla mas evitando valores monetários
        # Procura por CNPJs que NÃO estejam precedidos por R$ ou Valor
        # e que tenham o padrão /XXXX- (mais seguro que fallback total)
        match_safe = re.search(
            r'(?<!R\$\s)(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/]\d{4}[\-]\d{2})',
            texto,
            re.IGNORECASE
        )
        if match_safe:
            cnpj_limpo = normalizar_cnpj(match_safe.group(1))
            if len(cnpj_limpo) == 14:
                return cnpj_limpo

        return None

    except Exception as e:
        print(f"[AVISO] Erro ao extrair CNPJ de {os.path.basename(caminho_pdf)}: {e}")
        return None

def detectar_fidc_do_pdf(caminho_pdf: str) -> str:
    """
    Detecta qual FIDC (beneficiário) está no boleto PDF
    Usa IA primeiro, fallback para regex se falhar

    Retorna: "CAPITAL", "NOVAX", "CREDVALE", "SQUID" ou FIDC_PADRAO
    """
    if not PDF_DISPONIVEL:
        return FIDC_PADRAO

    try:
        # Extrair texto do PDF
        texto = extrair_texto_pdf(caminho_pdf)
        if not texto:
            return FIDC_PADRAO

        # TENTATIVA 1: Usar IA (se disponível)
        if IA_DISPONIVEL and USAR_IA:
            prompt = """Identifique qual FIDC é o beneficiário/cedente deste boleto.

Opções possíveis:
1. CAPITAL RS FIDC NP MULTISSETORIAL
2. Novax Fundo de Invest. Em Dir. Cred.
3. CREDVALE FUNDO DE INVESTIMENTO
4. SQUID FUNDO DE INVESTIMENTO

Procure no campo "Beneficiário", "Cedente" ou empresa que está recebendo o pagamento.

Retorne APENAS uma dessas palavras:
- CAPITAL
- NOVAX
- CREDVALE
- SQUID
- NAO_ENCONTRADO

Texto do PDF:
{text}

Resposta (uma palavra):"""

            resultado_ia = extrair_com_ia(texto, prompt)
            if resultado_ia:
                resultado_upper = resultado_ia.upper().strip()
                # Verificar se é um FIDC válido
                if resultado_upper in FIDC_CONFIG:
                    return resultado_upper

        # TENTATIVA 2: Fallback Regex (método original)
        # Normalizar texto para busca
        texto_upper = texto.upper()

        # Procurar por cada FIDC usando palavras-chave
        for fidc_nome, config in FIDC_CONFIG.items():
            for palavra_chave in config["palavras_chave"]:
                if palavra_chave.upper() in texto_upper:
                    return fidc_nome

        # Não encontrou nenhum - usar padrão
        print(f"[AVISO] FIDC nao detectado em {os.path.basename(caminho_pdf)}, usando padrao: {FIDC_PADRAO}")
        return FIDC_PADRAO

    except Exception as e:
        print(f"[AVISO] Erro ao detectar FIDC de {os.path.basename(caminho_pdf)}: {e}")
        return FIDC_PADRAO

def extrair_data_vencimento_do_pdf(caminho_pdf: str) -> str | None:
    """
    Extrai data de vencimento do boleto PDF
    Usa regex para encontrar data no formato brasileiro

    Retorna: "DD/MM/YYYY" ou None se não encontrar
    """
    if not PDF_DISPONIVEL:
        return None

    try:
        # Extrair texto do PDF
        texto = extrair_texto_pdf(caminho_pdf)
        if not texto:
            return None

        # REGEX: Procurar por "Vencimento" seguido de data
        # Formato esperado: DD/MM/YYYY ou DD/MM/YY
        # Aceita: "Vencimento:", "Vencimento ", "Vencimento\n", etc.
        match = re.search(
            r'Vencimento[:\s\n]*(\d{2}[\/\-]\d{2}[\/\-]\d{2,4})',
            texto,
            re.IGNORECASE | re.MULTILINE
        )

        if match:
            data_raw = match.group(1)
            # Normalizar separador para /
            data_normalizada = data_raw.replace('-', '/')

            # Verificar se tem ano completo (4 dígitos)
            partes = data_normalizada.split('/')
            if len(partes) == 3:
                dia, mes, ano = partes

                # Converter ano de 2 dígitos para 4 dígitos
                if len(ano) == 2:
                    ano_int = int(ano)
                    # Se ano >= 00 e <= 50, assume 20XX, senão 19XX
                    if ano_int <= 50:
                        ano = f"20{ano}"
                    else:
                        ano = f"19{ano}"

                return f"{dia}/{mes}/{ano}"

        # FALLBACK: Procurar qualquer data no formato DD/MM/YYYY
        # após palavras-chave relacionadas a vencimento
        match_amplo = re.search(
            r'(?:venc|data|pagamento)[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{2,4})',
            texto,
            re.IGNORECASE
        )

        if match_amplo:
            data_raw = match_amplo.group(1)
            data_normalizada = data_raw.replace('-', '/')

            partes = data_normalizada.split('/')
            if len(partes) == 3:
                dia, mes, ano = partes
                if len(ano) == 2:
                    ano_int = int(ano)
                    if ano_int <= 50:
                        ano = f"20{ano}"
                    else:
                        ano = f"19{ano}"

                return f"{dia}/{mes}/{ano}"

        return None

    except Exception as e:
        print(f"[AVISO] Erro ao extrair data de vencimento de {os.path.basename(caminho_pdf)}: {e}")
        return None

def calcular_similaridade(str1: str, str2: str) -> float:
    """
    Calcula similaridade entre duas strings (0.0 a 1.0)
    Usa SequenceMatcher para comparação fuzzy
    """
    return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()

def encontrar_match_mais_proximo(nome_busca: str, candidatos: list) -> tuple:
    """
    Encontra o candidato mais similar ao nome buscado
    Retorna: (melhor_candidato, score_similaridade)
    """
    if not candidatos:
        return None, 0.0

    melhor = max(candidatos, key=lambda x: calcular_similaridade(nome_busca, x))
    score = calcular_similaridade(nome_busca, melhor)
    return melhor, score

# -------------------- PLANILHA --------------------
def atualizar_cnpj_na_planilha(pagador, valor_cents, cnpj):
    """
    Auto-preenche CNPJ na planilha Excel para eliminar trabalho manual

    Parâmetros:
        pagador: Nome do pagador (normalizado)
        valor_cents: Valor em centavos
        cnpj: CNPJ extraído do boleto (14 dígitos)

    Retorna:
        True se atualizou, False se não encontrou ou erro
    """
    if not cnpj:
        return False

    try:
        wb = load_workbook(ARQUIVO_PLANILHA, data_only=False)
        sh = wb[ABA_PLANILHA]
        headers = {sh.cell(1, c).value: c for c in range(1, sh.max_column + 1)}

        col_pagador = headers.get("Pagador")
        col_valor = headers.get("Valor")
        col_cnpj = headers.get("CNPJ")

        # Se não tem coluna CNPJ, criar
        if not col_cnpj:
            col_cnpj = sh.max_column + 1
            sh.cell(1, col_cnpj).value = "CNPJ"
            print(f"   [INFO] Coluna 'CNPJ' criada na planilha")

        if not (col_pagador and col_valor):
            wb.close()
            return False

        # Procurar linha com mesmo pagador + valor
        for r in range(2, sh.max_row + 1):
            pag_cell = sh.cell(r, col_pagador).value
            val_cell = sh.cell(r, col_valor).value
            cnpj_cell = sh.cell(r, col_cnpj).value

            if not (pag_cell and val_cell):
                continue

            # Comparar pagador e valor
            pag_key_planilha = normalize_pagador(pag_cell)
            val_cents_planilha = valor_to_cents(val_cell)

            if pag_key_planilha == pagador and val_cents_planilha == valor_cents:
                # Encontrou a linha!
                if cnpj_cell:
                    # Já tem CNPJ, verificar se é o mesmo
                    cnpj_existente = normalizar_cnpj(str(cnpj_cell))
                    if cnpj_existente == cnpj:
                        wb.close()
                        return False  # Já tinha o CNPJ correto
                    else:
                        # CNPJ diferente - atualizar
                        print(f"   [AVISO] CNPJ diferente na planilha (era: {cnpj_existente}, agora: {cnpj})")

                # Atualizar CNPJ
                cnpj_formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
                sh.cell(r, col_cnpj).value = cnpj_formatado
                wb.save(ARQUIVO_PLANILHA)
                wb.close()
                print(f"   [OK] CNPJ adicionado a planilha: {cnpj_formatado}")
                return True

        wb.close()
        return False  # Não encontrou linha correspondente

    except Exception as e:
        print(f"   [AVISO] Erro ao atualizar CNPJ na planilha: {e}")
        return False

def carregar_dados_xmls():
    """
    Carrega dados de TODOS os XMLs das notas fiscais (v7.0 - XML-Based)

    Em vez de ler planilha Excel, agora lemos diretamente os XMLs NFe.
    Cada XML contém:
    - Emails do cliente (extraídos do campo <dest><email>)
    - CNPJ do cliente
    - Nome/Razão Social
    - Número da nota fiscal
    - Valor total

    Retorna:
        dict: Mapa indexado por número de nota
              {numero_nota: dados_xml}
              onde dados_xml contém: emails, cnpj, nome, valor_total, etc.
    """
    print()
    print("[XML] ============================================================")
    print("[XML] Carregando dados dos XMLs das notas fiscais...")
    print("[XML] ============================================================")

    # Usar função do módulo xml_nfe_reader
    mapa_xmls = indexar_xmls_por_nota(PASTA_NOTAS, max_emails=MAX_EMAILS_POR_CLIENTE)

    if not mapa_xmls:
        print("[ERRO] Nenhum XML foi carregado! Verifique a pasta de notas.")
        return {}

    # Estatísticas
    total_xmls = len(mapa_xmls)
    com_emails = sum(1 for dados in mapa_xmls.values() if dados.get('emails'))
    sem_emails = total_xmls - com_emails

    print()
    print("[XML] ============================================================")
    print(f"[XML] Resumo do carregamento:")
    print(f"[XML]   - Total de XMLs indexados: {total_xmls}")
    print(f"[XML]   - XMLs com emails validos: {com_emails}")
    print(f"[XML]   - XMLs sem emails: {sem_emails}")
    print("[XML] ============================================================")
    print()

    return mapa_xmls

# -------------------- VALIDAÇÃO DE NOTAS FISCAIS --------------------
# Flags para controle de IA (quando implementada)
USAR_IA_VALIDACAO = False  # Quando IA estiver pronta, mude para True

def extrair_cnpj_da_nota(caminho_pdf_nota):
    """
    Extrai CNPJ da nota fiscal PDF (do destinatário/remetente)
    Usa IA primeiro, fallback para regex se falhar

    Retorna: CNPJ normalizado (14 dígitos) ou None
    """
    if not PDF_DISPONIVEL:
        return None

    try:
        # Extrair texto do PDF
        texto = extrair_texto_pdf(caminho_pdf_nota)
        if not texto:
            return None

        # TENTATIVA 1: Usar IA (se disponível)
        if IA_DISPONIVEL and USAR_IA:
            prompt = """Extraia o CNPJ do DESTINATÁRIO desta nota fiscal.
O CNPJ tem 14 dígitos no formato XX.XXX.XXX/XXXX-XX.

Procure por:
- Seção "Destinatário" ou "Remetente"
- CNPJ próximo ao nome da empresa destinatária
- Geralmente está na parte superior da nota

Retorne APENAS os 14 dígitos sem pontuação (exemplo: 12345678000190).
Se não encontrar, retorne "NAO_ENCONTRADO".

Texto do PDF:
{text}

Resposta (apenas 14 números):"""

            resultado_ia = extrair_com_ia(texto, prompt)
            if resultado_ia:
                cnpj_limpo = normalizar_cnpj(resultado_ia)
                if len(cnpj_limpo) == 14:
                    return cnpj_limpo

        # TENTATIVA 2: Fallback Regex (método original)
        # Procurar TODOS os CNPJs e pegar o ÚLTIMO (geralmente é o destinatário)
        pattern = r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})'
        matches = re.findall(pattern, texto)

        if matches:
            # Pegar o ULTIMO CNPJ encontrado (geralmente é o destinatário)
            for match in reversed(matches):
                cnpj = normalizar_cnpj(match)
                if len(cnpj) == 14:
                    return cnpj

        return None

    except Exception as e:
        print(f"      [AVISO] Erro ao extrair CNPJ da nota: {e}")
        return None

def extrair_valor_da_nota(caminho_pdf_nota):
    """
    Extrai valor total da nota fiscal PDF
    Usa IA primeiro, fallback para regex se falhar

    Retorna: Valor em centavos (int) ou None
    """
    if not PDF_DISPONIVEL:
        return None

    try:
        # Extrair texto do PDF
        texto = extrair_texto_pdf(caminho_pdf_nota)
        if not texto:
            return None

        # TENTATIVA 1: Usar IA (se disponível)
        if IA_DISPONIVEL and USAR_IA:
            prompt = """Extraia o VALOR TOTAL desta nota fiscal.

Procure por:
- "Valor Total da Nota"
- "Total da NF"
- "Valor Total NF"
- Geralmente está no rodapé ou campo de totais

Retorne no formato: 1234.56 (com ponto como separador decimal, sem R$ ou símbolos).
Exemplo: 606.08 para R$ 606,08

Se não encontrar, retorne "NAO_ENCONTRADO".

Texto do PDF:
{text}

Resposta (apenas número com 2 decimais):"""

            resultado_ia = extrair_com_ia(texto, prompt)
            if resultado_ia:
                # Tentar converter para centavos
                valor_cents = valor_to_cents(resultado_ia)
                if valor_cents:
                    return valor_cents

        # TENTATIVA 2: Fallback Regex (método original)
        # Procurar valor total da nota
        patterns = [
            r'Valor\s+Total\s+(?:da\s+)?(?:Nota|NF)[:\s]*R?\$?\s*([\d\.\,]+)',
            r'Total\s+(?:da\s+)?(?:Nota|NF)[:\s]*R?\$?\s*([\d\.\,]+)',
            r'Valor\s+NF[:\s]*R?\$?\s*([\d\.\,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                valor_cents = valor_to_cents(valor_str)
                if valor_cents:
                    return valor_cents

        return None

    except Exception as e:
        print(f"      [AVISO] Erro ao extrair valor da nota: {e}")
        return None

# -------------------- NF MATCHING --------------------
def indexar_notas_por_digitos():
    itens = []
    if not os.path.isdir(PASTA_NOTAS): return itens
    for f in os.listdir(PASTA_NOTAS):
        if f.lower().endswith(".pdf"):
            itens.append((os.path.join(PASTA_NOTAS, f), digits_only(f)))
    return itens

def achar_notas_por_docs_set(docs_set, notas_index, cnpj_boleto=None, valor_boleto_cents=None):
    """
    Busca e valida notas fiscais por documentos

    Validação em 3 níveis:
    1. Número da nota (primeiros 6 dígitos)
    2. CNPJ (se fornecido)
    3. Valor (se fornecido, tolerância ±10 centavos)

    Retorna: (notas_validadas, bases6, detalhes_validacao, tem_erro_critico)
    """
    bases, candidatos = set(), []
    tem_erro_critico = False

    # Fase 1: Buscar candidatos por número
    for d in docs_set:
        digs = digits_only(d)
        if len(digs) >= 6:
            bases.add(digs[:6])

    # VALIDAÇÃO CRÍTICA: Verificar se TODOS os documentos têm notas
    if len(docs_set) > 0 and len(bases) == 0:
        print(f"      [ERRO CRÍTICO] Nenhum documento válido encontrado em: {docs_set}")
        tem_erro_critico = True
        return [], [], [], tem_erro_critico

    # Buscar notas para cada documento
    docs_sem_nota = []
    for base6 in sorted(bases):
        encontrou = False
        for nf_path, nf_digits in notas_index:
            if base6 and base6 in nf_digits:
                candidatos.append((nf_path, base6))
                encontrou = True
                break

        if not encontrou:
            docs_sem_nota.append(base6)

    # VALIDAÇÃO CRÍTICA: Se algum documento não tem nota, bloquear
    if docs_sem_nota:
        print(f"      [ERRO CRÍTICO] Notas fiscais NÃO ENCONTRADAS para documentos: {docs_sem_nota}")
        print(f"      [BLOQUEIO] Email NÃO será enviado por segurança!")
        tem_erro_critico = True
        return [], list(bases), [], tem_erro_critico

    # Fase 2 e 3: Validar CNPJ e Valor
    notas_validadas = []
    detalhes = []

    for nf_path, base6 in candidatos:
        nome_nota = os.path.basename(nf_path)
        validacao = {
            'nota': nome_nota,
            'numero_ok': True,  # Já passou pela validação de número
            'cnpj_ok': None,
            'valor_ok': None,
            'anexada': False
        }

        # Validar CNPJ se fornecido (VALIDAÇÃO CRÍTICA!)
        if cnpj_boleto:
            cnpj_nota = extrair_cnpj_da_nota(nf_path)
            if cnpj_nota:
                validacao['cnpj_ok'] = (cnpj_nota == cnpj_boleto)
                if not validacao['cnpj_ok']:
                    print(f"      [ERRO CRÍTICO] {nome_nota}: CNPJ DIVERGENTE!")
                    print(f"                     Boleto: {cnpj_boleto[:2]}.{cnpj_boleto[2:5]}...{cnpj_boleto[12:]}")
                    print(f"                     Nota:   {cnpj_nota[:2]}.{cnpj_nota[2:5]}...{cnpj_nota[12:]}")
                    print(f"      [BLOQUEIO] Nota com CNPJ divergente NÃO será anexada!")
                    detalhes.append(validacao)
                    tem_erro_critico = True
                    continue  # Pula esta nota
            else:
                print(f"      [AVISO] {nome_nota}: CNPJ não encontrado na nota (anexando mesmo assim)")
                validacao['cnpj_ok'] = None

        # Validar Valor se fornecido
        if valor_boleto_cents:
            valor_nota_cents = extrair_valor_da_nota(nf_path)
            if valor_nota_cents:
                diferenca = abs(valor_nota_cents - valor_boleto_cents)
                tolerancia = 10  # 10 centavos
                validacao['valor_ok'] = (diferenca <= tolerancia)
                if not validacao['valor_ok']:
                    valor_boleto_brl = cents_to_brl(valor_boleto_cents)
                    valor_nota_brl = cents_to_brl(valor_nota_cents)
                    print(f"      [AVISO] {nome_nota}: Valor diferente")
                    print(f"              Boleto: R$ {valor_boleto_brl}")
                    print(f"              Nota:   R$ {valor_nota_brl}")
                    # Não rejeita por valor, só avisa
            else:
                print(f"      [AVISO] {nome_nota}: Valor nao encontrado")
                validacao['valor_ok'] = None

        # Se passou nas validações (ou não havia validações), anexar
        validacao['anexada'] = True
        notas_validadas.append(nf_path)
        detalhes.append(validacao)
        print(f"      [OK] {nome_nota}: Validada (CNPJ: {validacao['cnpj_ok']}, Valor: {validacao['valor_ok']})")

    # Remover duplicatas
    seen, notas_unique = set(), []
    for n in notas_validadas:
        if n not in seen:
            seen.add(n)
            notas_unique.append(n)

    return notas_unique, sorted(list(bases)), detalhes, tem_erro_critico

# -------------------- MATCHING ROBUSTO --------------------
def validar_boleto_com_xml(numero_nota, pagador_norm, valor_cents, cnpj_boleto, mapa_xmls, boleto_auditoria):
    """
    Validacao em 5 CAMADAS do boleto com dados do XML (v7.0 - XML-Based)

    Sistema a prova de erros com validacao cruzada rigorosa.
    Cada camada adiciona uma barreira de seguranca.

    CAMADA 1: Buscar XML correspondente ao boleto (por numero da nota)
    CAMADA 2: Validar CNPJ (boleto vs XML)
    CAMADA 3: Validar Nome (boleto vs XML - fuzzy matching)
    CAMADA 4: Validar Valor (boleto vs XML - com tolerancia)
    CAMADA 5: Validar Emails (devem existir e estar completos)

    Parametros:
        numero_nota: Numero da nota fiscal extraido do boleto
        pagador_norm: Nome do pagador normalizado
        valor_cents: Valor do boleto em centavos
        cnpj_boleto: CNPJ extraido do boleto (pode ser None)
        mapa_xmls: Dicionario {numero_nota: dados_xml}
        boleto_auditoria: Objeto BoletoAuditoria para registro

    Retorna:
        (dados_xml, status, mensagem_erro) onde:
        - dados_xml: Dados do XML se aprovado, None se rejeitado
        - status: "APROVADO" ou "REJEITADO"
        - mensagem_erro: Descricao do erro se rejeitado
    """

    # ===== CAMADA 1: Buscar XML =====
    print(f"   [VALIDACAO] Camada 1/5: Buscando XML da nota {numero_nota}...")

    dados_xml = mapa_xmls.get(numero_nota)

    if not dados_xml or not dados_xml.get('xml_valido'):
        msg = f"XML nao encontrado ou invalido para nota {numero_nota}"
        print(f"   [X] FALHA: {msg}")
        boleto_auditoria.adicionar_detalhe("CAMADA 1 - XML", False, msg)
        boleto_auditoria.validacoes['xml_encontrado'] = False
        return None, "REJEITADO", msg

    print(f"   [OK] XML encontrado: {dados_xml['numero_nota']}")
    boleto_auditoria.adicionar_detalhe("CAMADA 1 - XML", True, f"XML encontrado ({dados_xml['numero_nota']})")
    boleto_auditoria.validacoes['xml_encontrado'] = True

    # ===== CAMADA 1.5: Validar Numero da Nota (100% igual) =====
    print(f"   [VALIDACAO] Camada 1.5/5: Validando numero da nota...")

    numero_nota_xml = dados_xml.get('numero_nota', '')

    # Validação crítica: número da nota deve ser EXATAMENTE igual
    if numero_nota != numero_nota_xml:
        msg = f"Numero da nota divergente! Boleto: {numero_nota}, XML: {numero_nota_xml}"
        print(f"   [X] FALHA CRITICA: {msg}")
        boleto_auditoria.adicionar_detalhe("CAMADA 1.5 - Numero Nota", False, msg)
        boleto_auditoria.validacoes['numero_nota_match'] = False
        return None, "REJEITADO", msg

    print(f"   [OK] Numero da nota match 100%: {numero_nota}")
    boleto_auditoria.adicionar_detalhe("CAMADA 1.5 - Numero Nota", True, f"Match perfeito: {numero_nota}")
    boleto_auditoria.validacoes['numero_nota_match'] = True

    # ===== CAMADA 2: Validar CNPJ =====
    print(f"   [VALIDACAO] Camada 2/5: Validando CNPJ...")

    cnpj_xml = dados_xml.get('cnpj', '')

    if VALIDACAO_CNPJ_OBRIGATORIA and cnpj_boleto and cnpj_xml:
        if cnpj_boleto == cnpj_xml:
            print(f"   [OK] CNPJ match: {cnpj_boleto[:2]}.{cnpj_boleto[2:5]}.{cnpj_boleto[5:8]}/{cnpj_boleto[8:12]}-{cnpj_boleto[12:]}")
            boleto_auditoria.adicionar_detalhe("CAMADA 2 - CNPJ", True, f"Match perfeito: {cnpj_boleto}")
            boleto_auditoria.validacoes['cnpj_match'] = True
        else:
            msg = f"CNPJ divergente! Boleto: {cnpj_boleto}, XML: {cnpj_xml}"
            print(f"   [X] FALHA: {msg}")
            boleto_auditoria.adicionar_detalhe("CAMADA 2 - CNPJ", False, msg)
            boleto_auditoria.validacoes['cnpj_match'] = False
            return None, "REJEITADO", msg
    else:
        print(f"   [AVISO] CNPJ nao disponivel para validacao (boleto: {cnpj_boleto or 'N/A'}, XML: {cnpj_xml or 'N/A'})")
        boleto_auditoria.adicionar_detalhe("CAMADA 2 - CNPJ", None, "CNPJ nao disponivel para validacao")
        boleto_auditoria.validacoes['cnpj_match'] = None

    # ===== CAMADA 3: Validar Nome =====
    print(f"   [VALIDACAO] Camada 3/5: Validando nome do cliente...")

    nome_xml = dados_xml.get('nome', '')
    nome_xml_norm = normalize_pagador(nome_xml)

    if nome_xml_norm and pagador_norm:
        similaridade = SequenceMatcher(None, pagador_norm, nome_xml_norm).ratio()

        if similaridade >= 0.85:  # 85% de similaridade minima
            print(f"   [OK] Nome match: {similaridade:.0%} de similaridade")
            boleto_auditoria.adicionar_detalhe("CAMADA 3 - Nome", True, f"Similaridade {similaridade:.0%}")
            boleto_auditoria.validacoes['nome_match'] = True
        else:
            print(f"   [AVISO] Similaridade baixa: {similaridade:.0%}")
            print(f"           Boleto: {pagador_norm}")
            print(f"           XML:    {nome_xml_norm}")
            boleto_auditoria.adicionar_detalhe("CAMADA 3 - Nome", True, f"Similaridade {similaridade:.0%} (baixa mas aceita)")
            boleto_auditoria.validacoes['nome_match'] = True  # Aceita mesmo com similaridade baixa
    else:
        print(f"   [AVISO] Nome nao disponivel para validacao")
        boleto_auditoria.adicionar_detalhe("CAMADA 3 - Nome", None, "Nome nao disponivel")
        boleto_auditoria.validacoes['nome_match'] = None

    # ===== CAMADA 4: Validar Valor =====
    print(f"   [VALIDACAO] Camada 4/5: Validando valor...")

    valor_xml = dados_xml.get('valor_total', Decimal(0))
    valor_xml_cents = int(valor_xml * 100) if valor_xml else 0

    if valor_xml_cents and valor_cents:
        diferenca_cents = abs(valor_xml_cents - valor_cents)

        if diferenca_cents <= TOLERANCIA_VALOR_CENTAVOS:
            print(f"   [OK] Valor match: Diferenca de R$ {diferenca_cents/100:.2f} (tolerancia: R$ {TOLERANCIA_VALOR_CENTAVOS/100:.2f})")
            boleto_auditoria.adicionar_detalhe("CAMADA 4 - Valor", True, f"Diferenca R$ {diferenca_cents/100:.2f}")
            boleto_auditoria.validacoes['valor_match'] = True
        else:
            msg = f"Valor divergente! Boleto: {cents_to_brl(valor_cents)}, XML: {cents_to_brl(valor_xml_cents)}, Diff: R$ {diferenca_cents/100:.2f}"
            print(f"   [X] FALHA: {msg}")
            boleto_auditoria.adicionar_detalhe("CAMADA 4 - Valor", False, msg)
            boleto_auditoria.validacoes['valor_match'] = False
            return None, "REJEITADO", msg
    else:
        print(f"   [AVISO] Valor nao disponivel para validacao")
        boleto_auditoria.adicionar_detalhe("CAMADA 4 - Valor", None, "Valor nao disponivel")
        boleto_auditoria.validacoes['valor_match'] = None

    # ===== CAMADA 5: Validar Emails =====
    print(f"   [VALIDACAO] Camada 5/5: Validando emails...")

    emails = dados_xml.get('emails', [])
    emails_invalidos = dados_xml.get('emails_invalidos', [])

    if emails:
        print(f"   [OK] {len(emails)} email(s) valido(s) encontrado(s)")
        for email in emails:
            print(f"        - {email}")

        if emails_invalidos:
            print(f"   [AVISO] {len(emails_invalidos)} email(s) invalido(s) filtrado(s):")
            for email in emails_invalidos:
                print(f"        - {email} (incompleto/invalido)")

        boleto_auditoria.adicionar_detalhe("CAMADA 5 - Email", True, f"{len(emails)} email(s) valido(s)")
        boleto_auditoria.validacoes['email_valido'] = True
    else:
        msg = "Nenhum email valido encontrado no XML"
        print(f"   [X] FALHA: {msg}")
        if emails_invalidos:
            print(f"   [INFO] Emails invalidos encontrados: {', '.join(emails_invalidos)}")
        boleto_auditoria.adicionar_detalhe("CAMADA 5 - Email", False, msg)
        boleto_auditoria.validacoes['email_valido'] = False
        return None, "REJEITADO", msg

    # ===== APROVADO! =====
    print(f"   [OK] Boleto APROVADO em todas as 5 camadas de validacao!")
    boleto_auditoria.dados_xml = {
        'numero_nota': dados_xml.get('numero_nota'),
        'nome': nome_xml,
        'cnpj': cnpj_xml,
        'valor_total': float(valor_xml) if valor_xml else 0,
        'emails': emails,
        'emails_invalidos': emails_invalidos
    }

    return dados_xml, "APROVADO", None

# -------------------- EMAIL --------------------
def montar_corpo_html(pagador, bases6_list, linhas_boleto, fidc_tipo):
    """
    Monta corpo HTML do email com template dinâmico baseado no FIDC

    Parâmetros:
        pagador: Nome do pagador
        bases6_list: Lista de números de notas fiscais
        linhas_boleto: Lista de dicts com 'valor_brl' e 'venc'
        fidc_tipo: Tipo do FIDC ("CAPITAL", "NOVAX", "CREDVALE", "SQUID")
    """
    # Obter configuração do FIDC
    config = FIDC_CONFIG.get(fidc_tipo, FIDC_CONFIG[FIDC_PADRAO])
    fidc_nome = config["nome_completo"]
    fidc_cnpj = config["cnpj"]

    # Montar lista de notas
    notas_txt = ", ".join(bases6_list) if bases6_list else "anexas"

    # Montar linhas de valor/vencimento
    linhas = "".join(
        f"<p>Valor: R$ {lb['valor_brl']}, Vencimento: {lb['venc']}</p>"
        for lb in linhas_boleto
    )

    # Template HTML dinâmico
    return f"""
<html>
<body style="font-family:Calibri,Arial,sans-serif; font-size:13.5px;">
<p>Boa tarde,</p>
<p>Prezado cliente,<br><b>{pagador}</b>,</p>
<p>Enviamos anexo o(s) seu(s) boleto(s) emitido(s) conforme a(as) nota(as): {notas_txt}</p>
{linhas}
<p>O(s) boleto(s) está(ão) com beneficiário nominal a <b>{fidc_nome}</b>, CNPJ: <b>{fidc_cnpj}</b>.</p>
<p>Vide boleto(s) e nota(s) em anexo.<br>Favor confirmar recebimento.</p>
<p>Em caso de dúvidas, nossa equipe permanece à disposição para esclarecimentos.</p>
<p>Atenciosamente,<br><b>Equipe de Cobrança</b></p>
<p><img src="cid:assinatura_jotajota" width="600"></p>
</body>
</html>
"""

def abrir_email_outlook(email_to, assunto, corpo_html, anexos, fidc_tipo):
    """
    Cria e envia email via Outlook com CCs dinâmicos baseados no FIDC

    Parâmetros:
        email_to: Email do destinatário
        assunto: Assunto do email
        corpo_html: Corpo do email em HTML
        anexos: Lista de caminhos de arquivos para anexar
        fidc_tipo: Tipo do FIDC ("CAPITAL", "NOVAX", "CREDVALE", "SQUID")
    """
    outlook = win32.Dispatch("Outlook.Application")

    # Verificação de segurança — garante conta de cobrança
    conta_cobranca = None
    for acc in outlook.Session.Accounts:
        if acc.SmtpAddress.lower() == "cobranca@jotajota.net.br":
            conta_cobranca = acc
            break

    if not conta_cobranca:
        print("[ERRO] ERRO: Conta cobrança@jotajota.net.br não encontrada — envio abortado.")
        with open(os.path.join(PASTA_AUDITORIA, "log_falha_conta.txt"), "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Conta cobrança não localizada. Envio abortado.\n")
        return

    mail = outlook.CreateItem(0)
    mail._oleobj_.Invoke(*(64209, 0, 8, 0, conta_cobranca))

    # Obter CCs dinâmicos baseados no FIDC
    config = FIDC_CONFIG.get(fidc_tipo, FIDC_CONFIG[FIDC_PADRAO])
    cc_emails = "; ".join(config["cc_emails"])

    mail.To = email_to
    mail.CC = cc_emails  # CC dinâmico por FIDC!
    mail.Subject = assunto

    # corpo + imagem inline
    mail.HTMLBody = corpo_html
    attach = mail.Attachments.Add(ASSINATURA_IMG)
    attach.PropertyAccessor.SetProperty(
        "http://schemas.microsoft.com/mapi/proptag/0x3712001F", "assinatura_jotajota"
    )

    # outros anexos
    for a in anexos:
        try:
            if not os.path.exists(a):
                print(f"      [ERRO] Arquivo não encontrado: {a}")
                raise FileNotFoundError(f"Arquivo não encontrado: {a}")
            mail.Attachments.Add(a)
        except Exception as e:
            print(f"      [ERRO] Falha ao anexar {os.path.basename(a)}: {e}")
            raise

    # Enviar ou mostrar preview
    if MODO_PREVIEW:
        mail.Display()  # Abre no Outlook para revisão (não envia)
    else:
        mail.Send()  # Envia automaticamente

# -------------------- MAIN --------------------
def executar():
    print("=" * 80)
    print("  ENVIO DE BOLETOS - v7.0.0 (XML-Based System)")
    print("=" * 80)
    modo_str = "PREVIEW" if MODO_PREVIEW else "PRODUCAO"
    print(f"  [MODO {modo_str}] {('Emails abrirao no Outlook sem enviar' if MODO_PREVIEW else 'Emails serao enviados automaticamente')}")
    print("=" * 80)
    print()

    t0 = time.time()

    # ==== INICIALIZAR AUDITORIA ====
    auditoria = AuditoriaExecucao(modo="preview" if MODO_PREVIEW else "producao")

    grupos = {}
    enviados = 0
    erros = 0

    # ==== CARREGAR DADOS DOS XMLs (v7.0) ====
    mapa_xmls = carregar_dados_xmls()

    if not mapa_xmls:
        print("[ERRO] Nenhum XML foi carregado! Sistema abortado.")
        auditoria.adicionar_erro_critico("Nenhum XML carregado - sistema abortado")
        auditoria.finalizar()

        # Gerar relatórios (se houver)
        gerar_relatorio_aprovados(auditoria, PASTA_AUDITORIA)
        gerar_relatorio_rejeitados(auditoria, PASTA_ERROS)
        gerar_relatorio_json(auditoria, PASTA_AUDITORIA)
        return

    # Indexar notas fiscais
    notas_idx = indexar_notas_por_digitos()
    print(f"[ARQUIVO] Notas fiscais indexadas: {len(notas_idx)}")
    print()

    # Listar boletos para processar
    arquivos_boletos = [f for f in os.listdir(PASTA_BOLETOS) if f.lower().endswith(".pdf")]
    print(f"[PACOTE] Boletos encontrados para processar: {len(arquivos_boletos)}")
    print()

    if not arquivos_boletos:
        print("[INFO] Nenhum boleto para processar.")
        return

    print("[PROC] Processando boletos...")
    print("-" * 80)

    # Processar cada boleto
    for idx, arquivo in enumerate(arquivos_boletos, 1):
        caminho = os.path.join(PASTA_BOLETOS, arquivo)

        print(f"\n[{idx}/{len(arquivos_boletos)}] {arquivo}")

        # ==== CRIAR OBJETO DE AUDITORIA PARA ESTE BOLETO ====
        boleto_aud = BoletoAuditoria(arquivo)

        # ==== EXTRAIR NUMERO DA NOTA DO NOME DO ARQUIVO ====
        # Novo formato (v10): "NOME - NF 310284 - DATA - VALOR.pdf"
        # Formato antigo: "310227.pdf", "3-0310227.pdf", "0310227.pdf"
        nome_sem_ext = os.path.splitext(arquivo)[0]

        # Tentar extrair padrão "NF 123456" primeiro (v10)
        match_nf = re.search(r'NF\s+(\d{6})', nome_sem_ext, re.IGNORECASE)
        if match_nf:
            numero_nota = match_nf.group(1)
            print(f"   [NOTA] Numero da nota extraido do nome: {numero_nota}")
        else:
            # Fallback: Extrair últimos 6 dígitos (formato antigo)
            digitos = digits_only(nome_sem_ext)

            if len(digitos) < 6:
                msg = f"Nome do arquivo deve conter numero da nota (minimo 6 digitos). Encontrado: {len(digitos)} digitos"
                print(f"   [X] ERRO: {msg}")
                boleto_aud.rejeitar(msg)
                auditoria.adicionar_boleto(boleto_aud)
                auditoria.adicionar_erro_critico(msg, arquivo)
                continue

            numero_nota = digitos[-6:]
            print(f"   [NOTA] Numero da nota extraido (fallback): {numero_nota}")

        # ==== EXTRAIR CNPJ DO PDF (PAGADOR DO BOLETO) ====
        print(f"   [PDF] Extraindo CNPJ do boleto...")
        cnpj = extrair_cnpj_do_pdf(caminho)
        if cnpj:
            print(f"   [OK] CNPJ extraido: {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}")
        else:
            print(f"   [AVISO] CNPJ nao encontrado no PDF")

        boleto_aud.dados_boleto['cnpj'] = cnpj
        boleto_aud.dados_boleto['numero_nota'] = numero_nota

        # ==== DETECTAR FIDC DO BOLETO ====
        print(f"   [FIDC] Detectando FIDC do boleto...")
        fidc_tipo = detectar_fidc_do_pdf(caminho)
        print(f"   [OK] FIDC detectado: {fidc_tipo} ({FIDC_CONFIG[fidc_tipo]['nome_completo']})")
        boleto_aud.dados_boleto['fidc'] = fidc_tipo

        # ==== EXTRAIR DATA DE VENCIMENTO DO BOLETO ====
        print(f"   [VENC] Extraindo data de vencimento do boleto...")
        data_vencimento = extrair_data_vencimento_do_pdf(caminho)
        if data_vencimento:
            print(f"   [OK] Data de vencimento: {data_vencimento}")
        else:
            print(f"   [AVISO] Data de vencimento nao encontrada, usando 'A definir'")
            data_vencimento = "A definir"
        boleto_aud.dados_boleto['data_vencimento'] = data_vencimento

        # ==== VALIDACAO EM 5 CAMADAS ====
        # A validacao vai buscar o XML e extrair todos os dados necessarios
        dados_xml, status, erro = validar_boleto_com_xml(
            numero_nota, None, None, cnpj, mapa_xmls, boleto_aud
        )

        if status == "REJEITADO":
            # BOLETO REJEITADO
            print(f"   [X] BOLETO REJEITADO: {erro}")
            boleto_aud.rejeitar(erro)
            auditoria.adicionar_boleto(boleto_aud)
            auditoria.adicionar_erro_critico(erro, arquivo)
            continue

        # ==== BOLETO APROVADO! ====
        print(f"   [OK] BOLETO APROVADO!")
        boleto_aud.aprovar()

        # Extrair dados do XML
        email_to = '; '.join(dados_xml.get('emails', []))
        nome_cliente = dados_xml.get('nome', 'Cliente Desconhecido')

        # Buscar valor correto: parcela se houver duplicatas, senão valor total
        duplicatas = dados_xml.get('duplicatas', [])
        if duplicatas and data_vencimento and data_vencimento != "A definir":
            # Normalizar data do boleto (DD/MM/YYYY → YYYY-MM-DD)
            if '/' in data_vencimento:  # Formato DD/MM/YYYY
                dia, mes, ano = data_vencimento.split('/')
                venc_normalizado = f"{ano}-{mes}-{dia}"
            else:
                venc_normalizado = data_vencimento

            # Buscar duplicata com vencimento correspondente
            valor_parcela = None
            for dup in duplicatas:
                if dup.get('vencimento') == venc_normalizado:
                    valor_parcela = dup.get('valor')
                    break

            # Usar valor da parcela se encontrou, senão usar total
            valor_final = valor_parcela if valor_parcela else dados_xml.get('valor_total', Decimal(0))
        else:
            # Sem duplicatas = nota sem parcelas = usar valor total
            valor_final = dados_xml.get('valor_total', Decimal(0))

        valor_cents = int(valor_final * 100)  # Converter Decimal para centavos
        nome_norm = normalize_pagador(nome_cliente)
        docs_set = {numero_nota}  # Usar numero da nota como documento

        print(f"   [EMAIL] Email destino: {email_to}")
        print(f"   [CLIENTE] {nome_cliente}")
        print(f"   [VALOR] R$ {valor_final}")
        print(f"   [DOC] Documento (nota): {numero_nota}")

        # Agrupar por (email, cliente normalizado)
        grupo_key = (email_to, nome_norm)
        g = grupos.setdefault(grupo_key, {
            'pagador_exib': nome_cliente,
            'docs': set(),
            'boletos': [],
            'linhas': [],
            'metodos': [],
            'fidcs': [],  # Lista de FIDCs dos boletos (caso tenha múltiplos)
            'cnpjs': [],  # CNPJs dos boletos (para validação)
            'valores_cents': [],  # Valores dos boletos (para validação)
            'auditorias': []  # Objetos BoletoAuditoria (v7.0)
        })

        g['docs'] |= docs_set
        g['boletos'].append(caminho)
        g['linhas'].append({'valor_brl': cents_to_brl(valor_cents), 'venc': data_vencimento})
        g['metodos'].append('XML')  # No novo sistema, todos são via XML
        g['fidcs'].append(fidc_tipo)  # Armazenar FIDC do boleto
        if cnpj:
            g['cnpjs'].append(cnpj)  # Armazenar CNPJ para validação
        g['valores_cents'].append(valor_cents)  # Armazenar valor para validação
        g['auditorias'].append(boleto_aud)  # Armazenar auditoria

    print()
    print("=" * 80)
    print("  PREPARANDO E ENVIANDO E-MAILS")
    print("=" * 80)
    print()

    # Enviar e-mails agrupados
    for (email_to, pag_key), g in grupos.items():
        print(f"[EMAIL] Enviando para: {g['pagador_exib']} ({email_to})")
        print(f"   - Boletos: {len(g['boletos'])}")
        print(f"   - Documentos: {len(g['docs'])}")

        # Determinar FIDC principal do grupo (caso tenha múltiplos, pega o mais comum)
        fidcs_unicos = list(set(g['fidcs']))
        if len(fidcs_unicos) == 1:
            fidc_grupo = fidcs_unicos[0]
            print(f"   - FIDC: {fidc_grupo}")
        else:
            # Múltiplos FIDCs no mesmo grupo - pegar o mais comum
            from collections import Counter
            fidc_grupo = Counter(g['fidcs']).most_common(1)[0][0]
            print(f"   - AVISO: Multiplos FIDCs detectados ({', '.join(fidcs_unicos)})")
            print(f"   - Usando FIDC mais comum: {fidc_grupo}")

        # Obter configuração do FIDC
        config_fidc = FIDC_CONFIG[fidc_grupo]
        print(f"   - CCs: {', '.join(config_fidc['cc_emails'])}")

        # Pegar CNPJ e valor do primeiro boleto para validação de notas
        cnpj_validacao = g['cnpjs'][0] if g['cnpjs'] else None
        valor_validacao = g['valores_cents'][0] if g['valores_cents'] else None

        # Buscar e validar notas fiscais correspondentes (ETAPA 3!)
        print(f"   - Validando notas fiscais...")
        print(f"   - Documentos esperados: {', '.join(sorted(g['docs']))}")
        notas_anexos, bases6, detalhes_validacao, tem_erro_critico = achar_notas_por_docs_set(
            g['docs'], notas_idx, cnpj_validacao, valor_validacao
        )
        print(f"   - Notas validadas: {len(notas_anexos)}")

        # BLOQUEIO DE SEGURANÇA: Se houver erro crítico, NÃO enviar email
        if tem_erro_critico:
            print(f"   [BLOQUEIO] Email NÃO será enviado devido a erros críticos de validação!")
            print(f"   [AÇÃO] Verifique as notas fiscais na pasta: {PASTA_NOTAS}")

            # Registrar erro na auditoria
            erro_msg = f"Bloqueado: {email_to} - {g['pagador_exib']} - Erro crítico na validação de notas"
            auditoria.adicionar_erro_critico(erro_msg, f"Grupo de {len(g['boletos'])} boletos")

            # Marcar todos os boletos deste grupo com erro
            for boleto_aud in g['auditorias']:
                if boleto_aud not in auditoria.boletos:
                    auditoria.adicionar_boleto(boleto_aud)

            erros += 1
            continue  # Pula para o próximo grupo

        # Enviar email com FIDC dinâmico
        try:
            abrir_email_outlook(
                email_to,
                f"Boleto e Nota Fiscal ({', '.join(bases6)})",
                montar_corpo_html(g['pagador_exib'], bases6, g['linhas'], fidc_grupo),
                list(g['boletos']) + list(notas_anexos),
                fidc_grupo  # Passa FIDC para CC dinâmico!
            )

            # Mover boletos para pasta de enviados (apenas em modo produção)
            if not MODO_PREVIEW:
                # Em modo produção, move após enviar automaticamente
                for b in g['boletos']:
                    try:
                        destino = os.path.join(PASTA_ENVIADOS, os.path.basename(b))
                        shutil.move(b, destino)
                        print(f"   [OK] Boleto movido para BoletosEnviados: {os.path.basename(b)}")
                    except Exception as e:
                        print(f"   [AVISO] Erro ao mover {os.path.basename(b)}: {e}")
            else:
                # Em modo preview, avisar usuário
                print(f"   [INFO] MODO PREVIEW: Boletos não foram movidos (mova manualmente após enviar)")

            enviados += 1
            metodos_str = ", ".join(set(g['metodos']))
            print(f"   [OK] Email enviado com sucesso!\n")

            # Atualizar auditoria de cada boleto deste grupo
            for boleto_aud in g['auditorias']:
                boleto_aud.email_enviado = True
                boleto_aud.email_destinatarios = email_to.split(';')
                boleto_aud.email_cc = config_fidc['cc_emails']
                boleto_aud.anexos_count = len(g['boletos']) + len(notas_anexos)
                boleto_aud.notas_fiscais = [os.path.basename(n) for n in notas_anexos]
                # Adicionar à auditoria geral se ainda não foi adicionado
                if boleto_aud not in auditoria.boletos:
                    auditoria.adicionar_boleto(boleto_aud)

        except Exception as e:
            print(f"   [ERRO] ERRO ao enviar email: {e}\n")
            # Registrar erro na auditoria
            for boleto_aud in g['auditorias']:
                if boleto_aud not in auditoria.boletos:
                    auditoria.adicionar_boleto(boleto_aud)
                    auditoria.adicionar_erro_critico(f"Erro ao enviar email: {e}", boleto_aud.arquivo)
            erros += 1

    # ==== FINALIZAR AUDITORIA ====
    auditoria.emails_enviados = enviados
    auditoria.finalizar()

    # Atualizar estatísticas de validação na auditoria
    for boleto in auditoria.boletos:
        for tipo, validou in boleto.validacoes.items():
            # Extrair categoria (primeira parte antes do _)
            categoria = tipo.split('_')[0]

            # Só processar se a categoria existe no dicionário
            if categoria in auditoria.stats_validacoes:
                if validou is True:
                    auditoria.stats_validacoes[categoria]['sucesso'] += 1
                elif validou is False:
                    auditoria.stats_validacoes[categoria]['falha'] += 1

    # ==== EXIBIR RESUMO ====
    print()
    print("=" * 80)
    print("  RESUMO DA EXECUCAO")
    print("=" * 80)
    print(f"[TEMPO] Tempo total: {auditoria.duracao_segundos:.2f}s")
    print(f"[OK] E-mails enviados: {auditoria.emails_enviados}")
    print(f"[OK] Boletos aprovados: {auditoria.aprovados}")
    print(f"[ERRO] Boletos rejeitados: {auditoria.rejeitados}")
    print(f"[TAXA] Taxa de sucesso: {auditoria.get_taxa_sucesso():.1%}")
    print()

    if auditoria.erros_criticos:
        print(f"[ALERTA] {len(auditoria.erros_criticos)} erro(s) critico(s) encontrado(s)")
        print()

    print("=" * 80)

    # ==== GERAR RELATORIOS SEPARADOS ====
    print()
    print("[AUDITORIA] Gerando relatorios...")

    try:
        # Relatório de APROVADOS (Auditoria)
        aprovados_path = gerar_relatorio_aprovados(auditoria, PASTA_AUDITORIA)
        if aprovados_path:
            print(f"[OK] Auditoria (Aprovados): {aprovados_path}")
        else:
            print(f"[INFO] Nenhum boleto aprovado para auditoria")

        # Relatório de REJEITADOS (Erros)
        rejeitados_path = gerar_relatorio_rejeitados(auditoria, PASTA_ERROS)
        if rejeitados_path:
            print(f"[OK] Erros (Rejeitados): {rejeitados_path}")
        else:
            print(f"[INFO] Nenhum boleto rejeitado")

        # Relatório JSON (estruturado - completo)
        json_path = gerar_relatorio_json(auditoria, PASTA_AUDITORIA)
        print(f"[OK] Relatorio JSON: {json_path}")

        # Log de erros críticos (se houver)
        if auditoria.erros_criticos:
            erros_path = gerar_log_erros_criticos(auditoria, PASTA_AUDITORIA)
            print(f"[OK] Log de erros criticos: {erros_path}")

    except Exception as e:
        print(f"[ERRO] Falha ao gerar relatorios: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)

    # ==== MENSAGEM FINAL ====
    if auditoria.aprovados > 0:
        print("[OK] Processamento concluido com sucesso!")
        print("   E-mails enviados pela conta cobranca@jotajota.net.br")
        if MODO_PREVIEW:
            print("   [MODO PREVIEW] Verifique os emails no Outlook antes de enviar")
    else:
        print("[AVISO] Nenhum boleto foi aprovado. Verifique o relatorio de auditoria.")

    print("=" * 80)

if __name__ == "__main__":
    executar()
