# ===============================================
# Base Extractor - Interface Comum para Todos os FIDCs
# ===============================================
#
# Define o contrato que todos os extratores devem seguir.
# Cada FIDC implementa sua própria lógica de extração.
#
# ===============================================

from abc import ABC, abstractmethod
from typing import Tuple

class BaseExtractor(ABC):
    """
    Classe abstrata que define a interface para todos os extratores de FIDCs.

    Cada FIDC (SQUID, CAPITAL, NOVAX, CREDVALE) deve implementar sua própria
    versão desta classe com lógica de extração específica e isolada.

    Benefícios:
    - Isolamento: Editar um extrator NÃO afeta os outros
    - Consistência: Todos os extratores têm a mesma interface
    - Testabilidade: Cada extrator pode ser testado independentemente
    """

    @property
    @abstractmethod
    def nome_fidc(self) -> str:
        """
        Nome do FIDC (SQUID, CAPITAL, NOVAX, CREDVALE)

        Returns:
            str: Nome do FIDC em maiúsculas
        """
        pass

    @abstractmethod
    def extrair_pagador(self, texto: str) -> str:
        """
        Extrai o nome do pagador do texto do PDF

        Args:
            texto: Texto completo extraído do PDF do boleto

        Returns:
            str: Nome do pagador ou "SEM_PAGADOR"
        """
        pass

    @abstractmethod
    def extrair_vencimento(self, texto: str) -> str:
        """
        Extrai a data de vencimento do texto do PDF

        Args:
            texto: Texto completo extraído do PDF do boleto

        Returns:
            str: Vencimento no formato "DD-MM" ou "SEM_VENCIMENTO"
        """
        pass

    @abstractmethod
    def extrair_valor(self, texto: str) -> str:
        """
        Extrai o valor do boleto do texto do PDF

        Args:
            texto: Texto completo extraído do PDF do boleto

        Returns:
            str: Valor no formato "R$ X.XXX,XX" ou "SEM_VALOR"
        """
        pass

    def extrair_dados(self, texto: str) -> Tuple[str, str, str]:
        """
        Método público que extrai todos os dados do boleto

        Este método chama os três métodos abstratos (extrair_pagador,
        extrair_vencimento, extrair_valor) na ordem correta.

        Args:
            texto: Texto completo extraído do PDF do boleto

        Returns:
            Tuple[str, str, str]: (pagador, vencimento, valor)
        """
        pagador = self.extrair_pagador(texto)
        vencimento = self.extrair_vencimento(texto)
        valor = self.extrair_valor(texto)

        return pagador, vencimento, valor

    def __repr__(self) -> str:
        """Representação string do extrator"""
        return f"<{self.__class__.__name__} fidc='{self.nome_fidc}'>"
