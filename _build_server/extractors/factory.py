# ===============================================
# Extractor Factory - Seletor Automático de Extratores
# ===============================================
#
# Este arquivo implementa o Factory Pattern para selecionar
# automaticamente o extrator correto baseado no FIDC.
#
# Quando a interface detecta que o boleto é SQUID, o factory
# retorna SQUIDExtractor. Quando detecta CAPITAL, retorna
# CAPITALExtractor, e assim por diante.
#
# Benefícios:
# - Centraliza a lógica de seleção
# - Fácil adicionar novos FIDCs (só adicionar no dicionário)
# - Interface gráfica não precisa saber dos detalhes
#
# ===============================================

from .base import BaseExtractor
from .squid import SQUIDExtractor
from .capital import CAPITALExtractor
from .novax import NOVAXExtractor
from .credvale import CREDVALEExtractor

class ExtractorFactory:
    """
    Factory que seleciona o extrator correto baseado no FIDC

    Esta classe implementa o padrão Factory (Padrão de Projeto GoF).
    Ela encapsula a lógica de criação de objetos extratores.

    Exemplo de uso:
        >>> fidc = "SQUID"
        >>> extractor = ExtractorFactory.get_extractor(fidc)
        >>> pagador, vencimento, valor = extractor.extrair_dados(texto)
    """

    # Instâncias únicas dos extratores (Singleton Pattern)
    # Criamos uma única instância de cada extrator para economizar memória
    _extractors = {
        "SQUID": SQUIDExtractor(),
        "CAPITAL": CAPITALExtractor(),
        "NOVAX": NOVAXExtractor(),
        "CREDVALE": CREDVALEExtractor(),
    }

    @classmethod
    def get_extractor(cls, fidc: str) -> BaseExtractor:
        """
        Retorna o extrator correto para o FIDC especificado

        Args:
            fidc: Nome do FIDC ("SQUID", "CAPITAL", "NOVAX", "CREDVALE")
                  Não é case-sensitive (aceita "squid", "Squid", "SQUID")

        Returns:
            BaseExtractor: Instância do extrator específico do FIDC

        Examples:
            >>> extractor = ExtractorFactory.get_extractor("SQUID")
            >>> print(extractor.nome_fidc)
            SQUID

            >>> extractor = ExtractorFactory.get_extractor("capital")
            >>> print(extractor.nome_fidc)
            CAPITAL
        """
        # Normaliza o nome do FIDC para maiúsculas
        fidc_upper = fidc.upper() if fidc else ""

        # Busca o extrator no dicionário
        extractor = cls._extractors.get(fidc_upper)

        if extractor is None:
            # Fallback: CAPITAL como padrão
            # Isso garante que sempre retornaremos um extrator válido
            print(f"[AVISO] FIDC '{fidc}' não reconhecido. Usando CAPITAL como fallback.")
            return cls._extractors["CAPITAL"]

        return extractor

    @classmethod
    def get_available_fidcs(cls) -> list:
        """
        Retorna lista de FIDCs disponíveis

        Returns:
            list: Lista com nomes dos FIDCs configurados

        Example:
            >>> fidcs = ExtractorFactory.get_available_fidcs()
            >>> print(fidcs)
            ['SQUID', 'CAPITAL', 'NOVAX', 'CREDVALE']
        """
        return list(cls._extractors.keys())

    @classmethod
    def register_extractor(cls, fidc: str, extractor: BaseExtractor) -> None:
        """
        Registra um novo extrator dinamicamente

        Útil para adicionar novos FIDCs sem modificar o código do factory.

        Args:
            fidc: Nome do FIDC
            extractor: Instância do extrator

        Example:
            >>> novo_extrator = NovoFIDCExtractor()
            >>> ExtractorFactory.register_extractor("NOVO_FIDC", novo_extrator)
        """
        cls._extractors[fidc.upper()] = extractor
        print(f"[INFO] Extrator '{fidc.upper()}' registrado com sucesso.")

    @classmethod
    def info(cls) -> str:
        """
        Retorna informações sobre os extratores disponíveis

        Returns:
            str: String formatada com informações dos extratores

        Example:
            >>> print(ExtractorFactory.info())
            Extratores disponíveis:
            - SQUID: <SQUIDExtractor fidc='SQUID'>
            - CAPITAL: <CAPITALExtractor fidc='CAPITAL'>
            - NOVAX: <NOVAXExtractor fidc='NOVAX'>
            - CREDVALE: <CREDVALEExtractor fidc='CREDVALE'>
        """
        info_lines = ["Extratores disponíveis:"]
        for fidc, extractor in cls._extractors.items():
            info_lines.append(f"  - {fidc}: {extractor}")
        return "\n".join(info_lines)


# ===============================================
# Função de conveniência para compatibilidade
# ===============================================

def get_extractor_for_fidc(fidc: str) -> BaseExtractor:
    """
    Função auxiliar que retorna extrator para o FIDC

    Esta é uma função de conveniência que pode ser importada diretamente:
        from extractors import get_extractor_for_fidc

    Args:
        fidc: Nome do FIDC

    Returns:
        BaseExtractor: Extrator apropriado
    """
    return ExtractorFactory.get_extractor(fidc)
