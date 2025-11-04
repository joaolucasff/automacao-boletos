# ===============================================
# Extrator SQUID - Código 100% Isolado
# ===============================================
#
# Este arquivo contém TODA a lógica de extração para boletos SQUID.
# Qualquer mudança aqui NÃO afeta CAPITAL, NOVAX ou CREDVALE.
#
# IMPORTANTE: Este extrator usa regex específico para DANFE SQUID,
# especialmente a seção FATURA que tem formato:
#   FATURA
#   NÚMERO VENCIMENTO VALOR
#   001 DD/MM/YYYY X.XXX,XX
#
# ===============================================

import re
from .base import BaseExtractor

class SQUIDExtractor(BaseExtractor):
    """
    Extrator EXCLUSIVO para boletos SQUID

    Características do boleto SQUID:
    - Usa formato DANFE (Nota Fiscal Eletrônica)
    - Seção FATURA com número, vencimento e valor
    - Campo DESTINATÁRIO/REMETENTE para pagador
    - Suporta fallback para boleto tradicional

    Bugs Corrigidos:
    - Regex FATURA agora captura apenas o valor, sem concatenar dia do vencimento
    - Validação do formato R$ X.XXX,XX
    """

    @property
    def nome_fidc(self) -> str:
        return "SQUID"

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

        # Tentativa 2: Boleto tradicional - Campo "Pagador" exato
        for i, linha in enumerate(linhas):
            if linha.strip() == "Pagador":
                if i + 1 < len(linhas):
                    linha_pagador = linhas[i + 1].strip()
                    # Valida que não é código de barras
                    if not re.match(r'^\d{5}\.\d{5}\s+\d{5}', linha_pagador):
                        pagador = self._limpar_nome(linha_pagador)
                        if pagador:
                            return pagador

        # Tentativa 3: Regex alternativo
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
        Extrai vencimento do boleto SQUID

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
        Extrai valor do boleto SQUID com múltiplos padrões de fallback

        Ordem de prioridade:
        1. Seção FATURA (DANFE) - PRIORIDADE MÁXIMA para SQUID
        2. Campo "Valor Documento" ou "(=) Valor Documento"
        3. Linha com número_doc + data + valor
        4. Vencimento seguido de valor
        5. Qualquer R$ seguido de valor válido
        6. Código de barras (últimas posições)

        Formato esperado: R$ X.XXX,XX (padrão brasileiro)

        Bug Corrigido (03/11/2025):
        - Regex FATURA anterior era muito ganancioso: captava caracteres extras
        - Capturava dia do vencimento junto: 26 + 522,30 = 60.000.522,30
        - Novo regex é específico: formato exato de moeda brasileira
        - Garante validação rigorosa do padrão R$ X.XXX,XX
        """

        # ============================================================
        # PADRÃO 0: FATURA (DANFE - PRIORIDADE MÁXIMA PARA SQUID)
        # ============================================================
        # Formato encontrado em DANFEs SQUID:
        # FATURA
        # NÚMERO VENCIMENTO VALOR
        # 001 26/09/2025 5.223,09
        #
        # Regex explicado:
        # - FATURA.*?[\r\n]+.*?[\r\n]+ → Encontra "FATURA" e pula 2 linhas
        # - \s*\d{3}\s+ → Número da duplicata (001)
        # - \d{2}/\d{2}/\d{4}\s+ → Data de vencimento (26/09/2025)
        # - (\d{1,3}(?:\.\d{3})*,\d{2}) → Valor em formato BR
        #   - \d{1,3} → 1 a 3 dígitos iniciais
        #   - (?:\.\d{3})* → Zero ou mais grupos de ponto + 3 dígitos
        #   - ,\d{2} → Vírgula obrigatória + 2 decimais
        # - (?:\s|$) → Deve terminar com espaço ou fim (evita capturar mais dígitos)

        match_fatura = re.search(
            r'FATURA.*?[\r\n]+.*?[\r\n]+\s*\d{3}\s+\d{2}/\d{2}/\d{4}\s+(\d{1,3}(?:\.\d{3})*,\d{2})(?:\s|$)',
            texto,
            re.IGNORECASE | re.DOTALL
        )
        if match_fatura:
            valor_str = match_fatura.group(1)
            return f"R$ {valor_str}"

        # ============================================================
        # PADRÃO 1: Valor Documento (boletos tradicionais)
        # ============================================================
        padroes_valor_doc = [
            r'\(=\)\s*Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
            r'Valor\s+(?:do\s+)?Documento\s*[:\s]*(?:R\$\s*)?([\d\.\,]+)',
            r'\(=\)\s*Valor\s+do\s+Documento\s+[\d/\s\w]+?\s+([\d\.\,]+)',
        ]

        for padrao in padroes_valor_doc:
            match = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
            if match:
                valor_str = match.group(1)
                # Validar formato brasileiro: X.XXX,XX ou X,XX
                if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                    return f"R$ {valor_str}"

        # ============================================================
        # PADRÃO 2: Linha com estrutura "número_doc data valor"
        # ============================================================
        # Formato: "310926/004 17/02/2026 2.221,20"
        match_linha = re.search(r'\d{6}[/\d]*\s+\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
        if match_linha:
            valor_str = match_linha.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # ============================================================
        # PADRÃO 3: Vencimento seguido de valor
        # ============================================================
        match_venc = re.search(r'\d{2}/\d{2}/\d{4}\s+([\d\.\,]+)', texto)
        if match_venc:
            valor_str = match_venc.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # ============================================================
        # PADRÃO 4: Qualquer R$ seguido de valor válido
        # ============================================================
        match_rs = re.search(r'R\$\s*([\d\.\,]+)', texto)
        if match_rs:
            valor_str = match_rs.group(1)
            if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}', valor_str):
                return f"R$ {valor_str}"

        # ============================================================
        # PADRÃO 5: Código de barras (último recurso)
        # ============================================================
        # Formato: "23790.36706 40000.911947 49000.840501 3 13600000222120"
        #                                                       ^^^^^^^^^^^
        # Posições 3-13 do último grupo (14 dígitos) = valor em centavos
        match_barras = re.search(
            r'\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+(\d{14})',
            texto
        )
        if match_barras:
            codigo_completo = match_barras.group(1)
            # Extrair valor (posições 3-13, 10 dígitos)
            valor_cents_str = codigo_completo[3:13]  # Ex: "0000222120" = R$ 2.221,20
            try:
                valor_cents = int(valor_cents_str)
                if valor_cents > 0:
                    valor_reais = valor_cents / 100
                    # Formatar para padrão brasileiro
                    valor_formatado = f"{valor_reais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    return f"R$ {valor_formatado}"
            except:
                pass

        return "SEM_VALOR"

    # ============================================================
    # Métodos Auxiliares Privados
    # ============================================================

    def _limpar_nome(self, nome: str) -> str:
        """
        Remove CNPJ/CPF e caracteres indesejados do nome do pagador

        Args:
            nome: Nome bruto extraído do PDF

        Returns:
            Nome limpo sem CNPJ/CPF
        """
        # Remove tudo após vírgula, "CNPJ", "CPF", ou "Beneficiario"
        nome = re.split(r',|CNPJ|CPF|Beneficiario', nome, maxsplit=1, flags=re.IGNORECASE)[0].strip()

        # Remove " - " seguido de números (formato CNPJ/CPF)
        nome = re.sub(r'\s*-\s*\d{2,3}[\.\s]*\d{3}[\.\s]*\d{3}[/-]?\d{0,4}[-]?\d{0,2}.*$', '', nome)

        # Remove CNPJ/CPF quando aparece DIRETO após nome (DANFE)
        # Formato: "NOME 83.601.534/0001-09" ou "NOME 123.456.789-01"
        nome = re.sub(r'\s+\d{2,3}[\.\s]?\d{3}[\.\s]?\d{3}[\/\-\s]?\d{2,4}[\-\s]?\d{2}.*$', '', nome)

        return nome.strip()
