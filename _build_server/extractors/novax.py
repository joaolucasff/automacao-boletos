# ===============================================
# Extrator NOVAX - Código 100% Isolado
# ===============================================
#
# Este arquivo contém TODA a lógica de extração para boletos NOVAX.
# Qualquer mudança aqui NÃO afeta SQUID, CAPITAL ou CREDVALE.
#
# NOVAX tem formato de boleto tradicional (não DANFE)
#
# ===============================================

import re
from .base import BaseExtractor

class NOVAXExtractor(BaseExtractor):
    """
    Extrator EXCLUSIVO para boletos NOVAX FIDC

    Características do boleto NOVAX:
    - Formato de boleto tradicional (não é DANFE)
    - Campo "Pagador:" seguido do nome
    - Vencimento no cabeçalho
    - Usa padrões específicos de regex
    """

    @property
    def nome_fidc(self) -> str:
        return "NOVAX"

    def extrair_pagador(self, texto: str) -> str:
        """
        Extrai pagador do boleto NOVAX

        NOVAX usa formato "Pagador: NOME - CNPJ/CPF"
        Regex busca especificamente "Pagador:" seguido do nome até CNPJ/CPF
        """
        # Texto compacto facilita regex em "mesma linha"
        compacto = re.sub(r'\s+', ' ', texto).strip()

        # Busca "Pagador:" seguido do nome até CNPJ/CPF
        # Aceita variações: CNPJ, CPF, CNPJ/, CNPJ/ CPF
        match = re.search(
            r'Pagador:\s*([A-Z0-9][A-Z0-9\s\.\-&]+?)(?:\s+CNPJ[/\s]|\s+CPF)',
            compacto,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        return "SEM_PAGADOR"

    def extrair_vencimento(self, texto: str) -> str:
        """
        Extrai vencimento do boleto NOVAX

        NOVAX tem vencimento no cabeçalho, próximo à palavra "Vencimento"
        """
        # Texto compacto para buscar na mesma linha
        compacto = re.sub(r'\s+', ' ', texto).strip()

        # Busca "Vencimento" seguido de data
        match = re.search(r'Vencimento\s+(\d{2}/\d{2}/\d{4})', compacto, re.IGNORECASE)
        if match:
            vencimento = match.group(1)
            # Retorna apenas DD-MM
            return vencimento[:5].replace("/", "-")

        return "SEM_VENCIMENTO"

    def extrair_valor(self, texto: str) -> str:
        """
        Extrai valor do boleto NOVAX

        NOVAX usa boleto tradicional, então priorizamos:
        1. Campo "Valor Documento"
        2. Código de barras
        3. Fallbacks gerais
        """

        # PADRÃO 1: Valor Documento (mais comum em NOVAX)
        padroes_valor_doc = [
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
