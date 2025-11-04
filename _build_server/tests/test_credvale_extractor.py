"""
Testes para o Extrator CREDVALE

Este arquivo contém testes isolados para o extrator CREDVALE FIDC.
CREDVALE usa formato de boleto tradicional.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors import CREDVALEExtractor


class TestCREDVALEExtractor:
    """Suite de testes para o extrator CREDVALE"""

    @pytest.fixture
    def extractor(self):
        """Fixture que retorna instância do extrator CREDVALE"""
        return CREDVALEExtractor()

    @pytest.fixture
    def texto_boleto_credvale(self):
        """Fixture com texto de boleto CREDVALE básico"""
        return """
        CREDVALE FUNDO DE INVESTIMENTO

        Vencimento
        20/07/2025

        Pagador
        EMPRESA CREDVALE TESTE LTDA - CNPJ: 98.765.432/0001-10

        (=) Valor do Documento  R$ 3.750,00
        """

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VALOR
    # ================================================================

    def test_extrair_valor_documento_padrao(self, extractor):
        """Teste: extração de valor do campo Valor Documento (padrão CREDVALE)"""
        texto = """
        (=) Valor do Documento  R$ 3.750,00
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 3.750,00"

    def test_extrair_valor_documento_com_data(self, extractor):
        """
        Teste: CREDVALE pode ter formato especial com data antes do valor

        Exemplo: "(=) Valor do Documento 15/07/2025 1.234,56"
        """
        texto = """
        (=) Valor do Documento 15/07/2025 1.234,56
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 1.234,56"

    def test_extrair_valor_com_milhares(self, extractor):
        """Teste: valor com separador de milhares"""
        texto = """
        (=) Valor do Documento  R$ 45.600,78
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 45.600,78"

    def test_extrair_valor_pequeno(self, extractor):
        """Teste: valor pequeno sem milhares"""
        texto = """
        (=) Valor do Documento  R$ 99,50
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 99,50"

    # ================================================================
    # TESTES DE EXTRAÇÃO DE PAGADOR
    # ================================================================

    def test_extrair_pagador_formato_padrao(self, extractor, texto_boleto_credvale):
        """Teste: extração de pagador no formato padrão CREDVALE"""
        pagador = extractor.extrair_pagador(texto_boleto_credvale)

        assert "EMPRESA CREDVALE TESTE LTDA" in pagador
        assert "CNPJ" not in pagador
        assert "98.765.432" not in pagador

    def test_extrair_pagador_linha_exata(self, extractor):
        """
        Teste: pagador em linha isolada (palavra "Pagador" sozinha)

        CREDVALE usa formato:
        Pagador
        NOME DO CLIENTE
        """
        texto = """
        Pagador
        CLIENTE EXEMPLO LTDA
        """

        pagador = extractor.extrair_pagador(texto)
        assert "CLIENTE EXEMPLO LTDA" in pagador

    def test_extrair_pagador_com_hifen_cnpj(self, extractor):
        """Teste: pagador com hífen antes do CNPJ"""
        texto = """
        Pagador
        EMPRESA XYZ - CNPJ 11.222.333/0001-44
        """

        pagador = extractor.extrair_pagador(texto)
        assert "EMPRESA XYZ" in pagador
        assert "CNPJ" not in pagador

    def test_extrair_pagador_com_cpf(self, extractor):
        """Teste: pagador pessoa física (CPF)"""
        texto = """
        Pagador
        MARIA SILVA - CPF 123.456.789-01
        """

        pagador = extractor.extrair_pagador(texto)
        assert "MARIA SILVA" in pagador
        assert "CPF" not in pagador

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VENCIMENTO
    # ================================================================

    def test_extrair_vencimento(self, extractor, texto_boleto_credvale):
        """Teste: extração de vencimento"""
        vencimento = extractor.extrair_vencimento(texto_boleto_credvale)
        assert vencimento == "20-07"

    def test_extrair_vencimento_mesma_linha(self, extractor):
        """Teste: vencimento na mesma linha da palavra 'Vencimento'"""
        texto = "Vencimento 25/11/2025"
        vencimento = extractor.extrair_vencimento(texto)
        assert vencimento == "25-11"

    def test_extrair_vencimento_proxima_linha(self, extractor):
        """Teste: vencimento na próxima linha"""
        texto = """
        Vencimento
        10/05/2025
        """

        vencimento = extractor.extrair_vencimento(texto)
        assert vencimento == "10-05"

    def test_extrair_vencimento_diferentes_datas(self, extractor):
        """Teste: vencimentos com diferentes datas"""
        casos = [
            ("Vencimento 01/01/2025", "01-01"),
            ("Vencimento 15/08/2025", "15-08"),
            ("Vencimento 31/12/2025", "31-12"),
        ]

        for texto, esperado in casos:
            vencimento = extractor.extrair_vencimento(texto)
            assert vencimento == esperado

    # ================================================================
    # TESTE DE INTEGRAÇÃO
    # ================================================================

    def test_extrair_dados_completo(self, extractor, texto_boleto_credvale):
        """Teste de integração: extrai todos os dados juntos"""
        pagador, vencimento, valor = extractor.extrair_dados(texto_boleto_credvale)

        assert pagador != "SEM_PAGADOR"
        assert vencimento != "SEM_VENCIMENTO"
        assert valor != "SEM_VALOR"

        assert "EMPRESA CREDVALE TESTE LTDA" in pagador
        assert vencimento == "20-07"
        assert valor == "R$ 3.750,00"

    # ================================================================
    # TESTES DE ISOLAMENTO
    # ================================================================

    def test_nao_afeta_outros_fidcs(self, extractor):
        """
        Teste de isolamento: CREDVALE não afeta outros FIDCs
        """
        from extractors import SQUIDExtractor, CAPITALExtractor, NOVAXExtractor

        credvale_ext = extractor
        squid_ext = SQUIDExtractor()
        capital_ext = CAPITALExtractor()
        novax_ext = NOVAXExtractor()

        # Todos devem ser instâncias diferentes
        assert credvale_ext is not squid_ext
        assert credvale_ext is not capital_ext
        assert credvale_ext is not novax_ext
        assert credvale_ext.__class__.__name__ == "CREDVALEExtractor"

    # ================================================================
    # TESTES DE PROPRIEDADES
    # ================================================================

    def test_nome_fidc(self, extractor):
        """Teste: propriedade nome_fidc retorna 'CREDVALE'"""
        assert extractor.nome_fidc == "CREDVALE"

    def test_repr(self, extractor):
        """Teste: representação string do extrator"""
        repr_str = repr(extractor)
        assert "CREDVALEExtractor" in repr_str


# ================================================================
# TESTES PARAMETRIZADOS
# ================================================================

@pytest.mark.parametrize("valor_str,esperado", [
    ("1.500,00", "R$ 1.500,00"),
    ("250,75", "R$ 250,75"),
    ("20.000,00", "R$ 20.000,00"),
    ("99,99", "R$ 99,99"),
])
def test_valores_diversos_credvale(valor_str, esperado):
    """Teste parametrizado: diversos valores CREDVALE"""
    extractor = CREDVALEExtractor()
    texto = f"(=) Valor do Documento  {valor_str}"

    valor = extractor.extrair_valor(texto)
    assert valor == esperado


@pytest.mark.parametrize("nome_pagador", [
    "EMPRESA COMERCIAL LTDA",
    "JOAO PEDRO DA SILVA",
    "INDUSTRIA ABC",
    "COMERCIO X & Y ME",
])
def test_pagadores_diversos_credvale(nome_pagador):
    """Teste parametrizado: diversos nomes de pagador"""
    extractor = CREDVALEExtractor()
    texto = f"""
    Pagador
    {nome_pagador} - CNPJ 12.345.678/0001-90
    """

    pagador = extractor.extrair_pagador(texto)
    # Pelo menos a primeira palavra deve estar presente
    primeira_palavra = nome_pagador.split()[0]
    assert primeira_palavra in pagador
    assert "CNPJ" not in pagador
