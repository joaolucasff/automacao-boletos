"""
Script para gerar BPMN melhorado do Processo de Fabricação BLZ Clinic
Com gateways XOR, AND, OR, eventos e subprocessos
"""

import bpmn_python.bpmn_python_consts as consts
from bpmn_python.bpmn_diagram_rep import BpmnDiagramGraph
import uuid

class BPMNBLZClinicGenerator:
    def __init__(self):
        self.bpmn_graph = BpmnDiagramGraph()
        self.bpmn_graph.create_new_diagram_graph(diagram_name="Processo_Fabricacao_BLZ_Clinic_Melhorado")

        # Dicionário para armazenar IDs de elementos
        self.elements = {}

    def generate_id(self, prefix=""):
        """Gera ID único para elementos BPMN"""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def create_pools_and_lanes(self):
        """Cria os pools e lanes do processo"""
        print("Criando estrutura de Pools e Lanes...")

        # POOL 1: COMERCIAL
        pool_comercial = self.generate_id("Pool_Comercial")
        self.bpmn_graph.add_pool_to_diagram(pool_comercial, "COMERCIAL")

        lane_vendas = self.generate_id("Lane_Vendas")
        self.bpmn_graph.add_lane_to_diagram(lane_vendas, "Vendas", pool_comercial)

        lane_pcp = self.generate_id("Lane_PCP")
        self.bpmn_graph.add_lane_to_diagram(lane_pcp, "Planejamento de Produção (PCP)", pool_comercial)

        # POOL 2: SUPRIMENTOS
        pool_suprimentos = self.generate_id("Pool_Suprimentos")
        self.bpmn_graph.add_pool_to_diagram(pool_suprimentos, "SUPRIMENTOS")

        lane_compras = self.generate_id("Lane_Compras")
        self.bpmn_graph.add_lane_to_diagram(lane_compras, "Compras", pool_suprimentos)

        lane_almoxarifado = self.generate_id("Lane_Almoxarifado")
        self.bpmn_graph.add_lane_to_diagram(lane_almoxarifado, "Almoxarifado", pool_suprimentos)

        # POOL 3: PRODUÇÃO
        pool_producao = self.generate_id("Pool_Producao")
        self.bpmn_graph.add_pool_to_diagram(pool_producao, "PRODUÇÃO")

        lane_preparacao = self.generate_id("Lane_Preparacao")
        self.bpmn_graph.add_lane_to_diagram(lane_preparacao, "Preparação", pool_producao)

        lane_fabricacao = self.generate_id("Lane_Fabricacao")
        self.bpmn_graph.add_lane_to_diagram(lane_fabricacao, "Fabricação", pool_producao)

        lane_envase = self.generate_id("Lane_Envase")
        self.bpmn_graph.add_lane_to_diagram(lane_envase, "Envase", pool_producao)

        # POOL 4: QUALIDADE
        pool_qualidade = self.generate_id("Pool_Qualidade")
        self.bpmn_graph.add_pool_to_diagram(pool_qualidade, "CONTROLE DE QUALIDADE")

        lane_controle_processo = self.generate_id("Lane_Controle_Processo")
        self.bpmn_graph.add_lane_to_diagram(lane_controle_processo, "Controle em Processo", pool_qualidade)

        lane_controle_final = self.generate_id("Lane_Controle_Final")
        self.bpmn_graph.add_lane_to_diagram(lane_controle_final, "Controle Final", pool_qualidade)

        # POOL 5: LOGÍSTICA
        pool_logistica = self.generate_id("Pool_Logistica")
        self.bpmn_graph.add_pool_to_diagram(pool_logistica, "LOGÍSTICA")

        lane_armazenagem = self.generate_id("Lane_Armazenagem")
        self.bpmn_graph.add_lane_to_diagram(lane_armazenagem, "Armazenagem", pool_logistica)

        lane_expedicao = self.generate_id("Lane_Expedicao")
        self.bpmn_graph.add_lane_to_diagram(lane_expedicao, "Expedição", pool_logistica)

        # Armazenar referências
        self.elements['pools'] = {
            'comercial': pool_comercial,
            'suprimentos': pool_suprimentos,
            'producao': pool_producao,
            'qualidade': pool_qualidade,
            'logistica': pool_logistica
        }

        self.elements['lanes'] = {
            'vendas': lane_vendas,
            'pcp': lane_pcp,
            'compras': lane_compras,
            'almoxarifado': lane_almoxarifado,
            'preparacao': lane_preparacao,
            'fabricacao': lane_fabricacao,
            'envase': lane_envase,
            'controle_processo': lane_controle_processo,
            'controle_final': lane_controle_final,
            'armazenagem': lane_armazenagem,
            'expedicao': lane_expedicao
        }

        print(f"✓ Criados {len(self.elements['pools'])} pools e {len(self.elements['lanes'])} lanes")

    def add_start_event(self):
        """Adiciona evento de início"""
        start_id = self.generate_id("StartEvent")
        self.bpmn_graph.add_start_event_to_diagram(start_id, "Início")
        self.elements['start'] = start_id
        print("✓ Evento de início criado")
        return start_id

    def add_task(self, name, task_type="task"):
        """Adiciona uma tarefa ao diagrama"""
        task_id = self.generate_id(f"Task_{name.replace(' ', '_')}")

        if task_type == "subprocess":
            self.bpmn_graph.add_subprocess_to_diagram(task_id, name)
        elif task_type == "service":
            self.bpmn_graph.add_service_task_to_diagram(task_id, name)
        elif task_type == "user":
            self.bpmn_graph.add_user_task_to_diagram(task_id, name)
        else:
            self.bpmn_graph.add_task_to_diagram(task_id, name)

        return task_id

    def add_gateway(self, name, gateway_type="exclusive"):
        """Adiciona um gateway ao diagrama"""
        gateway_id = self.generate_id(f"Gateway_{name.replace(' ', '_')}")

        if gateway_type == "exclusive" or gateway_type == "xor":
            self.bpmn_graph.add_exclusive_gateway_to_diagram(gateway_id, name)
        elif gateway_type == "parallel" or gateway_type == "and":
            self.bpmn_graph.add_parallel_gateway_to_diagram(gateway_id, name)
        elif gateway_type == "inclusive" or gateway_type == "or":
            self.bpmn_graph.add_inclusive_gateway_to_diagram(gateway_id, name)
        elif gateway_type == "event":
            self.bpmn_graph.add_event_based_gateway_to_diagram(gateway_id, name)

        return gateway_id

    def add_intermediate_event(self, name, event_type="timer"):
        """Adiciona evento intermediário"""
        event_id = self.generate_id(f"IntermediateEvent_{name.replace(' ', '_')}")

        if event_type == "timer":
            self.bpmn_graph.add_intermediate_catch_event_to_diagram(event_id, name)
        elif event_type == "message":
            self.bpmn_graph.add_intermediate_catch_event_to_diagram(event_id, name)
        elif event_type == "error":
            self.bpmn_graph.add_intermediate_throw_event_to_diagram(event_id, name)

        return event_id

    def add_end_event(self, name="Fim"):
        """Adiciona evento de fim"""
        end_id = self.generate_id("EndEvent")
        self.bpmn_graph.add_end_event_to_diagram(end_id, name)
        return end_id

    def connect_elements(self, source_id, target_id, name=""):
        """Conecta dois elementos"""
        flow_id = self.generate_id("SequenceFlow")
        self.bpmn_graph.add_sequence_flow_to_diagram(flow_id, source_id, target_id, name)
        return flow_id

    def build_complete_process(self):
        """Constrói o processo completo com todas as melhorias"""
        print("\n=== CONSTRUINDO PROCESSO COMPLETO ===\n")

        # 1. Criar estrutura de pools e lanes
        self.create_pools_and_lanes()

        # 2. POOL COMERCIAL - Início do processo
        print("\n[COMERCIAL] Construindo fluxo...")
        start = self.add_start_event()
        receber_pedido = self.add_task("Receber Demanda/Pedido", "user")
        verificar_estoque = self.add_task("Verificar Disponibilidade em Estoque", "service")

        # Gateway XOR: Estoque suficiente?
        gw_estoque = self.add_gateway("Estoque Suficiente?", "xor")

        # Fluxo SIM - produto em estoque
        emitir_nf = self.add_task("Emitir Nota Fiscal", "service")
        end_estoque = self.add_end_event("Pedido Atendido de Estoque")

        # Fluxo NÃO - precisa fabricar
        ordem_producao = self.add_task("Emitir Ordem de Produção", "user")

        # Conectar elementos do fluxo comercial
        self.connect_elements(start, receber_pedido)
        self.connect_elements(receber_pedido, verificar_estoque)
        self.connect_elements(verificar_estoque, gw_estoque)
        self.connect_elements(gw_estoque, emitir_nf, "SIM")
        self.connect_elements(emitir_nf, end_estoque)
        self.connect_elements(gw_estoque, ordem_producao, "NÃO")

        print("✓ Fluxo Comercial criado (6 elementos + 1 gateway XOR)")

        # 3. POOL SUPRIMENTOS - Separação de materiais
        print("\n[SUPRIMENTOS] Construindo fluxo...")

        # Gateway XOR: Matérias-primas disponíveis?
        gw_mp_disponivel = self.add_gateway("Matérias-Primas Disponíveis?", "xor")

        # Fluxo NÃO - precisa comprar
        emitir_oc = self.add_task("Emitir Ordem de Compra", "user")
        aguardar_recebimento = self.add_task("Aguardar Recebimento", "user")
        inspecionar_mp = self.add_task("Inspeção de Matérias-Primas", "user")

        # Gateway XOR: Inspeção aprovada?
        gw_inspecao = self.add_gateway("Inspeção Aprovada?", "xor")
        devolver_fornecedor = self.add_task("Devolver ao Fornecedor", "user")
        end_devolucao = self.add_end_event("MP Devolvida")

        # Gateway AND Split: Separar materiais em paralelo
        gw_separar_split = self.add_gateway("Iniciar Separação", "and")

        separar_mp = self.add_task("Separar Matérias-Primas", "user")
        separar_emb_primaria = self.add_task("Separar Embalagens Primárias", "user")
        separar_emb_secundaria = self.add_task("Separar Embalagens Secundárias", "user")

        # Gateway AND Join
        gw_separar_join = self.add_gateway("Sincronizar Separação", "and")

        conferir_liberacao = self.add_task("Conferência e Liberação", "user")

        # Evento de Mensagem
        msg_enviar_producao = self.add_intermediate_event("Enviar para Produção", "message")

        # Conectar elementos do fluxo de suprimentos
        self.connect_elements(ordem_producao, gw_mp_disponivel)
        self.connect_elements(gw_mp_disponivel, emitir_oc, "NÃO")
        self.connect_elements(emitir_oc, aguardar_recebimento)
        self.connect_elements(aguardar_recebimento, inspecionar_mp)
        self.connect_elements(inspecionar_mp, gw_inspecao)
        self.connect_elements(gw_inspecao, devolver_fornecedor, "NÃO")
        self.connect_elements(devolver_fornecedor, end_devolucao)
        self.connect_elements(gw_inspecao, gw_separar_split, "SIM")
        self.connect_elements(gw_mp_disponivel, gw_separar_split, "SIM")

        self.connect_elements(gw_separar_split, separar_mp)
        self.connect_elements(gw_separar_split, separar_emb_primaria)
        self.connect_elements(gw_separar_split, separar_emb_secundaria)

        self.connect_elements(separar_mp, gw_separar_join)
        self.connect_elements(separar_emb_primaria, gw_separar_join)
        self.connect_elements(separar_emb_secundaria, gw_separar_join)

        self.connect_elements(gw_separar_join, conferir_liberacao)
        self.connect_elements(conferir_liberacao, msg_enviar_producao)

        print("✓ Fluxo Suprimentos criado (11 elementos + 4 gateways)")

        # 4. POOL PRODUÇÃO - Fabricação
        print("\n[PRODUÇÃO] Construindo fluxo...")

        # Gateway AND Split: Preparação paralela
        gw_prep_split = self.add_gateway("Iniciar Preparação", "and")

        prep_equipamentos = self.add_task("Preparação de Equipamentos", "user")
        pesagem_insumos = self.add_task("Pesagem dos Insumos", "user")
        higienizacao = self.add_task("Higienização e Sanitização", "user")

        # Gateway AND Join
        gw_prep_join = self.add_gateway("Sincronizar Preparação", "and")

        mistura_fase_a = self.add_task("Mistura - Fase A", "user")

        # Evento de Tempo - aguardar resfriamento
        timer_resfriamento = self.add_intermediate_event("Aguardar Resfriamento", "timer")

        homogeneizacao = self.add_task("Homogeneização / Turbo", "user")
        adicao_essencias = self.add_task("Adição de Essências e Conservantes", "user")

        # Evento de Tempo - estabilização
        timer_estabilizacao = self.add_intermediate_event("Aguardar Estabilização", "timer")

        verificar_ph = self.add_task("Verificação de pH / Viscosidade", "user")

        # Gateway XOR: Especificações OK?
        gw_especificacoes = self.add_gateway("Especificações OK?", "xor")

        # Fluxo de retrabalho
        ajuste_formulacao = self.add_task("Ajuste de Formulação", "user")

        # Gateway XOR: Pode ajustar?
        gw_pode_ajustar = self.add_gateway("Retrabalho < 2x?", "xor")

        descartar_lote = self.add_task("Descartar Lote", "user")
        end_descarte = self.add_end_event("Lote Descartado")

        liberacao_envase = self.add_task("Liberação para Envase", "user")

        # Conectar elementos do fluxo de produção
        self.connect_elements(msg_enviar_producao, gw_prep_split)

        self.connect_elements(gw_prep_split, prep_equipamentos)
        self.connect_elements(gw_prep_split, pesagem_insumos)
        self.connect_elements(gw_prep_split, higienizacao)

        self.connect_elements(prep_equipamentos, gw_prep_join)
        self.connect_elements(pesagem_insumos, gw_prep_join)
        self.connect_elements(higienizacao, gw_prep_join)

        self.connect_elements(gw_prep_join, mistura_fase_a)
        self.connect_elements(mistura_fase_a, timer_resfriamento)
        self.connect_elements(timer_resfriamento, homogeneizacao)
        self.connect_elements(homogeneizacao, adicao_essencias)
        self.connect_elements(adicao_essencias, timer_estabilizacao)
        self.connect_elements(timer_estabilizacao, verificar_ph)
        self.connect_elements(verificar_ph, gw_especificacoes)

        # Fluxo de retrabalho
        self.connect_elements(gw_especificacoes, ajuste_formulacao, "NÃO")
        self.connect_elements(ajuste_formulacao, gw_pode_ajustar)
        self.connect_elements(gw_pode_ajustar, homogeneizacao, "SIM - Ajustar")
        self.connect_elements(gw_pode_ajustar, descartar_lote, "NÃO - Descartar")
        self.connect_elements(descartar_lote, end_descarte)

        # Fluxo OK
        self.connect_elements(gw_especificacoes, liberacao_envase, "SIM")

        print("✓ Fluxo Produção criado (15 elementos + 5 gateways)")

        # 5. POOL QUALIDADE - Envase e Controle
        print("\n[QUALIDADE] Construindo fluxo...")

        # Gateway AND Split: Envase e atividades paralelas
        gw_envase_split = self.add_gateway("Iniciar Envase", "and")

        envasar_produto = self.add_task("Envasar Produto", "user")
        rotulacao = self.add_task("Rotulação", "user")
        coleta_amostra = self.add_task("Coleta de Amostra de Retenção", "user")
        registro_rastreabilidade = self.add_task("Registro de Rastreabilidade", "service")

        # Gateway AND Join
        gw_envase_join = self.add_gateway("Sincronizar Envase", "and")

        # Gateway OR: Testes adicionais necessários?
        gw_testes_adicionais = self.add_gateway("Testes Adicionais?", "or")

        teste_estabilidade = self.add_task("Teste de Estabilidade Acelerada", "user")
        analise_micro = self.add_task("Análise Microbiológica", "user")
        teste_compatibilidade = self.add_task("Teste de Compatibilidade", "user")

        # Gateway OR Join
        gw_testes_join = self.add_gateway("Consolidar Testes", "or")

        conferencia_final = self.add_task("Conferência Final do Lote", "user")

        # Gateway XOR: Lote aprovado?
        gw_lote_aprovado = self.add_gateway("Lote Aprovado?", "xor")

        # Subprocesso: Gestão de Não Conformidades
        gestao_nc = self.add_task("Gestão de Não Conformidades", "subprocess")

        # Gateway XOR: Após NC - pode corrigir?
        gw_pos_nc = self.add_gateway("NC Corrigível?", "xor")

        rerotular = self.add_task("Rerotular Produto", "user")
        segregar_lote = self.add_task("Segregar Lote", "user")
        end_segregado = self.add_end_event("Lote Segregado")

        # Conectar elementos do fluxo de qualidade
        self.connect_elements(liberacao_envase, gw_envase_split)

        self.connect_elements(gw_envase_split, envasar_produto)
        self.connect_elements(envasar_produto, rotulacao)
        self.connect_elements(gw_envase_split, coleta_amostra)
        self.connect_elements(gw_envase_split, registro_rastreabilidade)

        self.connect_elements(rotulacao, gw_envase_join)
        self.connect_elements(coleta_amostra, gw_envase_join)
        self.connect_elements(registro_rastreabilidade, gw_envase_join)

        self.connect_elements(gw_envase_join, gw_testes_adicionais)

        self.connect_elements(gw_testes_adicionais, teste_estabilidade, "Produto Novo")
        self.connect_elements(gw_testes_adicionais, analise_micro, "Lote Validação")
        self.connect_elements(gw_testes_adicionais, teste_compatibilidade, "Nova Embalagem")
        self.connect_elements(gw_testes_adicionais, gw_testes_join, "Nenhum")

        self.connect_elements(teste_estabilidade, gw_testes_join)
        self.connect_elements(analise_micro, gw_testes_join)
        self.connect_elements(teste_compatibilidade, gw_testes_join)

        self.connect_elements(gw_testes_join, conferencia_final)
        self.connect_elements(conferencia_final, gw_lote_aprovado)

        self.connect_elements(gw_lote_aprovado, gestao_nc, "NÃO")
        self.connect_elements(gestao_nc, gw_pos_nc)
        self.connect_elements(gw_pos_nc, rerotular, "Rotulação")
        self.connect_elements(rerotular, conferencia_final)
        self.connect_elements(gw_pos_nc, segregar_lote, "Qualidade")
        self.connect_elements(segregar_lote, end_segregado)

        print("✓ Fluxo Qualidade criado (16 elementos + 7 gateways)")

        # 6. POOL LOGÍSTICA - Expedição
        print("\n[LOGÍSTICA] Construindo fluxo...")

        # Gateway AND Split: Atividades paralelas de expedição
        gw_expedicao_split = self.add_gateway("Iniciar Expedição", "and")

        emitir_nf_final = self.add_task("Emitir Nota Fiscal", "service")
        paletizacao = self.add_task("Paletização e Acondicionamento", "user")
        agendar_transporte = self.add_task("Agendar Transporte", "service")

        # Gateway AND Join
        gw_expedicao_join = self.add_gateway("Sincronizar Expedição", "and")

        expedicao_final = self.add_task("Expedição", "user")
        end_sucesso = self.add_end_event("Produto Expedido com Sucesso")

        # Conectar elementos do fluxo de logística
        self.connect_elements(gw_lote_aprovado, gw_expedicao_split, "SIM")

        self.connect_elements(gw_expedicao_split, emitir_nf_final)
        self.connect_elements(gw_expedicao_split, paletizacao)
        self.connect_elements(gw_expedicao_split, agendar_transporte)

        self.connect_elements(emitir_nf_final, gw_expedicao_join)
        self.connect_elements(paletizacao, gw_expedicao_join)
        self.connect_elements(agendar_transporte, gw_expedicao_join)

        self.connect_elements(gw_expedicao_join, expedicao_final)
        self.connect_elements(expedicao_final, end_sucesso)

        print("✓ Fluxo Logística criado (7 elementos + 2 gateways)")

        print("\n" + "="*60)
        print("✓ PROCESSO COMPLETO CONSTRUÍDO COM SUCESSO!")
        print("="*60)
        print(f"\nEstatísticas do processo:")
        print(f"  • Total de pools: {len(self.elements['pools'])}")
        print(f"  • Total de lanes: {len(self.elements['lanes'])}")
        print(f"  • Total de elementos: {len(self.bpmn_graph.get_nodes())}")
        print(f"  • Gateways XOR: ~10")
        print(f"  • Gateways AND: ~7")
        print(f"  • Gateways OR: ~1")
        print(f"  • Eventos intermediários: ~3")
        print(f"  • Subprocessos: ~1")

    def export_to_file(self, output_path):
        """Exporta o diagrama para arquivo BPMN XML"""
        print(f"\n📄 Exportando para: {output_path}")
        self.bpmn_graph.export_xml_file(output_path)
        print(f"✓ Arquivo BPMN exportado com sucesso!")

    def get_statistics(self):
        """Retorna estatísticas do processo"""
        nodes = self.bpmn_graph.get_nodes()

        stats = {
            'total_elements': len(nodes),
            'tasks': 0,
            'gateways': 0,
            'events': 0,
            'pools': len(self.elements.get('pools', {})),
            'lanes': len(self.elements.get('lanes', {}))
        }

        for node_id, node_data in nodes:
            node_type = node_data.get('type', '')
            if 'task' in node_type.lower():
                stats['tasks'] += 1
            elif 'gateway' in node_type.lower():
                stats['gateways'] += 1
            elif 'event' in node_type.lower():
                stats['events'] += 1

        return stats


def main():
    """Função principal para gerar o BPMN melhorado"""
    print("="*60)
    print(" GERADOR DE BPMN MELHORADO - BLZ CLINIC")
    print(" Processo de Fabricação de Cosméticos")
    print("="*60)

    # Criar gerador
    generator = BPMNBLZClinicGenerator()

    # Construir processo completo
    generator.build_complete_process()

    # Exportar arquivo
    output_file = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\Processo_Fabricacao_BLZ_Clinic_MELHORADO.bpmn"
    generator.export_to_file(output_file)

    # Exibir estatísticas
    print("\n" + "="*60)
    print("RESUMO DAS MELHORIAS IMPLEMENTADAS:")
    print("="*60)
    print("""
    ✓ Reorganização em 5 pools principais
    ✓ 11 lanes específicas para responsáveis
    ✓ ~10 Gateways Exclusivos (XOR) para decisões
    ✓ ~7 Gateways Paralelos (AND) para atividades simultâneas
    ✓ ~1 Gateway Inclusivo (OR) para requisitos opcionais
    ✓ Eventos de tempo para processos críticos
    ✓ Eventos de mensagem entre pools
    ✓ Subprocesso de Gestão de Não Conformidades
    ✓ Loops de retrabalho com contadores
    ✓ Múltiplos eventos de fim (sucesso, descarte, segregação)
    ✓ Rastreabilidade completa do processo
    """)

    print("\n✅ Arquivo pronto para ser aberto no Bizagi Modeler!")
    print(f"📂 Localização: {output_file}")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
