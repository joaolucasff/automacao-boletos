# ===============================================
# Módulo de Extratores - Sistema de Boletos
# ===============================================
#
# Este módulo contém extratores isolados por FIDC.
# Cada FIDC tem seu próprio arquivo com lógica independente.
#
# Arquitetura:
# - base.py: Interface comum (BaseExtractor)
# - squid.py: Extrator SQUID isolado
# - capital.py: Extrator CAPITAL isolado
# - novax.py: Extrator NOVAX isolado
# - credvale.py: Extrator CREDVALE isolado
# - factory.py: Seletor automático (Factory Pattern)
#
# Benefícios:
# ✅ Isolamento total: editar um FIDC não afeta outros
# ✅ Testabilidade: cada extrator pode ser testado separadamente
# ✅ Escalabilidade: fácil adicionar novos FIDCs
# ✅ Manutenibilidade: código organizado e limpo
#
# Uso:
#   from extractors import ExtractorFactory
#
#   extractor = ExtractorFactory.get_extractor("SQUID")
#   pagador, vencimento, valor = extractor.extrair_dados(texto_pdf)
#
# ===============================================

from .base import BaseExtractor
from .factory import ExtractorFactory, get_extractor_for_fidc

# Exportar extratores individuais (opcional, para testes)
from .squid import SQUIDExtractor
from .capital import CAPITALExtractor
from .novax import NOVAXExtractor
from .credvale import CREDVALEExtractor

# Define o que é exportado quando alguém faz "from extractors import *"
__all__ = [
    # Principal (usado pelo código)
    'ExtractorFactory',
    'get_extractor_for_fidc',

    # Base (para type hints e herança)
    'BaseExtractor',

    # Extratores individuais (para testes)
    'SQUIDExtractor',
    'CAPITALExtractor',
    'NOVAXExtractor',
    'CREDVALEExtractor',
]

# Metadados do módulo
__version__ = '2.0.0'
__author__ = 'Sistema Boletos JotaJota'
__description__ = 'Módulo de extratores isolados por FIDC'

# Informações de debug (útil para troubleshooting)
def get_module_info():
    """Retorna informações sobre o módulo de extratores"""
    return {
        'version': __version__,
        'available_fidcs': ExtractorFactory.get_available_fidcs(),
        'extractors_count': len(ExtractorFactory.get_available_fidcs()),
    }

# Log de inicialização (apenas para desenvolvimento)
if __name__ != "__main__":
    # Quando o módulo é importado, podemos fazer log silencioso
    pass
else:
    # Quando executado diretamente (python -m extractors)
    print("=" * 60)
    print("Módulo de Extratores - Sistema de Boletos")
    print("=" * 60)
    print(ExtractorFactory.info())
    print("\nVersão:", __version__)
    print("FIDCs disponíveis:", ExtractorFactory.get_available_fidcs())
    print("=" * 60)
