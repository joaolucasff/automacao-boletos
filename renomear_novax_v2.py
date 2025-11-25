"""
Script de Renomeação NOVAX - v2 (Do Zero)

Script ISOLADO e LIMPO para renomear boletos NOVAX usando XML como fonte principal.

Autor: Claude Code
Data: 2025-11-04
"""

import os
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Adicionar pasta _build_server ao path
sys.path.insert(0, r'C:\Users\User-OEM\Desktop\BoletosAutomação\_build_server')

import pdfplumber
from unidecode import unidecode
from xml_nfe_reader import extrair_dados_nfe


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Pasta com as NOTAS (XMLs + PDFs das notas fiscais)
PASTA_NOTAS = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletosnovax'

# Pasta com os BOLETOS (PDFs dos boletos bancários a serem renomeados)
PASTA_BOLETOS = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletosnovax\Boletos'

# Pasta de saída (boletos renomeados) - será criada com timestamp
PASTA_SAIDA_BASE = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletosnovax\Boletos_RENOMEADOS'

RELATORIO_EMAILS = 'novax_emails_relatorio.txt'


# ============================================================================
# FUNÇÕES DE INDEXAÇÃO XML
# ============================================================================

def indexar_xmls_novax(pasta: str) -> Dict[str, dict]:
    """
    Indexa todos os XMLs da pasta e retorna mapa {numero_nota: dados}

    Returns:
        {
            "310018": {
                'nome': str,
                'cnpj': str,
                'cpf_cnpj': str,
                'valor_total': Decimal,
                'duplicatas': [{numero, vencimento, valor}, ...],
                'emails': [email1, email2, ...]
            }
        }
    """
    print("\n[XML] Indexando XMLs da pasta NOVAX...")
    mapa_xmls = {}

    arquivos_xml = [f for f in os.listdir(pasta) if f.endswith('.xml')]
    print(f"[XML] {len(arquivos_xml)} XMLs encontrados")

    for xml_file in arquivos_xml:
        try:
            xml_path = os.path.join(pasta, xml_file)
            dados = extrair_dados_nfe(xml_path)

            # Extrair número da nota do nome do arquivo ou do XML
            numero_nota = extrair_numero_nota_arquivo(xml_file)

            if numero_nota and numero_nota != "SEM_NOTA":
                mapa_xmls[numero_nota] = dados

        except Exception as e:
            print(f"[AVISO] Erro ao processar XML {xml_file}: {e}")
            continue

    print(f"[XML] {len(mapa_xmls)} XMLs indexados com sucesso\n")
    return mapa_xmls


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO
# ============================================================================

def extrair_numero_nota_arquivo(filename: str) -> Optional[str]:
    """
    Extrai número da nota do nome do arquivo

    Exemplos:
        "3-310018.pdf" → "310018"
        "3-310018.xml" → "310018"
        "310018.pdf" → "310018"
    """
    # Padrão 1: "3-310018.pdf"
    match = re.search(r'\d+-0?(\d{6})', filename)
    if match:
        return match.group(1)

    # Padrão 2: "310018.pdf"
    match = re.search(r'^0?(\d{6})', filename)
    if match:
        return match.group(1)

    return None


def extrair_cnpj_boleto(texto: str) -> Optional[str]:
    """
    Extrai CNPJ/CPF do boleto NOVAX

    Busca após "Pagador" ou em linha com CNPJ/CPF
    Retorna apenas dígitos (14 para CNPJ, 11 para CPF)
    """
    linhas = texto.splitlines()

    # Buscar após PAGADOR
    for i, linha in enumerate(linhas):
        if "PAGADOR" in linha.upper():
            # Próximas 3-4 linhas podem conter o CNPJ/CPF
            for j in range(i, min(i + 5, len(linhas))):
                linha_busca = linhas[j]

                # Padrão CPF: XXX.XXX.XXX-XX
                match_cpf = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', linha_busca)
                if match_cpf:
                    cpf = match_cpf.group(1)
                    return re.sub(r'[.-]', '', cpf)

                # Padrão CNPJ: XX.XXX.XXX/XXXX-XX
                match_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', linha_busca)
                if match_cnpj:
                    cnpj = match_cnpj.group(1)
                    return re.sub(r'[./-]', '', cnpj)

    # Fallback: buscar em qualquer lugar do texto
    # CPF
    match_cpf = re.search(r'CPF[:\s]*(\d{3}\.\d{3}\.\d{3}-\d{2})', texto, re.IGNORECASE)
    if match_cpf:
        return re.sub(r'[.-]', '', match_cpf.group(1))

    # CNPJ
    match_cnpj = re.search(r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto, re.IGNORECASE)
    if match_cnpj:
        return re.sub(r'[./-]', '', match_cnpj.group(1))

    return None


def extrair_vencimento_boleto(texto: str) -> Optional[str]:
    """
    Extrai data de vencimento do boleto

    Busca padrão DD/MM/YYYY e retorna DD-MM
    """
    linhas = texto.splitlines()

    for i, linha in enumerate(linhas):
        if "VENCIMENTO" in linha.upper():
            # Tentar na mesma linha
            match = re.search(r'(\d{2})/(\d{2})/\d{4}', linha)
            if not match and i + 1 < len(linhas):
                # Tentar na próxima linha
                match = re.search(r'(\d{2})/(\d{2})/\d{4}', linhas[i + 1])

            if match:
                dia = match.group(1)
                mes = match.group(2)
                return f"{dia}-{mes}"

    return None


# ============================================================================
# VALIDAÇÃO DE EMAILS
# ============================================================================

def validar_email(email: str) -> bool:
    """
    Valida se email está completo (tem @ e domínio)

    Exemplos:
        "cliente@empresa.com" → True
        "cliente@emp" → False (cortado)
        "cliente" → False (sem @)
    """
    if not email or '@' not in email:
        return False

    partes = email.split('@')
    if len(partes) != 2:
        return False

    usuario, dominio = partes

    # Validações básicas
    if not usuario or not dominio:
        return False

    # Domínio deve ter pelo menos um ponto e extensão
    if '.' not in dominio:
        return False

    # Extensão deve ter pelo menos 2 caracteres
    extensao = dominio.split('.')[-1]
    if len(extensao) < 2:
        return False

    return True


def extrair_emails_validos(emails_xml: List[str], max_emails: int = 2) -> List[str]:
    """
    Extrai emails válidos do XML (máximo 2)

    Ignora emails cortados/incompletos
    """
    emails_validos = []

    for email in emails_xml[:5]:  # Checar até 5 emails
        if validar_email(email):
            emails_validos.append(email)
            if len(emails_validos) >= max_emails:
                break

    return emails_validos


# ============================================================================
# LÓGICA DE PROCESSAMENTO
# ============================================================================

def escolher_valor_correto(dados_xml: dict, vencimento_boleto: str) -> Tuple[str, str]:
    """
    Escolhe o valor correto baseado em duplicatas

    Lógica:
        - Se tem duplicatas: buscar por vencimento → usar duplicata.valor
        - Se NÃO tem duplicatas: usar valor_total

    Returns:
        (valor_formatado, origem)
        origem: "DUPLICATA" ou "TOTAL"
    """
    duplicatas = dados_xml.get('duplicatas', [])

    if duplicatas:
        # Tem duplicatas - buscar por vencimento
        # Converter vencimento boleto "DD-MM" para formato XML "YYYY-MM-DD"
        # Precisamos comparar apenas dia e mês
        if vencimento_boleto:
            dia, mes = vencimento_boleto.split('-')

            for dup in duplicatas:
                venc_xml = dup.get('vencimento', '')  # "2025-12-12"
                if venc_xml:
                    # Pegar apenas DD-MM do XML
                    partes = venc_xml.split('-')  # ["2025", "12", "12"]
                    if len(partes) == 3:
                        dia_xml = partes[2]
                        mes_xml = partes[1]

                        if dia == dia_xml and mes == mes_xml:
                            # Match! Usar valor desta duplicata
                            valor = dup['valor']
                            if isinstance(valor, Decimal):
                                valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            else:
                                valor_formatado = f"R$ {valor}"
                            return (valor_formatado, "DUPLICATA")

        # Se não achou duplicata por vencimento, usar primeira duplicata
        if duplicatas:
            valor = duplicatas[0]['valor']
            if isinstance(valor, Decimal):
                valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_formatado = f"R$ {valor}"
            return (valor_formatado, "DUPLICATA_PRIMEIRA")

    # Não tem duplicatas - usar valor total
    valor_total = dados_xml.get('valor_total')
    if valor_total:
        if isinstance(valor_total, (Decimal, float)):
            valor_formatado = f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            valor_formatado = f"R$ {valor_total}"
        return (valor_formatado, "TOTAL")

    return ("R$ 0,00", "NAO_ENCONTRADO")


def buscar_xml_por_cnpj_e_vencimento(cnpj_boleto: str, vencimento_boleto: str, mapa_xmls: Dict[str, dict]) -> Tuple[Optional[str], Optional[dict], Optional[dict]]:
    """
    Busca XML por CNPJ/CPF e vencimento

    Returns:
        (numero_nota, dados_xml, duplicata_matched)
    """
    if not cnpj_boleto or not vencimento_boleto:
        return (None, None, None)

    # Converter vencimento "DD-MM" para comparar
    dia, mes = vencimento_boleto.split('-')

    # Buscar em todos os XMLs
    for numero_nota, dados_xml in mapa_xmls.items():
        # Usar 'cpf_cnpj' que funciona tanto para CPF quanto CNPJ
        cpf_cnpj_xml = dados_xml.get('cpf_cnpj', '') or dados_xml.get('cnpj', '')

        # Match por CNPJ/CPF
        if cnpj_boleto == cpf_cnpj_xml:
            # Tem match de CNPJ - agora buscar duplicata por vencimento
            duplicatas = dados_xml.get('duplicatas', [])

            if duplicatas:
                for dup in duplicatas:
                    venc_xml = dup.get('vencimento', '')  # "2025-11-17"
                    if venc_xml:
                        partes = venc_xml.split('-')  # ["2025", "11", "17"]
                        if len(partes) == 3:
                            dia_xml = partes[2]
                            mes_xml = partes[1]

                            if dia == dia_xml and mes == mes_xml:
                                # Match perfeito!
                                return (numero_nota, dados_xml, dup)

                # Se não achou duplicata por vencimento, mas CNPJ bateu
                # Retornar primeiro (pode ter apenas 1 duplicata)
                if len(duplicatas) == 1:
                    return (numero_nota, dados_xml, duplicatas[0])

            else:
                # Não tem duplicatas - nota de parcela única
                return (numero_nota, dados_xml, None)

    return (None, None, None)


def processar_boleto_novax(pdf_path: str, mapa_xmls: Dict[str, dict]) -> dict:
    """
    Processa um boleto NOVAX e retorna dados para renomeação

    Match por CNPJ + vencimento (não usa número da nota do filename)

    Returns:
        {
            'status': 'ok' | 'erro',
            'novo_nome': str,
            'emails': [email1, email2],
            'erro_msg': str,
            'detalhes': {...}
        }
    """
    filename = os.path.basename(pdf_path)
    resultado = {
        'status': 'erro',
        'novo_nome': '',
        'emails': [],
        'erro_msg': '',
        'detalhes': {}
    }

    try:
        # 1. Extrair texto do PDF
        with pdfplumber.open(pdf_path) as pdf:
            texto = "".join([page.extract_text() or "" for page in pdf.pages])

        # 2. Extrair dados do boleto
        cnpj_boleto = extrair_cnpj_boleto(texto)
        vencimento_boleto = extrair_vencimento_boleto(texto)

        resultado['detalhes']['cnpj_boleto'] = cnpj_boleto
        resultado['detalhes']['vencimento_boleto'] = vencimento_boleto

        if not cnpj_boleto:
            resultado['erro_msg'] = "Não foi possível extrair CNPJ/CPF do boleto"
            return resultado

        if not vencimento_boleto:
            resultado['erro_msg'] = "Não foi possível extrair vencimento do boleto"
            return resultado

        # 3. Buscar XML por CNPJ + vencimento
        numero_nota, dados_xml, duplicata_matched = buscar_xml_por_cnpj_e_vencimento(
            cnpj_boleto, vencimento_boleto, mapa_xmls
        )

        if not numero_nota or not dados_xml:
            resultado['erro_msg'] = f"XML não encontrado para CNPJ={cnpj_boleto}, vencimento={vencimento_boleto}"
            return resultado

        resultado['detalhes']['numero_nota'] = numero_nota
        resultado['detalhes']['xml_encontrado'] = True

        # 4. Escolher valor correto
        valor, origem_valor = escolher_valor_correto(dados_xml, vencimento_boleto)
        resultado['detalhes']['valor'] = valor
        resultado['detalhes']['origem_valor'] = origem_valor

        # 5. Extrair emails válidos
        emails_xml = dados_xml.get('emails', [])
        emails_validos = extrair_emails_validos(emails_xml, max_emails=2)
        resultado['emails'] = emails_validos

        # 6. Montar novo nome
        pagador = dados_xml.get('nome', 'SEM_PAGADOR')

        # Limpar nome do pagador
        pagador_limpo = unidecode(pagador)
        pagador_limpo = re.sub(r'[\\/*?:"<>|]', '-', pagador_limpo)
        pagador_limpo = re.sub(r'\s+', ' ', pagador_limpo).strip()

        # Truncar se muito longo
        if len(pagador_limpo) > 60:
            pagador_limpo = pagador_limpo[:60]

        # Formato: PAGADOR - NF NUMERO - DD-MM - R$ VALOR.pdf
        novo_nome = f"{pagador_limpo} - NF {numero_nota} - {vencimento_boleto or 'SEM_VENC'} - {valor}.pdf"

        resultado['status'] = 'ok'
        resultado['novo_nome'] = novo_nome
        resultado['detalhes']['pagador'] = pagador_limpo

        return resultado

    except Exception as e:
        resultado['erro_msg'] = f"Exceção: {type(e).__name__}: {str(e)}"
        return resultado


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def renomear_novax():
    """
    Função principal - processa todos os boletos NOVAX
    """
    print("=" * 80)
    print("RENOMEAÇÃO NOVAX - v2 (Script Isolado)")
    print("=" * 80)

    # Verificar pastas
    if not os.path.exists(PASTA_NOTAS):
        print(f"[ERRO] Pasta de notas não encontrada: {PASTA_NOTAS}")
        return

    if not os.path.exists(PASTA_BOLETOS):
        print(f"[ERRO] Pasta de boletos não encontrada: {PASTA_BOLETOS}")
        return

    # Criar pasta de saída com timestamp
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    PASTA_SAIDA = f"{PASTA_SAIDA_BASE}_{timestamp}"

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    print(f"[OK] Pasta de notas (XMLs): {PASTA_NOTAS}")
    print(f"[OK] Pasta de boletos: {PASTA_BOLETOS}")
    print(f"[OK] Pasta de saída: {PASTA_SAIDA}\n")

    # Indexar XMLs (da pasta de notas)
    mapa_xmls = indexar_xmls_novax(PASTA_NOTAS)

    if not mapa_xmls:
        print("[ERRO] Nenhum XML foi indexado. Verifique a pasta.")
        return

    # Listar PDFs dos BOLETOS (não das notas)
    arquivos_pdf = [f for f in os.listdir(PASTA_BOLETOS) if f.endswith('.pdf')]
    print(f"[BOLETOS] {len(arquivos_pdf)} boletos bancários encontrados\n")

    if not arquivos_pdf:
        print("[AVISO] Nenhum PDF encontrado para processar.")
        return

    # Processar boletos
    print("=" * 80)
    print("PROCESSANDO BOLETOS")
    print("=" * 80)

    resultados = []
    sucessos = 0
    erros = 0

    for idx, arquivo in enumerate(arquivos_pdf, 1):
        print(f"\n[{idx}/{len(arquivos_pdf)}] {arquivo}")
        print("-" * 80)

        pdf_path = os.path.join(PASTA_BOLETOS, arquivo)
        resultado = processar_boleto_novax(pdf_path, mapa_xmls)

        if resultado['status'] == 'ok':
            # Copiar arquivo com novo nome
            import shutil
            caminho_destino = os.path.join(PASTA_SAIDA, resultado['novo_nome'])
            shutil.copy2(pdf_path, caminho_destino)

            print(f"  [OK] {resultado['novo_nome']}")
            print(f"  [VALOR] {resultado['detalhes'].get('valor')} (origem: {resultado['detalhes'].get('origem_valor')})")
            print(f"  [EMAILS] {', '.join(resultado['emails']) if resultado['emails'] else 'Nenhum email válido'}")

            sucessos += 1
        else:
            print(f"  [ERRO] {resultado['erro_msg']}")
            erros += 1

        resultados.append(resultado)

    # Gerar relatório de emails
    print("\n" + "=" * 80)
    print("GERANDO RELATÓRIO DE EMAILS")
    print("=" * 80)

    relatorio_path = os.path.join(PASTA_SAIDA, RELATORIO_EMAILS)
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE EMAILS - NOVAX\n")
        f.write("=" * 80 + "\n\n")

        for resultado in resultados:
            if resultado['status'] == 'ok':
                detalhes = resultado['detalhes']
                numero_nota = detalhes.get('numero_nota', 'N/A')
                pagador = detalhes.get('pagador', 'N/A')
                emails = resultado['emails']

                f.write(f"NF {numero_nota} - {pagador}\n")
                if emails:
                    f.write(f"  Emails: {', '.join(emails)}\n")
                else:
                    f.write(f"  Emails: Nenhum email válido encontrado\n")
                f.write("\n")

    print(f"[OK] Relatório salvo: {relatorio_path}")

    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print(f"Total processado: {len(arquivos_pdf)}")
    print(f"Sucessos: {sucessos}")
    print(f"Erros: {erros}")
    print(f"\nArquivos renomeados salvos em: {PASTA_SAIDA}")
    print("=" * 80)


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    renomear_novax()
