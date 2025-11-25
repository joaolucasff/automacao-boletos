"""
Script de teste v2.0 - SQUID FIDC
Baseado no padrão validado CAPITAL/NOVAX/CREDVALE
Match por CNPJ/CPF + vencimento
XML como fonte principal de dados
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict
import pdfplumber

# Adicionar o diretório _build_server ao path para importar os módulos
sys.path.insert(0, r'C:\Users\User-OEM\Desktop\BoletosAutomação\_build_server')

from extractors.squid import SQUIDExtractor
from xml_nfe_reader import extrair_dados_nfe

# ============================================================================
# CONFIGURAÇÃO - SQUID
# ============================================================================
PASTA_NOTAS = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletossquid'
PASTA_BOLETOS = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletossquid\Boletos'
PASTA_SAIDA_BASE = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletossquid\Boletos_RENOMEADOS'

def extrair_numero_nota_arquivo(filename: str) -> str:
    """
    Extrai número da nota do nome do arquivo SQUID
    Exemplos:
        "3-0305537.xml" → "305537"
        "3-305537.pdf" → "305537"
    """
    import os
    nome_arquivo = os.path.basename(filename)
    match = re.search(r'\d+-0?(\d{6})\.', nome_arquivo)
    if match:
        return match.group(1)
    return "SEM_NOTA"

def criar_mapa_xmls(pasta_notas: str) -> Dict[str, dict]:
    """
    Cria mapa de XMLs: numero_nota -> dados_xml
    """
    mapa = {}

    xmls = list(Path(pasta_notas).glob('*.xml'))
    print(f"\nProcessando {len(xmls)} XMLs da pasta de notas...")

    for xml_path in xmls:
        try:
            dados_xml = extrair_dados_nfe(str(xml_path))

            if not dados_xml['xml_valido']:
                continue

            # Extrair número da nota do arquivo
            numero_nota = extrair_numero_nota_arquivo(str(xml_path))

            if numero_nota and numero_nota != "SEM_NOTA":
                mapa[numero_nota] = dados_xml

        except Exception as e:
            print(f"  [ERRO] Erro ao processar {xml_path.name}: {str(e)}")
            continue

    print(f"  OK Mapa criado com {len(mapa)} entradas (numero_nota -> dados)")
    return mapa

def processar_boletos(pasta_boletos: str, mapa_xmls: Dict[str, dict], pasta_saida: str):
    """
    Processa todos os boletos SQUID usando extrator v2.0
    """
    extrator = SQUIDExtractor()

    boletos = list(Path(pasta_boletos).glob('*.pdf'))
    print(f"\nProcessando {len(boletos)} boletos SQUID...\n")

    Path(pasta_saida).mkdir(parents=True, exist_ok=True)

    sucessos = 0
    erros = 0
    detalhes_erros = []

    for boleto_path in boletos:
        try:
            # Extrair texto do PDF
            with pdfplumber.open(str(boleto_path)) as pdf:
                texto_completo = ""
                for page in pdf.pages:
                    texto_completo += page.extract_text() + "\n"

            # Processar com extrator v2.0
            resultado = extrator.processar_boleto_com_xml(texto_completo, mapa_xmls)

            if resultado['status'] == 'ok':
                # Criar nome do arquivo
                pagador = resultado['pagador']
                vencimento = resultado['vencimento']
                valor = resultado['valor']
                numero_nota = resultado['numero_nota']

                # Limpar nome do pagador
                from unidecode import unidecode
                pagador_limpo = unidecode(pagador)
                pagador_limpo = re.sub(r'[\\/*?:"<>|]', '-', pagador_limpo)
                pagador_limpo = re.sub(r'\s+', ' ', pagador_limpo).strip()

                # Truncar se muito longo
                if len(pagador_limpo) > 60:
                    pagador_limpo = pagador_limpo[:60]

                # Formato: PAGADOR - NF NUMERO - DD-MM - R$ VALOR.pdf
                nome_novo = f"{pagador_limpo} - NF {numero_nota} - {vencimento} - {valor}.pdf"
                caminho_novo = Path(pasta_saida) / nome_novo

                # Copiar arquivo
                import shutil
                shutil.copy2(str(boleto_path), str(caminho_novo))

                print(f"OK {boleto_path.name}")
                print(f"  -> {nome_novo}")
                print(f"  Valor: {valor} ({resultado['origem_valor']})")
                print()

                sucessos += 1
            else:
                erro_msg = resultado.get('erro_msg', 'Erro desconhecido')
                print(f"ERRO {boleto_path.name}")
                print(f"  ERRO: {erro_msg}\n")
                erros += 1
                detalhes_erros.append((boleto_path.name, erro_msg))

        except Exception as e:
            print(f"ERRO {boleto_path.name}")
            print(f"  EXCECAO: {str(e)}\n")
            erros += 1
            detalhes_erros.append((boleto_path.name, f"Exceção: {str(e)}"))

    # Relatório final
    print("\n" + "=" * 70)
    print("RELATORIO FINAL - SQUID v2.0")
    print("=" * 70)
    print(f"Total processado: {len(boletos)}")
    print(f"Sucessos: {sucessos} ({sucessos/len(boletos)*100:.1f}%)")
    print(f"Erros: {erros} ({erros/len(boletos)*100:.1f}%)")

    if detalhes_erros:
        print("\nDETALHES DOS ERROS:")
        for arquivo, erro in detalhes_erros:
            print(f"  - {arquivo}")
            print(f"    {erro}")

    print("=" * 70)

if __name__ == "__main__":
    print("=" * 70)
    print("SCRIPT DE TESTE - SQUID FIDC v2.0")
    print("=" * 70)
    print(f"Notas XML: {PASTA_NOTAS}")
    print(f"Boletos PDF: {PASTA_BOLETOS}")
    print(f"Saida: {PASTA_SAIDA_BASE}")
    print("=" * 70)

    # Criar mapa de XMLs
    mapa_xmls = criar_mapa_xmls(PASTA_NOTAS)

    # Processar boletos
    processar_boletos(PASTA_BOLETOS, mapa_xmls, PASTA_SAIDA_BASE)
