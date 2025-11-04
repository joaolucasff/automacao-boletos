"""
Testes para o Extrator SQUID

Este arquivo contém testes isolados para o extrator SQUID.
Testa casos específicos de boletos SQUID, incluindo casos de regressão.
"""

import pytest
import sys
import os

# Adicionar pasta pai ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors import SQUIDExtractor
from RenomeaçãoBoletos import extrair_texto_pdf


class TestSQUIDExtractor:
    """
    Suite de testes para o extrator SQUID

    Testa:
    - Extração de valor (caso crítico com bug corrigido)
    - Extração de pagador
    - Extração de vencimento
    - Casos de regressão
    """

    @pytest.fixture
    def extractor(self):
        """Fixture que retorna instância do extrator SQUID"""
        return SQUIDExtractor()

    @pytest.fixture
    def texto_danfe_basico(self):
        """Fixture com texto DANFE SQUID básico para testes"""
        return """
        SQUID FUNDO DE INVESTIMENTO

        DESTINATÁRIO REMETENTE
        NOME/RAZÃO SOCIAL
        EMPRESA TESTE LTDA

        VENCIMENTO
        01/12/2025

        FATURA
        NÚMERO VENCIMENTO VALOR
        001 01/12/2025 1.234,56
        """

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VALOR (CRÍTICO)
    # ================================================================

    def test_extrair_valor_formato_basico(self, extractor):
        """Teste básico: valor com formato R$ X.XXX,XX"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 01/12/2025 1.234,56
        """

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 1.234,56", f"Esperado 'R$ 1.234,56', obtido '{valor}'"

    def test_extrair_valor_sem_milhares(self, extractor):
        """Teste: valor sem separador de milhares R$ XXX,XX"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 01/12/2025 110,25
        """

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 110,25", f"Esperado 'R$ 110,25', obtido '{valor}'"

    def test_extrair_valor_com_milhoes(self, extractor):
        """Teste: valor grande com milhões R$ X.XXX.XXX,XX"""
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 01/12/2025 1.234.567,89
        """

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 1.234.567,89", f"Esperado 'R$ 1.234.567,89', obtido '{valor}'"

    # ================================================================
    # TESTES DE REGRESSÃO (BUG 03/11/2025)
    # ================================================================

    def test_regressao_dia_26_nao_concatenado(self, extractor):
        """
        Teste de regressão: Dia 26 do vencimento NÃO deve ser concatenado ao valor

        Bug anterior: 26/09/2025 + 5.223,09 = 60.000.522,30
        Esperado: R$ 5.223,09
        """
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 26/09/2025 5.223,09
        """

        valor = extractor.extrair_valor(texto)

        # Verificações
        assert valor == "R$ 5.223,09", f"Valor incorreto: {valor}"
        assert "60.000" not in valor, "Dia do vencimento (26) foi concatenado ao valor!"
        assert "000.522" not in valor, "Formato corrompido detectado!"

    def test_regressao_dia_25_nao_concatenado(self, extractor):
        """
        Teste de regressão: Dia 25 do vencimento NÃO deve ser concatenado

        Bug anterior: 25/09/2025 + 3.280,82 = 50.000.328,08
        Esperado: R$ 3.280,82
        """
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 25/09/2025 3.280,82
        """

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 3.280,82", f"Valor incorreto: {valor}"
        assert "50.000" not in valor, "Dia do vencimento (25) foi concatenado ao valor!"

    def test_regressao_dia_30_nao_concatenado(self, extractor):
        """
        Teste de regressão: Dia 30 do vencimento NÃO deve ser concatenado
        """
        texto = """
        FATURA
        NÚMERO VENCIMENTO VALOR
        001 30/09/2025 110,25
        """

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 110,25", f"Valor incorreto: {valor}"
        # Dia 30 + 110,25 não criaria problema óbvio, mas garantir formato correto
        assert valor.startswith("R$ "), "Valor deve começar com 'R$ '"

    # ================================================================
    # TESTES DE EXTRAÇÃO DE PAGADOR
    # ================================================================

    def test_extrair_pagador_danfe(self, extractor, texto_danfe_basico):
        """Teste: extração de pagador de DANFE (DESTINATÁRIO/REMETENTE)"""
        pagador = extractor.extrair_pagador(texto_danfe_basico)

        assert pagador == "EMPRESA TESTE LTDA", f"Pagador incorreto: '{pagador}'"

    def test_extrair_pagador_boleto_tradicional(self, extractor):
        """Teste: extração de pagador de boleto tradicional (campo Pagador)"""
        texto = """
        Pagador
        CLIENTE EXEMPLO LTDA - CNPJ: 12.345.678/0001-90
        """

        pagador = extractor.extrair_pagador(texto)

        assert "CLIENTE EXEMPLO LTDA" in pagador
        assert "CNPJ" not in pagador, "CNPJ não deve ser incluído no nome"

    # ================================================================
    # TESTES DE EXTRAÇÃO DE VENCIMENTO
    # ================================================================

    def test_extrair_vencimento_formato_basico(self, extractor, texto_danfe_basico):
        """Teste: extração de vencimento no formato DD-MM"""
        vencimento = extractor.extrair_vencimento(texto_danfe_basico)

        assert vencimento == "01-12", f"Vencimento incorreto: '{vencimento}'"

    def test_extrair_vencimento_diferentes_datas(self, extractor):
        """Teste: vencimentos com diferentes datas"""
        casos = [
            ("15/03/2025", "15-03"),
            ("28/02/2025", "28-02"),
            ("31/12/2025", "31-12"),
        ]

        for data_completa, esperado in casos:
            texto = f"VENCIMENTO\n{data_completa}"
            vencimento = extractor.extrair_vencimento(texto)
            assert vencimento == esperado, f"Data {data_completa} -> esperado {esperado}, obtido {vencimento}"

    # ================================================================
    # TESTE DE INTEGRAÇÃO
    # ================================================================

    def test_extrair_dados_completo(self, extractor, texto_danfe_basico):
        """Teste de integração: extrai pagador, vencimento e valor juntos"""
        pagador, vencimento, valor = extractor.extrair_dados(texto_danfe_basico)

        assert pagador != "SEM_PAGADOR", "Pagador não foi extraído"
        assert vencimento != "SEM_VENCIMENTO", "Vencimento não foi extraído"
        assert valor != "SEM_VALOR", "Valor não foi extraído"

        assert "EMPRESA TESTE LTDA" in pagador
        assert vencimento == "01-12"
        assert valor == "R$ 1.234,56"

    # ================================================================
    # TESTE COM PDF REAL (SE DISPONÍVEL)
    # ================================================================

    @pytest.mark.skipif(
        not os.path.exists("tests/fixtures/squid/3-0305537.pdf"),
        reason="PDF de teste não disponível"
    )
    def test_pdf_real_nf_305537(self, extractor):
        """
        Teste com PDF real: NF 305537 (caso crítico do bug)

        Este é o PDF que estava retornando valor incorreto.
        Esperado: R$ 5.223,09
        Bug anterior: R$ 60.000.522,30
        """
        pdf_path = "tests/fixtures/squid/3-0305537.pdf"
        texto = extrair_texto_pdf(pdf_path)

        valor = extractor.extrair_valor(texto)

        assert valor == "R$ 5.223,09", f"Valor incorreto no PDF real: {valor}"
        assert "60.000" not in valor, "Bug de concatenação ainda presente!"

    # ================================================================
    # TESTES DE PROPRIEDADES
    # ================================================================

    def test_nome_fidc(self, extractor):
        """Teste: propriedade nome_fidc retorna 'SQUID'"""
        assert extractor.nome_fidc == "SQUID"

    def test_repr(self, extractor):
        """Teste: representação string do extrator"""
        repr_str = repr(extractor)
        assert "SQUIDExtractor" in repr_str
        assert "SQUID" in repr_str


# ================================================================
# TESTES PARAMETRIZADOS
# ================================================================

@pytest.mark.parametrize("dia,mes,valor_str,esperado", [
    (26, 9, "5.223,09", "R$ 5.223,09"),
    (25, 9, "3.280,82", "R$ 3.280,82"),
    (30, 9, "110,25", "R$ 110,25"),
    (15, 3, "1.234,56", "R$ 1.234,56"),
    (1, 12, "999,99", "R$ 999,99"),
])
def test_valores_diversos_datas(dia, mes, valor_str, esperado):
    """Teste parametrizado: diversos valores com diferentes datas de vencimento"""
    extractor = SQUIDExtractor()
    texto = f"""
    FATURA
    NÚMERO VENCIMENTO VALOR
    001 {dia:02d}/{mes:02d}/2025 {valor_str}
    """

    valor = extractor.extrair_valor(texto)
    assert valor == esperado, f"Data {dia:02d}/{mes:02d} -> esperado {esperado}, obtido {valor}"
