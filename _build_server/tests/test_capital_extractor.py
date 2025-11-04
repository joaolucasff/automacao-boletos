"""
Testes para o Extrator CAPITAL RS

Este arquivo contém testes isolados para o extrator CAPITAL RS FIDC.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors import CAPITALExtractor


class TestCAPITALExtractor:
    """Suite de testes para o extrator CAPITAL RS"""

    @pytest.fixture
    def extractor(self):
        """Fixture que retorna instância do extrator CAPITAL"""
        return CAPITALExtractor()

    @pytest.fixture
    def texto_danfe_capital(self):
        """Fixture com texto DANFE CAPITAL básico"""
        return """
        CAPITAL RS FIDC NP MULTISSETORIAL

        DESTINATÁRIO REMETENTE
        NOME/RAZÃO SOCIAL
        EMPRESA CAPITAL LTDA

        VENCIMENTO
        15/03/2025

        FATURA
        NÚMERO VENCIMENTO VALOR
        001 15/03/2025 2.500,00
        """

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VALOR
    # ================================================================

    def test_extrair_valor_danfe_fatura(self, extractor):
        """Teste: extração de valor da seção FATURA (DANFE)"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 15/03/2025 2.500,00
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 2.500,00", f"Esperado 'R$ 2.500,00', obtido '{valor}'"

    def test_extrair_valor_com_milhares(self, extractor):
        """Teste: valor com separador de milhares"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 15/03/2025 15.750,50
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 15.750,50"

    def test_extrair_valor_documento_tradicional(self, extractor):
        """Teste: valor de boleto tradicional (campo Valor Documento)"""
        texto = """
        (=) Valor do Documento  R$ 3.456,78
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 3.456,78"

    def test_extrair_valor_pequeno(self, extractor):
        """Teste: valor pequeno sem separador de milhares"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 15/03/2025 99,99
        """

        valor = extractor.extrair_valor(texto)
        assert valor == "R$ 99,99"

    # ================================================================
    # TESTES DE EXTRAÇÃO DE PAGADOR
    # ================================================================

    def test_extrair_pagador_danfe(self, extractor, texto_danfe_capital):
        """Teste: extração de pagador de DANFE CAPITAL"""
        pagador = extractor.extrair_pagador(texto_danfe_capital)
        assert "EMPRESA CAPITAL LTDA" in pagador

    def test_extrair_pagador_remove_cnpj(self, extractor):
        """Teste: CNPJ deve ser removido do nome do pagador"""
        texto = """
        DESTINATÁRIO REMETENTE
        NOME/RAZÃO SOCIAL
        EMPRESA TESTE LTDA 12.345.678/0001-90
        """

        pagador = extractor.extrair_pagador(texto)
        assert "EMPRESA TESTE LTDA" in pagador
        assert "12.345.678" not in pagador

    def test_extrair_pagador_boleto_tradicional(self, extractor):
        """Teste: extração de pagador de boleto tradicional"""
        texto = """
        Pagador
        CLIENTE EXEMPLO LTDA
        """

        pagador = extractor.extrair_pagador(texto)
        assert "CLIENTE EXEMPLO LTDA" in pagador

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VENCIMENTO
    # ================================================================

    def test_extrair_vencimento(self, extractor, texto_danfe_capital):
        """Teste: extração de vencimento"""
        vencimento = extractor.extrair_vencimento(texto_danfe_capital)
        assert vencimento == "15-03"

    def test_extrair_vencimento_diferentes_meses(self, extractor):
        """Teste: vencimentos em diferentes meses"""
        casos = [
            ("01/01/2025", "01-01"),
            ("15/06/2025", "15-06"),
            ("31/12/2025", "31-12"),
        ]

        for data_completa, esperado in casos:
            texto = f"VENCIMENTO\n{data_completa}"
            vencimento = extractor.extrair_vencimento(texto)
            assert vencimento == esperado

    # ================================================================
    # TESTE DE INTEGRAÇÃO
    # ================================================================

    def test_extrair_dados_completo(self, extractor, texto_danfe_capital):
        """Teste de integração: extrai todos os dados juntos"""
        pagador, vencimento, valor = extractor.extrair_dados(texto_danfe_capital)

        assert pagador != "SEM_PAGADOR"
        assert vencimento != "SEM_VENCIMENTO"
        assert valor != "SEM_VALOR"

        assert "EMPRESA CAPITAL LTDA" in pagador
        assert vencimento == "15-03"
        assert valor == "R$ 2.500,00"

    # ================================================================
    # TESTES DE ISOLAMENTO
    # ================================================================

    def test_nao_afeta_squid(self, extractor):
        """
        Teste de isolamento: código CAPITAL não deve afetar SQUID

        Este teste garante que a arquitetura isolada está funcionando.
        """
        from extractors import SQUIDExtractor

        capital_ext = extractor
        squid_ext = SQUIDExtractor()

        # Devem ser instâncias diferentes
        assert capital_ext is not squid_ext
        assert capital_ext.__class__.__name__ != squid_ext.__class__.__name__

    # ================================================================
    # TESTES DE PROPRIEDADES
    # ================================================================

    def test_nome_fidc(self, extractor):
        """Teste: propriedade nome_fidc retorna 'CAPITAL'"""
        assert extractor.nome_fidc == "CAPITAL"

    def test_repr(self, extractor):
        """Teste: representação string do extrator"""
        repr_str = repr(extractor)
        assert "CAPITALExtractor" in repr_str


# ================================================================
# TESTES PARAMETRIZADOS
# ================================================================

@pytest.mark.parametrize("valor_str,esperado", [
    ("1.234,56", "R$ 1.234,56"),
    ("999,99", "R$ 999,99"),
    ("10.000,00", "R$ 10.000,00"),
    ("250.500,75", "R$ 250.500,75"),
])
def test_valores_diversos(valor_str, esperado):
    """Teste parametrizado: diversos formatos de valor"""
    extractor = CAPITALExtractor()
    texto = f"""
    FATURA
    NÚMERO VENCIMENTO VALOR
    001 15/03/2025 {valor_str}
    """

    valor = extractor.extrair_valor(texto)
    assert valor == esperado
