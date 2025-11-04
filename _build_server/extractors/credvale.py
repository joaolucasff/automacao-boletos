# ===============================================
# Extrator CREDVALE - Código 100% Isolado
# ===============================================
#
# Este arquivo contém TODA a lógica de extração para boletos CREDVALE.
# Qualquer mudança aqui NÃO afeta SQUID, CAPITAL ou NOVAX.
#
# CREDVALE tem formato de boleto tradicional
#
# ===============================================

import re
from .base import BaseExtractor

class CREDVALEExtractor(BaseExtractor):
    """
    Extrator EXCLUSIVO para boletos CREDVALE FIDC

    Características do boleto CREDVALE:
    - Formato de boleto tradicional
    - Campo "Pagador" em linha separada
    - Padrão similar ao NOVAX, mas pode ter variações
    """

    @property
    def nome_fidc(self) -> str:
        return "CREDVALE"

    def extrair_pagador(self, texto: str) -> str:
        """
        Extrai pagador do boleto CREDVALE

        Busca linha "Pagador" exata e pega próxima linha
        """
        linhas = texto.splitlines()

        # Tentativa 1: Linha "Pagador" exata
        for i, linha in enumerate(linhas):
            if linha.strip() == "Pagador":
                if i + 1 < len(linhas):
                    linha_pagador = linhas[i + 1].strip()
                    # Valida que não é código de barras
                    if not re.match(r'^\d{5}\.\d{5}\s+\d{5}', linha_pagador):
                        pagador = self._limpar_nome(linha_pagador)
                        if pagador:
                            return pagador

        # Tentativa 2: Regex alternativo
        match = re.search(
            r'Pagador\s*\n\s*([A-ZÀ-Ú][A-ZÀ-Ú\s\.\-&]+?)\s*-\s*(?:CNPJ|CPF)',
            texto,
            re.IGNORECASE | re.MULTILINE
        )
        if match:
            return match.group(1).strip()

        return "SEM_PAGADOR"

    def extrair_vencimento(self, texto: str) -> str:
        """
        Extrai vencimento do boleto CREDVALE

        Busca "Vencimento" e captura data DD/MM/YYYY
        """
        linhas = texto.splitlines()

        for i, linha in enumerate(linhas):
            if "Vencimento" in linha:
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
        Extrai valor do boleto CREDVALE

        CREDVALE tem um padrão específico de "(=) Valor do Documento"
        seguido de data e então valor
        """

        # PADRÃO 1: Valor Documento (padrão CREDVALE específico)
        padroes_valor_doc = [
            r'\(=\)\s*Valor\s+do\s+Documento\s+[\d/\s\w]+?\s+([\d\.\,]+)',  # CREDVALE específico
            r'\(=\)\s*Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
            r'Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
        ]

        for padrao in padroes_valor_doc:
            match = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                valor_str = match.group(1)
                # Validar formato brasileiro
                if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                    return f"R$ {valor_str}"

        # PADRÃO 2: Linha com número_doc + data + valor
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

        # PADRÃO 5: Código de barras (último recurso)
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
