# ===============================================
# Extrator SQUID - Código 100% Isolado (v2.0)
# ===============================================
#
# Este arquivo contém TODA a lógica de extração para boletos SQUID.
# Qualquer mudança aqui NÃO afeta CAPITAL, NOVAX ou CREDVALE.
#
# VERSÃO 2.0 - Atualizado em 2025-11-04
# - Suporte a CPF/CNPJ (campo unificado cpf_cnpj)
# - Match por CNPJ+vencimento para boletos sem número NF no filename
# - Validação de emails (máximo 2 válidos)
# - Escolha inteligente de valor (duplicata vs total)
#
# IMPORTANTE: Este extrator usa regex específico para DANFE SQUID,
# especialmente a seção FATURA que tem formato:
#   FATURA
#   NÚMERO VENCIMENTO VALOR
#   001 DD/MM/YYYY X.XXX,XX
#
# ===============================================

import re
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from .base import BaseExtractor


class SQUIDExtractor(BaseExtractor):
    """
    Extrator EXCLUSIVO para boletos SQUID FIDC (v2.0)

    Características do boleto SQUID:
    - Usa formato DANFE (Nota Fiscal Eletrônica)
    - Seção FATURA com número, vencimento e valor
    - Campo DESTINATÁRIO/REMETENTE para pagador
    - Suporta fallback para boleto tradicional
    """

    @property
    def nome_fidc(self) -> str:
        return "SQUID"

    # ========================================================================
    # MÉTODOS ORIGINAIS (compatibilidade com BaseExtractor)
    # ========================================================================

    def extrair_pagador(self, texto: str) -> str:
        """
        Extrai pagador do boleto SQUID

        Ordem de tentativa:
        1. DANFE: Campo DESTINATÁRIO/REMETENTE
        2. Boleto tradicional: Campo Pagador
        3. Regex alternativo: "Pagador" seguido de nome
        """
        linhas = texto.splitlines()

        # Tentativa 1: DANFE - Campo DESTINATÁRIO/REMETENTE
        for i, linha in enumerate(linhas):
            if "DESTINAT" in linha.upper() and "REMETENTE" in linha.upper():
                # Próxima linha: "NOME/RAZÃO SOCIAL"
                # Linha seguinte: nome do destinatário
                if i + 2 < len(linhas):
                    linha_nome = linhas[i + 2].strip()
                    # Validar que não é cabeçalho
                    if "CNPJ" not in linha_nome and "CPF" not in linha_nome:
                        pagador = self._limpar_nome(linha_nome)
                        if pagador and pagador != "SEM_PAGADOR":
                            return pagador

        # Tentativa 2: Boleto tradicional - Campo "Pagador"
        for i, linha in enumerate(linhas):
            if "PAGADOR" in linha.upper():
                if i + 1 < len(linhas):
                    pagador = linhas[i + 1].strip()
                    pagador = self._limpar_nome(pagador)
                    if pagador:
                        return pagador

        # Tentativa 3: Regex alternativo
        compacto = re.sub(r'\s+', ' ', texto).strip()
        match = re.search(
            r'Pagador:\s*([A-Z0-9][A-Z0-9\s\.\-&]+?)(?:\s+CNPJ[/\s]|\s+CPF)',
            compacto,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        return "SEM_PAGADOR"

    def extrair_numero_nota(self, texto: str) -> Optional[str]:
        """
        Extrai número da nota fiscal do boleto SQUID

        Padrão DANFE: "NÚMERO DA NOTA ... 305537" ou "Número do Documento ... 305537/001"
        Retorna apenas o número da nota (sem a parte "/XXX")
        """
        linhas = texto.splitlines()

        # Tentativa 1: DANFE - "NÚMERO DA NOTA"
        for i, linha in enumerate(linhas):
            if 'MERO DA NOTA' in linha.upper():
                # Verificar próximas 3 linhas
                for j in range(i, min(i + 4, len(linhas))):
                    linha_check = linhas[j]
                    # Padrão: 305537 ou 0305537
                    match = re.search(r'0?(\d{6})', linha_check)
                    if match:
                        return match.group(1)

        # Tentativa 2: "Número do Documento" (formato boleto tradicional)
        for i, linha in enumerate(linhas):
            if 'MERO DO DOCUMENTO' in linha.upper():
                # Verificar próximas 3 linhas
                for j in range(i, min(i + 4, len(linhas))):
                    linha_check = linhas[j]
                    # Padrão: 305537/001 ou 0305537/001
                    match = re.search(r'0?(\d{6})(?:/\d{3})?', linha_check)
                    if match:
                        return match.group(1)

        return None

    def extrair_vencimento(self, texto: str) -> str:
        """
        Extrai vencimento do boleto SQUID

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

        return "SEM_VENCIMENTO"

    def extrair_valor(self, texto: str) -> str:
        """
        Extrai valor do boleto SQUID com múltiplos padrões de fallback

        Ordem de prioridade:
        1. Seção FATURA (DANFE SQUID)
        2. Campo "Valor Documento"
        3. Linha com número_doc + data + valor
        4. Vencimento seguido de valor
        5. Qualquer R$ seguido de valor válido
        6. Código de barras

        BUGS CORRIGIDOS v2.0:
        - Regex FATURA agora captura apenas o valor, sem concatenar dia do vencimento
        - Validação do formato R$ X.XXX,XX
        """

        # PADRÃO 0: FATURA (DANFE SQUID)
        match_fatura = re.search(
            r'FATURA.*?[\r\n]+.*?[\r\n]+\s*\d{3}\s+\d{2}/\d{2}/\d{4}\s+(\d{1,3}(?:\.\d{3})*,\d{2})(?:\s|$)',
            texto,
            re.IGNORECASE | re.DOTALL
        )
        if match_fatura:
            valor_str = match_fatura.group(1)
            return f"R$ {valor_str}"

        # PADRÃO 1: Valor Documento
        padroes_valor_doc = [
            r'\(=\)\s*Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
            r'Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
        ]

        for padrao in padroes_valor_doc:
            match = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                valor_str = match.group(1)
                if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                    return f"R$ {valor_str}"

        # PADRÃO 2: Linha com estrutura "número_doc data valor"
        match_linha = re.search(r'\d{6}[/\d]*\s+\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
        if match_linha:
            valor_str = match_linha.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # PADRÃO 3: Vencimento seguido de valor
        match_venc = re.search(r'\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
        if match_venc:
            valor_str = match_venc.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # PADRÃO 4: Qualquer R$ seguido de valor válido
        match_rs = re.search(r'R\$\s*([\d\.\,]+)', texto)
        if match_rs:
            valor_str = match_rs.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # PADRÃO 5: Código de barras
        match_barras = re.search(
            r'\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+(\d{14})',
            texto
        )
        if match_barras:
            codigo_completo = match_barras.group(1)
            valor_cents_str = codigo_completo[3:13]
            try:
                valor_cents = int(valor_cents_str)
                if valor_cents > 0:
                    valor_reais = valor_cents / 100
                    valor_formatado = f"{valor_reais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    return f"R$ {valor_formatado}"
            except:
                pass

        return "SEM_VALOR"

    # ========================================================================
    # MÉTODO ESPECÍFICO SQUID
    # ========================================================================

    @staticmethod
    def extrair_numero_nf_do_filename(filename: str) -> str:
        """
        Extrai número da NF do nome do arquivo SQUID

        Exemplos:
            "3-0305537.pdf" → "305537"
            "3-305537.xml" → "305537"
        """
        import os
        nome_arquivo = os.path.basename(filename)

        # Padrão 1: "3-0305537.pdf" → "305537"
        match = re.search(r'\d+-0?(\d{6})\.', nome_arquivo)
        if match:
            return match.group(1)

        # Padrão 2: "305537.pdf"
        match = re.search(r'^0?(\d{6})\.', nome_arquivo)
        if match:
            return match.group(1)

        return "SEM_NOTA"

    # ========================================================================
    # NOVOS MÉTODOS v2.0 - LÓGICA AVANÇADA COM XML
    # ========================================================================

    def extrair_cnpj_cpf_boleto(self, texto: str) -> Optional[str]:
        """
        Extrai CNPJ/CPF do DESTINATÁRIO no boleto SQUID

        Busca após seção "DESTINATÁRIO/REMETENTE"
        Retorna apenas dígitos (14 para CNPJ, 11 para CPF)
        """
        linhas = texto.splitlines()

        # Buscar após DESTINATÁRIO/REMETENTE
        for i, linha in enumerate(linhas):
            if "DESTINAT" in linha.upper() and "REMETENTE" in linha.upper():
                # Próximas 3-4 linhas podem conter o CNPJ/CPF
                for j in range(i + 1, min(i + 5, len(linhas))):
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

        # Fallback: buscar após "Pagador"
        for i, linha in enumerate(linhas):
            if "PAGADOR" in linha.upper():
                for j in range(i + 1, min(i + 3, len(linhas))):
                    linha_busca = linhas[j]

                    # CPF
                    match_cpf = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', linha_busca)
                    if match_cpf:
                        return re.sub(r'[.-]', '', match_cpf.group(1))

                    # CNPJ
                    match_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', linha_busca)
                    if match_cnpj:
                        return re.sub(r'[./-]', '', match_cnpj.group(1))

        return None

    def validar_email(self, email: str) -> bool:
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

    def extrair_emails_validos(self, emails_xml: List[str], max_emails: int = 2) -> List[str]:
        """
        Extrai emails válidos do XML (máximo 2)

        Ignora emails cortados/incompletos
        """
        emails_validos = []

        for email in emails_xml[:5]:  # Checar até 5 emails
            if self.validar_email(email):
                emails_validos.append(email)
                if len(emails_validos) >= max_emails:
                    break

        return emails_validos

    def escolher_valor_correto(self, dados_xml: dict, vencimento_boleto: str) -> Tuple[str, str]:
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

    def buscar_xml_por_cnpj_e_vencimento(
        self,
        cnpj_boleto: str,
        vencimento_boleto: str,
        mapa_xmls: Dict[str, dict]
    ) -> Tuple[Optional[str], Optional[dict], Optional[dict]]:
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

    # ========================================================================
    # MÉTODO DE PROCESSAMENTO COMPLETO
    # ========================================================================

    def processar_boleto_com_xml(
        self,
        texto_pdf: str,
        mapa_xmls: Dict[str, dict]
    ) -> dict:
        """
        Processa um boleto SQUID usando XML como fonte principal

        Match por CNPJ/CPF + vencimento

        Returns:
            {
                'status': 'ok' | 'erro',
                'pagador': str,
                'vencimento': str,
                'valor': str,
                'numero_nota': str,
                'emails': [email1, email2],
                'origem_valor': str,
                'erro_msg': str
            }
        """
        resultado = {
            'status': 'erro',
            'pagador': 'SEM_PAGADOR',
            'vencimento': 'SEM_VENCIMENTO',
            'valor': 'SEM_VALOR',
            'numero_nota': 'SEM_NOTA',
            'emails': [],
            'origem_valor': '',
            'erro_msg': ''
        }

        try:
            # 1. Extrair dados do boleto
            cnpj_boleto = self.extrair_cnpj_cpf_boleto(texto_pdf)
            vencimento_boleto = self.extrair_vencimento(texto_pdf)
            numero_nota_boleto = self.extrair_numero_nota(texto_pdf)

            if not cnpj_boleto:
                resultado['erro_msg'] = "Não foi possível extrair CNPJ/CPF do boleto"
                return resultado

            if not vencimento_boleto or vencimento_boleto == "SEM_VENCIMENTO":
                resultado['erro_msg'] = "Não foi possível extrair vencimento do boleto"
                return resultado

            # 2. Buscar XML - priorizar match direto por número da nota
            numero_nota = None
            dados_xml = None
            duplicata_matched = None

            # Tentativa 1: Match direto por número da nota (mais preciso)
            if numero_nota_boleto and numero_nota_boleto in mapa_xmls:
                numero_nota = numero_nota_boleto
                dados_xml = mapa_xmls[numero_nota]

            # Tentativa 2: Se não encontrou, buscar por CNPJ + vencimento (fallback)
            if not dados_xml:
                numero_nota, dados_xml, duplicata_matched = self.buscar_xml_por_cnpj_e_vencimento(
                    cnpj_boleto, vencimento_boleto, mapa_xmls
                )

            if not numero_nota or not dados_xml:
                resultado['erro_msg'] = f"XML não encontrado para nota={numero_nota_boleto or 'N/A'}, CNPJ={cnpj_boleto}, vencimento={vencimento_boleto}"
                return resultado

            # 3. Usar dados do XML
            pagador = dados_xml.get('nome', 'SEM_PAGADOR')
            valor, origem_valor = self.escolher_valor_correto(dados_xml, vencimento_boleto)

            # 4. Extrair emails válidos
            emails_xml = dados_xml.get('emails', [])
            emails_validos = self.extrair_emails_validos(emails_xml, max_emails=2)

            # 5. Montar resultado
            resultado['status'] = 'ok'
            resultado['pagador'] = pagador
            resultado['vencimento'] = vencimento_boleto
            resultado['valor'] = valor
            resultado['numero_nota'] = numero_nota
            resultado['emails'] = emails_validos
            resultado['origem_valor'] = origem_valor

            return resultado

        except Exception as e:
            resultado['erro_msg'] = f"Exceção: {type(e).__name__}: {str(e)}"
            return resultado

    # ========================================================================
    # MÉTODO AUXILIAR
    # ========================================================================

    def _limpar_nome(self, nome: str) -> str:
        """Remove CNPJ/CPF e caracteres indesejados do nome do pagador"""
        nome = re.split(r',|CNPJ|CPF|Beneficiario', nome, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        nome = re.sub(r'\s*-\s*\d{2,3}[\.\s]*\d{3}[\.\s]*\d{3}[/-]?\d{0,4}[-]?\d{0,2}.*$', '', nome)
        nome = re.sub(r'\s+\d{2,3}[\.\s]?\d{3}[\.\s]?\d{3}[\/\-\s]?\d{2,4}[\-\s]?\d{2}.*$', '', nome)
        return nome.strip()
