# ===============================================
# Extrator CAPITAL - Código 100% Isolado
# ===============================================
#
# Este arquivo contém TODA a lógica de extração para boletos CAPITAL RS.
# Qualquer mudança aqui NÃO afeta SQUID, NOVAX ou CREDVALE.
#
# CAPITAL RS também usa formato DANFE (similar ao SQUID, mas isolado)
#
# ===============================================

import re
from .base import BaseExtractor

class CAPITALExtractor(BaseExtractor):
    """
    Extrator EXCLUSIVO para boletos CAPITAL RS FIDC

    Características do boleto CAPITAL:
    - Usa formato DANFE (Nota Fiscal Eletrônica)
    - Campo DESTINATÁRIO/REMETENTE para pagador
    - Seção FATURA (similar ao SQUID, mas pode ter variações)
    - Suporta boleto tradicional como fallback
    """

    @property
    def nome_fidc(self) -> str:
        return "CAPITAL"

    def extrair_pagador(self, texto: str) -> str:
        """
        Extrai pagador do boleto CAPITAL

        Ordem de tentativa:
        1. DANFE: Campo DESTINATÁRIO/REMETENTE
        2. Boleto tradicional: Campo Pagador
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

        return "SEM_PAGADOR"

    def extrair_vencimento(self, texto: str) -> str:
        """
        Extrai vencimento do boleto CAPITAL

        Busca padrão DD/MM/YYYY e retorna DD-MM
        """
        linhas = texto.splitlines()

        for i, linha in enumerate(linhas):
            if "VENCIMENTO" in linha.upper():
                # Tentar na mesma linha
                match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                if not match and i + 1 < len(linhas):
                    # Tentar na próxima linha
                    match = re.search(r'(\d{2}/\d{2}/\d{4})', linhas[i + 1])

                if match:
                    vencimento = match.group(1)
                    # Retorna apenas DD-MM
                    return vencimento[:5].replace("/", "-")

        return "SEM_VENCIMENTO"

    def extrair_valor(self, texto: str) -> str:
        """
        Extrai valor do boleto CAPITAL com múltiplos padrões de fallback

        Ordem de prioridade:
        1. Seção FATURA (DANFE)
        2. Campo "Valor Documento"
        3. Linha com número_doc + data + valor
        4. Vencimento seguido de valor
        5. Qualquer R$ seguido de valor válido
        6. Código de barras

        NOTA: Código similar ao SQUID, mas ISOLADO.
        Mudanças aqui NÃO afetam extrator SQUID.
        """

        # PADRÃO 0: FATURA (DANFE CAPITAL)
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

    def _limpar_nome(self, nome: str) -> str:
        """Remove CNPJ/CPF e caracteres indesejados do nome do pagador"""
        nome = re.split(r',|CNPJ|CPF|Beneficiario', nome, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        nome = re.sub(r'\s*-\s*\d{2,3}[\.\s]*\d{3}[\.\s]*\d{3}[/-]?\d{0,4}[-]?\d{0,2}.*$', '', nome)
        nome = re.sub(r'\s+\d{2,3}[\.\s]?\d{3}[\.\s]?\d{3}[\/\-\s]?\d{2,4}[\-\s]?\d{2}.*$', '', nome)
        return nome.strip()
