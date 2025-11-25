"""
================================================================================
auditoria.py - Sistema de Auditoria Profissional
================================================================================

Módulo responsável por registrar e gerar relatórios completos de auditoria
para o sistema de envio de boletos.

Funcionalidades:
- Registro detalhado de cada operação
- Rastreabilidade completa (todas as validações)
- Relatórios em formato TXT (legível) e JSON (estruturado)
- Timestamps precisos para cada evento
- Checksums para integridade dos dados

Autor: Sistema de Boletos v6.0
Data: 2025-10-30
================================================================================
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import hashlib

# ==================== CLASSES DE AUDITORIA ====================

class BoletoAuditoria:
    """
    Representa a auditoria completa de um único boleto processado.
    """

    def __init__(self, arquivo: str, timestamp: datetime = None):
        self.arquivo = arquivo
        self.timestamp = timestamp or datetime.now()
        self.status = "pendente"  # pendente, aprovado, rejeitado
        self.motivo_rejeicao = None

        # Validações (5 camadas)
        self.validacoes = {
            'xml_encontrado': None,
            'cnpj_match': None,
            'nome_match': None,
            'valor_match': None,
            'email_valido': None
        }

        # Dados extraídos
        self.dados_xml = {}
        self.dados_boleto = {}
        self.notas_fiscais = []

        # Resultado
        self.email_enviado = False
        self.email_destinatarios = []
        self.email_cc = []
        self.anexos_count = 0

        # Detalhes de validação
        self.detalhes_validacao = []


    def adicionar_detalhe(self, camada: str, sucesso: bool, mensagem: str):
        """
        Adiciona um detalhe de validação.
        """
        self.detalhes_validacao.append({
            'camada': camada,
            'sucesso': sucesso,
            'mensagem': mensagem,
            'timestamp': datetime.now()
        })


    def aprovar(self):
        """Marca boleto como aprovado."""
        self.status = "aprovado"


    def rejeitar(self, motivo: str):
        """Marca boleto como rejeitado com motivo."""
        self.status = "rejeitado"
        self.motivo_rejeicao = motivo


    def to_dict(self) -> dict:
        """Converte para dicionário (para JSON)."""
        return {
            'arquivo': self.arquivo,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'motivo_rejeicao': self.motivo_rejeicao,
            'validacoes': self.validacoes,
            'dados_xml': self._serializar_dados(self.dados_xml),
            'dados_boleto': self._serializar_dados(self.dados_boleto),
            'notas_fiscais': self.notas_fiscais,
            'email_enviado': self.email_enviado,
            'email_destinatarios': self.email_destinatarios,
            'email_cc': self.email_cc,
            'anexos_count': self.anexos_count,
            'detalhes_validacao': [
                {
                    'camada': d['camada'],
                    'sucesso': d['sucesso'],
                    'mensagem': d['mensagem'],
                    'timestamp': d['timestamp'].isoformat()
                }
                for d in self.detalhes_validacao
            ]
        }


    def _serializar_dados(self, dados: dict) -> dict:
        """Converte Decimal para float para JSON (recursivo)."""
        resultado = {}
        for k, v in dados.items():
            if isinstance(v, Decimal):
                resultado[k] = float(v)
            elif isinstance(v, list):
                # Tratar listas (ex: duplicatas)
                resultado[k] = [
                    self._serializar_item(item) for item in v
                ]
            elif isinstance(v, dict):
                # Tratar dicts aninhados
                resultado[k] = self._serializar_dados(v)
            else:
                resultado[k] = v
        return resultado


    def _serializar_item(self, item):
        """Serializa um item individual (dict, Decimal, ou outro)."""
        if isinstance(item, dict):
            return self._serializar_dados(item)
        elif isinstance(item, Decimal):
            return float(item)
        else:
            return item


class AuditoriaExecucao:
    """
    Representa a auditoria completa de uma execução do sistema.
    """

    def __init__(self, modo: str = "preview"):
        self.execucao_id = self._gerar_id()
        self.timestamp_inicio = datetime.now()
        self.timestamp_fim = None
        self.duracao_segundos = 0
        self.modo = modo
        self.versao = "6.0.0 (XML-Based)"

        # Contadores
        self.total_boletos = 0
        self.aprovados = 0
        self.rejeitados = 0
        self.emails_enviados = 0

        # Estatísticas de validação
        self.stats_validacoes = {
            'xml': {'sucesso': 0, 'falha': 0},
            'cnpj': {'sucesso': 0, 'falha': 0},
            'nome': {'sucesso': 0, 'falha': 0},
            'valor': {'sucesso': 0, 'falha': 0},
            'email': {'sucesso': 0, 'falha': 0}
        }

        # Estatísticas de matching
        self.stats_matching = {
            'cnpj_valor': 0,
            'nome_valor': 0,
            'fuzzy': 0,
            'nao_encontrado': 0
        }

        # Boletos processados
        self.boletos: List[BoletoAuditoria] = []

        # Erros críticos
        self.erros_criticos = []

        # Avisos
        self.avisos = []

        # Checksum (para integridade)
        self.checksum_boletos = None
        self.checksum_xmls = None


    def _gerar_id(self) -> str:
        """Gera ID único para a execução."""
        now = datetime.now()
        return now.strftime("%Y%m%d_%H%M%S")


    def adicionar_boleto(self, boleto: BoletoAuditoria):
        """Adiciona um boleto à auditoria."""
        self.boletos.append(boleto)
        self.total_boletos += 1

        if boleto.status == "aprovado":
            self.aprovados += 1
        elif boleto.status == "rejeitado":
            self.rejeitados += 1


    def adicionar_erro_critico(self, mensagem: str, boleto: str = None):
        """Adiciona um erro crítico."""
        self.erros_criticos.append({
            'timestamp': datetime.now(),
            'mensagem': mensagem,
            'boleto': boleto
        })


    def adicionar_aviso(self, mensagem: str, boleto: str = None):
        """Adiciona um aviso."""
        self.avisos.append({
            'timestamp': datetime.now(),
            'mensagem': mensagem,
            'boleto': boleto
        })


    def finalizar(self):
        """Finaliza a execução e calcula métricas."""
        self.timestamp_fim = datetime.now()
        self.duracao_segundos = (self.timestamp_fim - self.timestamp_inicio).total_seconds()

        # Calcular checksums
        self.checksum_boletos = self._calcular_checksum_boletos()


    def _calcular_checksum_boletos(self) -> str:
        """Calcula SHA256 dos nomes dos boletos processados."""
        if not self.boletos:
            return ""

        nomes = sorted([b.arquivo for b in self.boletos])
        texto = "|".join(nomes)
        return hashlib.sha256(texto.encode()).hexdigest()[:16]


    def get_taxa_sucesso(self) -> float:
        """Calcula taxa de sucesso."""
        if self.total_boletos == 0:
            return 0.0
        return self.aprovados / self.total_boletos


    def to_dict(self) -> dict:
        """Converte para dicionário (para JSON)."""
        return {
            'execucao_id': self.execucao_id,
            'timestamp_inicio': self.timestamp_inicio.isoformat(),
            'timestamp_fim': self.timestamp_fim.isoformat() if self.timestamp_fim else None,
            'duracao_segundos': self.duracao_segundos,
            'modo': self.modo,
            'versao': self.versao,
            'resumo': {
                'total_boletos': self.total_boletos,
                'aprovados': self.aprovados,
                'rejeitados': self.rejeitados,
                'emails_enviados': self.emails_enviados,
                'taxa_sucesso': self.get_taxa_sucesso()
            },
            'stats_validacoes': self.stats_validacoes,
            'stats_matching': self.stats_matching,
            'boletos': [b.to_dict() for b in self.boletos],
            'erros_criticos': [
                {
                    'timestamp': e['timestamp'].isoformat(),
                    'mensagem': e['mensagem'],
                    'boleto': e.get('boleto')
                }
                for e in self.erros_criticos
            ],
            'avisos': [
                {
                    'timestamp': a['timestamp'].isoformat(),
                    'mensagem': a['mensagem'],
                    'boleto': a.get('boleto')
                }
                for a in self.avisos
            ],
            'checksums': {
                'boletos': self.checksum_boletos,
                'xmls': self.checksum_xmls
            }
        }


# ==================== GERAÇÃO DE RELATÓRIOS ====================

def gerar_relatorio_aprovados(auditoria: AuditoriaExecucao, pasta_auditoria: str) -> str:
    """
    Gera relatório de auditoria APENAS com boletos APROVADOS e ENVIADOS.

    Este relatório é para registro de conformidade e auditoria fiscal.
    Contém apenas os boletos que foram efetivamente enviados com sucesso.

    Returns:
        Caminho do arquivo gerado (ou None se nenhum boleto aprovado)
    """
    # Filtrar apenas boletos aprovados
    boletos_aprovados = [b for b in auditoria.boletos if b.status == "aprovado" and b.email_enviado]

    if not boletos_aprovados:
        return None  # Não gera relatório se não houver aprovados

    nome_arquivo = f"auditoria_aprovados_{auditoria.execucao_id}.txt"
    caminho = os.path.join(pasta_auditoria, nome_arquivo)

    with open(caminho, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("=" * 80 + "\n")
        f.write("AUDITORIA - BOLETOS ENVIADOS COM SUCESSO\n")
        f.write("=" * 80 + "\n")
        f.write(f"Execucao ID: {auditoria.execucao_id}\n")
        f.write(f"Data/Hora: {auditoria.timestamp_inicio.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Modo: {auditoria.modo.upper()}\n")
        f.write(f"Versao: {auditoria.versao}\n")
        f.write("=" * 80 + "\n\n")

        # Resumo
        f.write("RESUMO:\n")
        f.write(f"- Total de boletos enviados: {len(boletos_aprovados)}\n")
        f.write(f"- Taxa de sucesso: {auditoria.get_taxa_sucesso():.1%}\n\n")

        f.write("=" * 80 + "\n")
        f.write("BOLETOS ENVIADOS\n")
        f.write("=" * 80 + "\n\n")

        # Detalhes de cada boleto aprovado
        for i, boleto in enumerate(boletos_aprovados, 1):
            f.write(f"[{i:03d}/{len(boletos_aprovados):03d}] {boleto.arquivo}\n")
            f.write(f"  Timestamp: {boleto.timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"  Status: ✓ ENVIADO COM SUCESSO\n")

            f.write("\n  Validacoes Aprovadas:\n")
            for detalhe in boleto.detalhes_validacao:
                if detalhe['sucesso']:
                    f.write(f"    ✓ {detalhe['camada']}: {detalhe['mensagem']}\n")

            if boleto.dados_xml:
                f.write("\n  Dados do XML:\n")
                for k, v in boleto.dados_xml.items():
                    f.write(f"    - {k}: {v}\n")

            f.write("\n  Email Enviado:\n")
            f.write(f"    Para: {'; '.join(boleto.email_destinatarios)}\n")
            f.write(f"    CC: {'; '.join(boleto.email_cc)}\n")
            f.write(f"    Anexos: {boleto.anexos_count}\n")

            f.write("\n" + "-" * 80 + "\n\n")

        # Rodapé
        f.write("=" * 80 + "\n")
        f.write("FIM DO RELATORIO DE AUDITORIA\n")
        f.write("=" * 80 + "\n")
        f.write(f"Gerado automaticamente pelo Sistema de Envio de Boletos v{auditoria.versao}\n")

    return caminho


def gerar_relatorio_rejeitados(auditoria: AuditoriaExecucao, pasta_erros: str) -> str:
    """
    Gera relatório APENAS com boletos REJEITADOS.

    Este relatório é para troubleshooting e correção de erros.
    Contém apenas os boletos que falharam nas validações.

    Returns:
        Caminho do arquivo gerado (ou None se nenhum boleto rejeitado)
    """
    # Filtrar apenas boletos rejeitados
    boletos_rejeitados = [b for b in auditoria.boletos if b.status == "rejeitado"]

    if not boletos_rejeitados:
        return None  # Não gera relatório se não houver rejeitados

    nome_arquivo = f"erros_{auditoria.execucao_id}.txt"
    caminho = os.path.join(pasta_erros, nome_arquivo)

    with open(caminho, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("=" * 80 + "\n")
        f.write("RELATORIO DE ERROS - BOLETOS REJEITADOS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Execucao ID: {auditoria.execucao_id}\n")
        f.write(f"Data/Hora: {auditoria.timestamp_inicio.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Modo: {auditoria.modo.upper()}\n")
        f.write(f"Versao: {auditoria.versao}\n")
        f.write("=" * 80 + "\n\n")

        # Resumo
        f.write("RESUMO:\n")
        f.write(f"- Total de boletos rejeitados: {len(boletos_rejeitados)}\n")
        f.write(f"- Total processados: {auditoria.total_boletos}\n")
        f.write(f"- Taxa de falha: {auditoria.rejeitados/auditoria.total_boletos:.1%}\n\n")

        f.write("=" * 80 + "\n")
        f.write("BOLETOS REJEITADOS\n")
        f.write("=" * 80 + "\n\n")

        # Detalhes de cada boleto rejeitado
        for i, boleto in enumerate(boletos_rejeitados, 1):
            f.write(f"[{i:03d}/{len(boletos_rejeitados):03d}] {boleto.arquivo}\n")
            f.write(f"  Timestamp: {boleto.timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"  Status: ✗ REJEITADO\n")
            f.write(f"  Motivo: {boleto.motivo_rejeicao}\n")

            f.write("\n  Validacoes:\n")
            for detalhe in boleto.detalhes_validacao:
                if detalhe['sucesso'] is False:
                    f.write(f"    ✗ {detalhe['camada']}: {detalhe['mensagem']}\n")
                elif detalhe['sucesso'] is True:
                    f.write(f"    ✓ {detalhe['camada']}: {detalhe['mensagem']}\n")
                else:
                    f.write(f"    ⚠ {detalhe['camada']}: {detalhe['mensagem']}\n")

            if boleto.dados_boleto:
                f.write("\n  Dados do Boleto:\n")
                for k, v in boleto.dados_boleto.items():
                    f.write(f"    - {k}: {v}\n")

            f.write("\n" + "-" * 80 + "\n\n")

        # Erros Críticos
        if auditoria.erros_criticos:
            f.write("=" * 80 + "\n")
            f.write("ERROS CRITICOS\n")
            f.write("=" * 80 + "\n\n")

            for i, erro in enumerate(auditoria.erros_criticos, 1):
                ts = erro['timestamp'].strftime('%H:%M:%S')
                boleto = f" - {erro['boleto']}" if erro.get('boleto') else ""
                f.write(f"{i}. [{ts}] {erro['mensagem']}{boleto}\n")
            f.write("\n")

        # Rodapé
        f.write("=" * 80 + "\n")
        f.write("FIM DO RELATORIO DE ERROS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Gerado automaticamente pelo Sistema de Envio de Boletos v{auditoria.versao}\n")

    return caminho


def gerar_relatorio_txt(auditoria: AuditoriaExecucao, pasta_auditoria: str) -> str:
    """
    [DEPRECATED] Gera relatório completo (manter para compatibilidade).
    Use gerar_relatorio_aprovados() e gerar_relatorio_rejeitados() separadamente.

    Returns:
        Caminho do arquivo gerado
    """
    nome_arquivo = f"relatorio_completo_{auditoria.execucao_id}.txt"
    caminho = os.path.join(pasta_auditoria, nome_arquivo)

    with open(caminho, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("=" * 80 + "\n")
        f.write("RELATORIO DE AUDITORIA - ENVIO DE BOLETOS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Execucao ID: {auditoria.execucao_id}\n")
        f.write(f"Data/Hora Inicio: {auditoria.timestamp_inicio.strftime('%d/%m/%Y %H:%M:%S')}\n")

        if auditoria.timestamp_fim:
            f.write(f"Data/Hora Fim: {auditoria.timestamp_fim.strftime('%d/%m/%Y %H:%M:%S')}\n")
            minutos = int(auditoria.duracao_segundos // 60)
            segundos = int(auditoria.duracao_segundos % 60)
            f.write(f"Duracao Total: {minutos}m {segundos}s\n")

        f.write(f"Operador: Sistema Automatico\n")
        f.write(f"Modo: {auditoria.modo.upper()}\n")
        f.write(f"Versao: {auditoria.versao}\n")
        f.write("=" * 80 + "\n\n")

        # Resumo Executivo
        f.write("RESUMO EXECUTIVO:\n")
        f.write(f"- Total de boletos processados: {auditoria.total_boletos}\n")
        f.write(f"- Emails enviados com sucesso: {auditoria.emails_enviados}\n")
        f.write(f"- Boletos aprovados: {auditoria.aprovados}\n")
        f.write(f"- Boletos rejeitados: {auditoria.rejeitados}\n")
        f.write(f"- Taxa de sucesso: {auditoria.get_taxa_sucesso():.1%}\n\n")

        # Estatísticas de Validações
        f.write("VALIDACOES REALIZADAS:\n")
        for tipo, stats in auditoria.stats_validacoes.items():
            total = stats['sucesso'] + stats['falha']
            if total > 0:
                f.write(f"- {tipo.upper()}: {total} ({stats['sucesso']} OK, {stats['falha']} FALHA)\n")
        f.write("\n")

        # Estatísticas de Matching
        f.write("ESTATISTICAS DE MATCHING:\n")
        f.write(f"- CNPJ + Valor: {auditoria.stats_matching['cnpj_valor']} boletos\n")
        f.write(f"- Nome + Valor: {auditoria.stats_matching['nome_valor']} boletos\n")
        f.write(f"- Fuzzy Match: {auditoria.stats_matching['fuzzy']} boletos\n")
        f.write(f"- Nao encontrados: {auditoria.stats_matching['nao_encontrado']} boletos\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("DETALHAMENTO POR BOLETO\n")
        f.write("=" * 80 + "\n\n")

        # Detalhes de cada boleto
        for i, boleto in enumerate(auditoria.boletos, 1):
            f.write(f"[{i:03d}/{auditoria.total_boletos:03d}] {boleto.arquivo}\n")
            f.write(f"  Timestamp: {boleto.timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n")

            if boleto.status == "aprovado":
                f.write(f"  Status: [OK] APROVADO\n")
            else:
                f.write(f"  Status: [X] REJEITADO\n")
                if boleto.motivo_rejeicao:
                    f.write(f"  Motivo: {boleto.motivo_rejeicao}\n")

            f.write("\n  Validacoes:\n")
            for detalhe in boleto.detalhes_validacao:
                status_icon = "[OK]" if detalhe['sucesso'] else "[X]"
                f.write(f"    {status_icon} {detalhe['camada']}: {detalhe['mensagem']}\n")

            if boleto.dados_xml:
                f.write("\n  Dados do XML:\n")
                for k, v in boleto.dados_xml.items():
                    f.write(f"    - {k}: {v}\n")

            if boleto.email_enviado:
                f.write("\n  Email Criado:\n")
                f.write(f"    Para: {'; '.join(boleto.email_destinatarios)}\n")
                f.write(f"    CC: {'; '.join(boleto.email_cc)}\n")
                f.write(f"    Anexos: {boleto.anexos_count}\n")
                f.write(f"    Resultado: [OK] Email enviado com sucesso\n")

            f.write("\n" + "-" * 80 + "\n\n")

        # Erros e Avisos
        if auditoria.erros_criticos or auditoria.avisos:
            f.write("=" * 80 + "\n")
            f.write("ERROS E AVISOS\n")
            f.write("=" * 80 + "\n\n")

            if auditoria.erros_criticos:
                f.write(f"ERROS CRITICOS ({len(auditoria.erros_criticos)}):\n")
                for i, erro in enumerate(auditoria.erros_criticos, 1):
                    ts = erro['timestamp'].strftime('%H:%M:%S')
                    boleto = f" - {erro['boleto']}" if erro.get('boleto') else ""
                    f.write(f"{i}. [{ts}] {erro['mensagem']}{boleto}\n")
                f.write("\n")

            if auditoria.avisos:
                f.write(f"AVISOS ({len(auditoria.avisos)}):\n")
                for i, aviso in enumerate(auditoria.avisos, 1):
                    ts = aviso['timestamp'].strftime('%H:%M:%S')
                    boleto = f" - {aviso['boleto']}" if aviso.get('boleto') else ""
                    f.write(f"{i}. [{ts}] {aviso['mensagem']}{boleto}\n")
                f.write("\n")

        # Rastreabilidade
        f.write("=" * 80 + "\n")
        f.write("RASTREABILIDADE\n")
        f.write("=" * 80 + "\n")
        f.write(f"Checksums (integridade):\n")
        f.write(f"- Boletos processados: {auditoria.checksum_boletos}\n")
        if auditoria.checksum_xmls:
            f.write(f"- XMLs lidos: {auditoria.checksum_xmls}\n")
        f.write("\n")

        # Rodapé
        f.write("=" * 80 + "\n")
        f.write("FIM DO RELATORIO\n")
        f.write("=" * 80 + "\n")
        f.write(f"Gerado automaticamente pelo Sistema de Envio de Boletos v{auditoria.versao}\n")

    return caminho


def gerar_relatorio_json(auditoria: AuditoriaExecucao, pasta_auditoria: str) -> str:
    """
    Gera relatório de auditoria em formato JSON estruturado.

    Returns:
        Caminho do arquivo gerado
    """
    nome_arquivo = f"auditoria_{auditoria.execucao_id}.json"
    caminho = os.path.join(pasta_auditoria, nome_arquivo)

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(auditoria.to_dict(), f, ensure_ascii=False, indent=2)

    return caminho


def gerar_log_erros_criticos(auditoria: AuditoriaExecucao, pasta_auditoria: str) -> str:
    """
    Gera log apenas com erros críticos (para troubleshooting rápido).

    Returns:
        Caminho do arquivo gerado (ou None se não houver erros)
    """
    if not auditoria.erros_criticos:
        return None

    data_str = auditoria.timestamp_inicio.strftime("%Y%m%d")
    nome_arquivo = f"erros_criticos_{data_str}.log"
    caminho = os.path.join(pasta_auditoria, nome_arquivo)

    # Append mode (acumula erros do dia)
    with open(caminho, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Execucao: {auditoria.execucao_id}\n")
        f.write(f"Timestamp: {auditoria.timestamp_inicio.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")

        for erro in auditoria.erros_criticos:
            ts = erro['timestamp'].strftime('%H:%M:%S')
            boleto = f" [{erro['boleto']}]" if erro.get('boleto') else ""
            f.write(f"[{ts}] {erro['mensagem']}{boleto}\n")

        f.write("\n")

    return caminho


# ==================== TESTE ====================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DO MODULO auditoria.py")
    print("=" * 80)
    print()

    # Criar auditoria de teste
    auditoria = AuditoriaExecucao(modo="preview")

    # Simular processamento de 2 boletos
    boleto1 = BoletoAuditoria("AREAIS DO LESTE SPE LTDA - 13-01 - R$ 2.833,34.pdf")
    boleto1.adicionar_detalhe("XML", True, "XML encontrado (3-0310227.xml)")
    boleto1.adicionar_detalhe("CNPJ", True, "Match perfeito: 54737141000110")
    boleto1.adicionar_detalhe("Nome", True, "Similaridade 100%")
    boleto1.adicionar_detalhe("Valor", True, "Diferenca R$ 0,01 (tolerancia)")
    boleto1.adicionar_detalhe("Email", True, "2 emails validos")
    boleto1.aprovar()
    boleto1.email_enviado = True
    boleto1.email_destinatarios = ["compras@dacampos.com.br"]
    boleto1.email_cc = ["adm@jotajota.net.br"]
    boleto1.anexos_count = 2
    auditoria.adicionar_boleto(boleto1)
    auditoria.emails_enviados += 1

    boleto2 = BoletoAuditoria("CLIENTE XYZ LTDA - 02-10 - R$ 1.445,54.pdf")
    boleto2.adicionar_detalhe("XML", True, "XML encontrado")
    boleto2.adicionar_detalhe("CNPJ", False, "CNPJ divergente!")
    boleto2.rejeitar("CNPJ divergente entre boleto e XML")
    auditoria.adicionar_boleto(boleto2)
    auditoria.adicionar_erro_critico("CNPJ divergente", boleto2.arquivo)

    auditoria.finalizar()

    # Gerar relatórios em pasta temporária
    pasta_teste = "."

    print("Gerando relatorios de teste...")
    txt_path = gerar_relatorio_txt(auditoria, pasta_teste)
    json_path = gerar_relatorio_json(auditoria, pasta_teste)
    erros_path = gerar_log_erros_criticos(auditoria, pasta_teste)

    print(f"[OK] Relatorio TXT: {txt_path}")
    print(f"[OK] Relatorio JSON: {json_path}")
    print(f"[OK] Log de erros: {erros_path}")
    print()
    print("=" * 80)
    print("TESTE CONCLUIDO")
    print("=" * 80)
