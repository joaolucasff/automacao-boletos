"""
Testes para o Extrator NOVAX

Este arquivo contém testes isolados para o extrator NOVAX FIDC.
NOVAX usa formato de boleto tradicional (não DANFE).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors import NOVAXExtractor


class TestNOVAXExtractor:
    """Suite de testes para o extrator NOVAX"""

    @pytest.fixture
    def extractor(self):
        """Fixture que retorna instância do extrator NOVAX"""
        return NOVAXExtractor()

    @pytest.fixture
    def texto_boleto_novax(self):
        """Fixture com texto de boleto NOVAX básico"""
        return """
        NOVAX FUNDO DE INVESTIMENTO

        Vencimento  15/06/2025

        Pagador: EMPRESA NOVAX LTDA CNPJ 12.345.678/0001-90

        (=) Valor do Documento  R$ 5.678,90
        """

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VALOR
    # ================================================================

    def test_extrair_valor_documento(self, extractor):
        """Teste: extração de valor do campo Valor Documento"""
        texto = """
        (=) Valor do Documento  R$ 5.678,90
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 5.678,90"

    def test_extrair_valor_sem_rs(self, extractor):
        """Teste: extração de valor sem prefixo R$"""
        texto = """
        Valor do Documento  2.345,67
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 2.345,67"

    def test_extrair_valor_com_milhares(self, extractor):
        """Teste: valor grande com separador de milhares"""
        texto = """
        (=) Valor do Documento  R$ 25.500,00
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 25.500,00"

    def test_extrair_valor_pequeno(self, extractor):
        """Teste: valor pequeno sem milhares"""
        texto = """
        (=) Valor do Documento  R$ 150,50
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 150,50"

    # ================================================================
    # TESTES DE EXTRAÇÃO DE PAGADOR (CRÍTICO PARA NOVAX)
    # ================================================================

    def test_extrair_pagador_formato_padrao(self, extractor, texto_boleto_novax):
        """
        Teste: extração de pagador no formato NOVAX padrão

        NOVAX usa: "Pagador: NOME CNPJ/CPF"
        """
        pagador = extractor.extrair_pagador(texto_boleto_novax)

        assert "EMPRESA NOVAX LTDA" in pagador
        assert "CNPJ" not in pagador, "CNPJ não deve ser incluído"
        assert "12.345.678" not in pagador, "Números do CNPJ não devem ser incluídos"

    def test_extrair_pagador_com_cpf(self, extractor):
        """Teste: extração de pagador com CPF (pessoa física)"""
        texto = """
        Pagador: JOAO DA SILVA CPF 123.456.789-01
        """

        pagador = extractor.extrair_pagador(texto)
        assert "JOAO DA SILVA" in pagador
        assert "CPF" not in pagador
        assert "123.456.789" not in pagador

    def test_extrair_pagador_sem_espacos_extras(self, extractor):
        """Teste: pagador sem espaços extras"""
        texto = """
        Pagador:EMPRESA TESTE LTDA CNPJ 11.222.333/0001-44
        """

        pagador = extractor.extrair_pagador(texto)
        assert "EMPRESA TESTE LTDA" in pagador

    def test_extrair_pagador_com_caracteres_especiais(self, extractor):
        """Teste: pagador com caracteres especiais (hífen, ponto, &)"""
        texto = """
        Pagador: EMPRESA A-B & C LTDA. CNPJ 99.888.777/0001-66
        """

        pagador = extractor.extrair_pagador(texto)
        assert "EMPRESA A-B & C LTDA" in pagador or "EMPRESA A-B" in pagador

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VENCIMENTO
    # ================================================================

    def test_extrair_vencimento(self, extractor, texto_boleto_novax):
        """Teste: extração de vencimento"""
        vencimento = extractor.extrair_vencimento(texto_boleto_novax)
        assert vencimento == "15-06"

    def test_extrair_vencimento_texto_compacto(self, extractor):
        """
        Teste: vencimento em texto compacto (sem quebras de linha)

        NOVAX compacta o texto, então "Vencimento 15/06/2025" pode estar
        na mesma linha.
        """
        texto = "Vencimento 20/08/2025 Valor 1.234,56"
        vencimento = extractor.extrair_vencimento(texto)
        assert vencimento == "20-08"

    def test_extrair_vencimento_diferentes_datas(self, extractor):
        """Teste: vencimentos com diferentes datas"""
        casos = [
            ("Vencimento 01/01/2025", "01-01"),
            ("Vencimento 15/12/2025", "15-12"),
            ("Vencimento 31/03/2025", "31-03"),
        ]

        for texto, esperado in casos:
            vencimento = extractor.extrair_vencimento(texto)
            assert vencimento == esperado

    # ================================================================
    # TESTE DE INTEGRAÇÃO
    # ================================================================

    def test_extrair_dados_completo(self, extractor, texto_boleto_novax):
        """Teste de integração: extrai todos os dados juntos"""
        pagador, vencimento, valor = extractor.extrair_dados(texto_boleto_novax)

        assert pagador != "SEM_PAGADOR"
        assert vencimento != "SEM_VENCIMENTO"
        assert valor != "SEM_VALOR"

        assert "EMPRESA NOVAX LTDA" in pagador
        assert vencimento == "15-06"
        assert valor == "R$ 5.678,90"

    # ================================================================
    # TESTES DE ISOLAMENTO
    # ================================================================

    def test_nao_afeta_squid_nem_capital(self, extractor):
        """
        Teste de isolamento: NOVAX não afeta SQUID nem CAPITAL
        """
        from extractors import SQUIDExtractor, CAPITALExtractor

        novax_ext = extractor
        squid_ext = SQUIDExtractor()
        capital_ext = CAPITALExtractor()

        # Todos devem ser instâncias diferentes
        assert novax_ext is not squid_ext
        assert novax_ext is not capital_ext
        assert novax_ext.__class__.__name__ == "NOVAXExtractor"

    # ================================================================
    # TESTES DE PROPRIEDADES
    # ================================================================

    def test_nome_fidc(self, extractor):
        """Teste: propriedade nome_fidc retorna 'NOVAX'"""
        assert extractor.nome_fidc == "NOVAX"

    def test_repr(self, extractor):
        """Teste: representação string do extrator"""
        repr_str = repr(extractor)
        assert "NOVAXExtractor" in repr_str


# ================================================================
# TESTES PARAMETRIZADOS
# ================================================================

@pytest.mark.parametrize("valor_str,esperado", [
    ("1.000,00", "R$ 1.000,00"),
    ("500,50", "R$ 500,50"),
    ("15.750,25", "R$ 15.750,25"),
    ("99,99", "R$ 99,99"),
])
def test_valores_diversos_novax(valor_str, esperado):
    """Teste parametrizado: diversos valores NOVAX"""
    extractor = NOVAXExtractor()
    texto = f"(=) Valor do Documento  {valor_str}"

    valor = extractor.extrair_valor(texto)
    assert valor == esperado


@pytest.mark.parametrize("nome_pagador", [
    "EMPRESA ABC LTDA",
    "JOAO SILVA",
    "COMERCIO X-Y-Z LTDA",
    "INDUSTRIA & COMERCIO ME",
])
def test_pagadores_diversos(nome_pagador):
    """Teste parametrizado: diversos nomes de pagador"""
    extractor = NOVAXExtractor()
    texto = f"Pagador: {nome_pagador} CNPJ 12.345.678/0001-90"

    pagador = extractor.extrair_pagador(texto)
    assert nome_pagador.split()[0] in pagador  # Pelo menos primeira palavra
    assert "CNPJ" not in pagador
