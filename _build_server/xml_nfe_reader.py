"""
================================================================================
xml_nfe_reader.py - Leitor de XMLs de Nota Fiscal Eletrônica (NFe)
================================================================================

Módulo responsável por extrair dados de XMLs NFe (padrão brasileiro)
para uso no sistema de envio de boletos.

Funcionalidades:
- Extração de emails do destinatário (máximo 2 válidos)
- Extração de CNPJ, nome, número da nota e valor
- Validação de emails completos (sem truncamento)
- Tratamento robusto de erros e XMLs malformados

Autor: Sistema de Boletos v6.0
Data: 2025-10-30
================================================================================
"""

import xml.etree.ElementTree as ET
import re
import os
from decimal import Decimal, InvalidOperation

# ==================== CONFIGURAÇÕES ====================
# Namespace padrão do NFe (obrigatório para parsing correto)
NFE_NAMESPACE = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe'
}

# Regex para validação de email completo
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# ==================== FUNÇÕES DE VALIDAÇÃO ====================

def validar_email_completo(email: str) -> bool:
    """
    Valida se um email está completo e bem formado.

    Retorna False para:
    - Emails incompletos: "joao@gmail." (sem TLD)
    - Emails truncados: "lucas@gm" (incompleto por limite de caracteres)
    - Emails inválidos: "teste@", "@gmail.com", etc.

    Args:
        email: String do email a validar

    Returns:
        True se email válido e completo, False caso contrário
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()

    # Validação básica de formato
    if not EMAIL_REGEX.match(email):
        return False

    # Verificar se termina com ponto (email incompleto)
    if email.endswith('.'):
        return False

    # Verificar se tem TLD válido (pelo menos 2 caracteres após último ponto)
    partes = email.split('@')
    if len(partes) != 2:
        return False

    dominio = partes[1]
    if '.' not in dominio:
        return False

    tld = dominio.split('.')[-1]
    if len(tld) < 2:
        return False

    return True


def normalizar_cnpj(cnpj_raw: str) -> str:
    """
    Normaliza CNPJ removendo pontuação e retornando apenas dígitos.

    Args:
        cnpj_raw: CNPJ com ou sem formatação

    Returns:
        CNPJ com 14 dígitos ou string vazia se inválido
    """
    if not cnpj_raw:
        return ""

    # Remover tudo que não é dígito
    cnpj_limpo = re.sub(r'\D', '', str(cnpj_raw))

    # CNPJ deve ter exatamente 14 dígitos
    if len(cnpj_limpo) == 14:
        return cnpj_limpo

    return ""


def normalizar_cpf(cpf_raw: str) -> str:
    """
    Normaliza CPF removendo pontuação e retornando apenas dígitos.

    Args:
        cpf_raw: CPF com ou sem formatação

    Returns:
        CPF com 11 dígitos ou string vazia se inválido
    """
    if not cpf_raw:
        return ""

    # Remover tudo que não é dígito
    cpf_limpo = re.sub(r'\D', '', str(cpf_raw))

    # CPF deve ter exatamente 11 dígitos
    if len(cpf_limpo) == 11:
        return cpf_limpo

    return ""


def valor_to_decimal(valor_str: str) -> Decimal:
    """
    Converte string de valor para Decimal.

    Args:
        valor_str: String com valor (ex: "8500.00")

    Returns:
        Decimal com o valor ou Decimal(0) se inválido
    """
    if not valor_str:
        return Decimal(0)

    try:
        return Decimal(str(valor_str))
    except InvalidOperation:
        return Decimal(0)


# ==================== FUNÇÃO PRINCIPAL ====================

def extrair_dados_nfe(caminho_xml: str, max_emails: int = 2) -> dict:
    """
    Extrai todos os dados relevantes de um XML NFe para envio de boletos.

    Esta é a função principal do módulo. Ela faz o parsing completo do XML
    e retorna um dicionário com todos os dados necessários para validação
    e envio de emails.

    Args:
        caminho_xml: Caminho completo para o arquivo XML
        max_emails: Número máximo de emails a retornar (padrão: 2)

    Returns:
        Dicionário com estrutura:
        {
            'xml_valido': bool,           # Se conseguiu ler o XML
            'xml_path': str,              # Caminho do XML
            'emails': list,               # Lista com até max_emails emails válidos
            'emails_invalidos': list,     # Emails filtrados (incompletos/inválidos)
            'cnpj': str,                  # CNPJ normalizado (14 dígitos)
            'nome': str,                  # Razão social do destinatário
            'numero_nota': str,           # Número da nota fiscal
            'valor_total': Decimal,       # Valor total da nota
            'erro': str|None              # Mensagem de erro se houver
        }

    Exemplo de uso:
        >>> dados = extrair_dados_nfe('3-0310227.xml')
        >>> if dados['xml_valido']:
        >>>     print(f"Emails: {dados['emails']}")
        >>>     print(f"CNPJ: {dados['cnpj']}")
    """

    # Estrutura padrão de retorno (assume falha até provar sucesso)
    resultado = {
        'xml_valido': False,
        'xml_path': caminho_xml,
        'emails': [],
        'emails_invalidos': [],
        'cnpj': '',          # CNPJ (14 dígitos) ou vazio
        'cpf': '',           # CPF (11 dígitos) ou vazio
        'cpf_cnpj': '',      # Unificado: CPF ou CNPJ (11 ou 14 dígitos)
        'nome': '',
        'numero_nota': '',
        'valor_total': Decimal(0),
        'duplicatas': [],  # Lista de duplicatas (parcelas)
        'erro': None
    }

    # Validação básica
    if not os.path.exists(caminho_xml):
        resultado['erro'] = f"Arquivo não encontrado: {caminho_xml}"
        return resultado

    try:
        # Parse do XML
        tree = ET.parse(caminho_xml)
        root = tree.getroot()

        # ===== EXTRAÇÃO DE DADOS =====

        # 1. Número da Nota (tag: <nNF>)
        nNF_elem = root.find('.//nfe:nNF', NFE_NAMESPACE)
        if nNF_elem is not None and nNF_elem.text:
            resultado['numero_nota'] = nNF_elem.text.strip()

        # 2. Valor Total da Nota (tag: <vNF>)
        vNF_elem = root.find('.//nfe:vNF', NFE_NAMESPACE)
        if vNF_elem is not None and vNF_elem.text:
            resultado['valor_total'] = valor_to_decimal(vNF_elem.text)

        # 3. Dados do Destinatário (seção <dest>)
        dest = root.find('.//nfe:dest', NFE_NAMESPACE)

        if dest is not None:
            # 3a. CNPJ do destinatário (14 dígitos)
            cnpj_elem = dest.find('nfe:CNPJ', NFE_NAMESPACE)
            if cnpj_elem is not None and cnpj_elem.text:
                resultado['cnpj'] = normalizar_cnpj(cnpj_elem.text)
                resultado['cpf_cnpj'] = resultado['cnpj']

            # 3b. CPF do destinatário (11 dígitos) - para pessoa física
            if not resultado['cpf_cnpj']:  # Só tentar CPF se não achou CNPJ
                cpf_elem = dest.find('nfe:CPF', NFE_NAMESPACE)
                if cpf_elem is not None and cpf_elem.text:
                    resultado['cpf'] = normalizar_cpf(cpf_elem.text)
                    resultado['cpf_cnpj'] = resultado['cpf']

            # 3c. Nome/Razão Social do destinatário
            nome_elem = dest.find('nfe:xNome', NFE_NAMESPACE)
            if nome_elem is not None and nome_elem.text:
                resultado['nome'] = nome_elem.text.strip()

            # 3c. Emails do destinatário (CAMPO MAIS IMPORTANTE!)
            email_elem = dest.find('nfe:email', NFE_NAMESPACE)
            if email_elem is not None and email_elem.text:
                # Emails podem vir separados por ; ou ,
                email_text = email_elem.text.strip()

                # Separar por ; ou ,
                separadores = [';', ',']
                emails_raw = [email_text]

                for sep in separadores:
                    emails_temp = []
                    for e in emails_raw:
                        emails_temp.extend(e.split(sep))
                    emails_raw = emails_temp

                # Limpar e validar cada email
                for email_raw in emails_raw:
                    email = email_raw.strip()

                    if not email:
                        continue

                    # Validar se email está completo
                    if validar_email_completo(email):
                        # Adicionar apenas se ainda não atingiu o limite
                        if len(resultado['emails']) < max_emails:
                            resultado['emails'].append(email)
                    else:
                        # Email inválido ou incompleto
                        resultado['emails_invalidos'].append(email)

        # 4. Duplicatas (parcelas do boleto)
        for dup_elem in root.findall('.//nfe:dup', NFE_NAMESPACE):
            num_dup = dup_elem.find('nfe:nDup', NFE_NAMESPACE)
            venc_dup = dup_elem.find('nfe:dVenc', NFE_NAMESPACE)
            valor_dup = dup_elem.find('nfe:vDup', NFE_NAMESPACE)

            if num_dup is not None and venc_dup is not None and valor_dup is not None:
                duplicata = {
                    'numero': num_dup.text.strip(),
                    'vencimento': venc_dup.text.strip(),  # Formato: YYYY-MM-DD
                    'valor': valor_to_decimal(valor_dup.text)
                }
                resultado['duplicatas'].append(duplicata)

        # Validação final: XML é considerado válido se tem pelo menos nome e nota
        if resultado['nome'] and resultado['numero_nota']:
            resultado['xml_valido'] = True
        else:
            resultado['erro'] = "XML não contém dados mínimos necessários (nome e número da nota)"

    except ET.ParseError as e:
        resultado['erro'] = f"XML malformado: {str(e)}"
    except Exception as e:
        resultado['erro'] = f"Erro ao processar XML: {str(e)}"

    return resultado


# ==================== FUNÇÃO DE INDEXAÇÃO ====================

def indexar_xmls_por_nota(pasta_notas: str, max_emails: int = 2) -> dict:
    """
    Indexa todos os XMLs de uma pasta por número de nota.

    Cria um mapa de fácil acesso onde a chave é o número da nota
    (últimos 6 dígitos) e o valor são os dados extraídos do XML.

    Args:
        pasta_notas: Caminho da pasta contendo os XMLs
        max_emails: Número máximo de emails por cliente

    Returns:
        Dicionário {numero_nota: dados_xml}

    Exemplo:
        >>> mapa = indexar_xmls_por_nota('Notas')
        >>> dados = mapa.get('310227')
        >>> if dados and dados['xml_valido']:
        >>>     print(f"Email: {dados['emails'][0]}")
    """

    mapa = {}
    xmls_processados = 0
    xmls_validos = 0
    xmls_invalidos = 0

    if not os.path.exists(pasta_notas):
        print(f"[ERRO] Pasta de notas não encontrada: {pasta_notas}")
        return mapa

    # Listar todos os XMLs
    arquivos_xml = [f for f in os.listdir(pasta_notas) if f.lower().endswith('.xml')]

    print(f"[XML] Indexando XMLs da pasta: {pasta_notas}")
    print(f"[XML] Total de XMLs encontrados: {len(arquivos_xml)}")

    for arquivo_xml in arquivos_xml:
        caminho_completo = os.path.join(pasta_notas, arquivo_xml)

        # Extrair dados do XML
        dados = extrair_dados_nfe(caminho_completo, max_emails)
        xmls_processados += 1

        if dados['xml_valido']:
            # Usar número da nota como chave
            numero_nota = dados['numero_nota']

            # Também criar entrada com últimos 6 dígitos (para compatibilidade)
            if len(numero_nota) >= 6:
                chave_curta = numero_nota[-6:]
                mapa[chave_curta] = dados

            # E a chave completa
            mapa[numero_nota] = dados
            xmls_validos += 1
        else:
            xmls_invalidos += 1
            print(f"[AVISO] XML inválido: {arquivo_xml} - Erro: {dados.get('erro', 'Desconhecido')}")

    print(f"[XML] Indexação concluída:")
    print(f"      - XMLs processados: {xmls_processados}")
    print(f"      - XMLs válidos: {xmls_validos}")
    print(f"      - XMLs inválidos: {xmls_invalidos}")
    print()

    return mapa


# ==================== TESTES ====================

if __name__ == "__main__":
    """
    Testes básicos do módulo
    """
    print("=" * 80)
    print("TESTE DO MÓDULO xml_nfe_reader.py")
    print("=" * 80)
    print()

    # Teste 1: Validação de emails
    print("TESTE 1: Validação de Emails")
    print("-" * 80)
    emails_teste = [
        "joao@gmail.com",           # Válido
        "maria@empresa.com.br",     # Válido
        "lucas@gmail.",             # Inválido (sem TLD)
        "teste@",                   # Inválido (sem domínio)
        "@gmail.com",               # Inválido (sem usuário)
        "pedro@site.c",             # Inválido (TLD muito curto)
        "ana@teste.com.br.gov",     # Válido (múltiplos níveis)
    ]

    for email in emails_teste:
        valido = validar_email_completo(email)
        status = "[OK] VALIDO" if valido else "[X] INVALIDO"
        print(f"  {status:15} | {email}")

    print()

    # Teste 2: Normalização de CNPJ
    print("TESTE 2: Normalização de CNPJ")
    print("-" * 80)
    cnpjs_teste = [
        "12.345.678/0001-90",
        "12345678000190",
        "12.345.678",               # Inválido (poucos dígitos)
        "19622616000122",
    ]

    for cnpj in cnpjs_teste:
        normalizado = normalizar_cnpj(cnpj)
        if normalizado:
            print(f"  [OK] {cnpj:20} >> {normalizado}")
        else:
            print(f"  [X]  {cnpj:20} >> INVALIDO")

    print()

    # Teste 3: Leitura de XML (se existir)
    print("TESTE 3: Leitura de XML de Exemplo")
    print("-" * 80)

    xml_exemplo = r"C:\Users\User-OEM\Desktop\BoletosAutomação\Notas\3-0310227.xml"

    if os.path.exists(xml_exemplo):
        dados = extrair_dados_nfe(xml_exemplo)

        print(f"  XML Válido: {dados['xml_valido']}")
        print(f"  Número Nota: {dados['numero_nota']}")
        print(f"  CNPJ: {dados['cnpj']}")
        print(f"  Nome: {dados['nome']}")
        print(f"  Valor Total: R$ {dados['valor_total']}")
        print(f"  Emails Válidos ({len(dados['emails'])}):")
        for email in dados['emails']:
            print(f"    - {email}")

        if dados['emails_invalidos']:
            print(f"  Emails Inválidos ({len(dados['emails_invalidos'])}):")
            for email in dados['emails_invalidos']:
                print(f"    - {email}")

        if dados['erro']:
            print(f"  Erro: {dados['erro']}")
    else:
        print(f"  [SKIP] Arquivo de exemplo não encontrado: {xml_exemplo}")

    print()
    print("=" * 80)
    print("FIM DOS TESTES")
    print("=" * 80)
