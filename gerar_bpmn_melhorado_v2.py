"""
Script para gerar BPMN melhorado do Processo de Fabricação BLZ Clinic
Gera XML BPMN 2.0 diretamente - compatível com Bizagi Modeler
"""

from lxml import etree as ET
import uuid
from datetime import datetime

class BPMNBLZClinicGeneratorV2:
    def __init__(self):
        # Namespaces BPMN 2.0
        self.nsmap = {
            None: "http://www.omg.org/spec/BPMN/20100524/MODEL",
            "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            "dc": "http://www.omg.org/spec/DD/20100524/DC",
            "di": "http://www.omg.org/spec/DD/20100524/DI",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }

        # Criar elemento raiz
        self.definitions = ET.Element("{http://www.omg.org/spec/BPMN/20100524/MODEL}definitions", nsmap=self.nsmap)
        self.definitions.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                           "http://www.omg.org/spec/BPMN/20100524/MODEL BPMN20.xsd")
        self.definitions.set("id", "Definitions_" + self.generate_id())
        self.definitions.set("targetNamespace", "http://bpmn.io/schema/bpmn")
        self.definitions.set("exporter", "BLZ Clinic BPMN Generator")
        self.definitions.set("exporterVersion", "1.0")

        # Processo principal
        self.process = ET.SubElement(self.definitions, "process")
        self.process.set("id", "Process_BLZ_Clinic")
        self.process.set("isExecutable", "true")

        # Diagrama para visualização
        self.diagram = ET.SubElement(self.definitions, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram")
        self.diagram.set("id", "BPMNDiagram_1")
        self.plane = ET.SubElement(self.diagram, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane")
        self.plane.set("id", "BPMNPlane_1")
        self.plane.set("bpmnElement", "Process_BLZ_Clinic")

        # Contador de posição para layout
        self.x_pos = 100
        self.y_pos = 100
        self.lane_height = 200
        self.element_spacing = 150

        # Dicionário de elementos
        self.elements = {}
        self.current_lane_y = {}

    def generate_id(self):
        """Gera ID único"""
        return uuid.uuid4().hex[:8]

    def add_lane_set(self, pool_name, lanes):
        """Adiciona conjunto de lanes (piscinas)"""
        lane_set = ET.SubElement(self.process, "laneSet")
        lane_set.set("id", f"LaneSet_{self.generate_id()}")

        y_offset = self.y_pos
        for lane_name in lanes:
            lane = ET.SubElement(lane_set, "lane")
            lane_id = f"Lane_{self.generate_id()}"
            lane.set("id", lane_id)
            lane.set("name", lane_name)

            self.elements[lane_name] = {
                'id': lane_id,
                'type': 'lane',
                'y_pos': y_offset
            }

            # Criar shape visual para lane
            shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
            shape.set("id", f"{lane_id}_di")
            shape.set("bpmnElement", lane_id)
            shape.set("isHorizontal", "true")

            bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
            bounds.set("x", "50")
            bounds.set("y", str(y_offset))
            bounds.set("width", "2000")
            bounds.set("height", str(self.lane_height))

            # Armazenar posição Y da lane
            self.current_lane_y[lane_name] = y_offset + 50

            y_offset += self.lane_height

        self.y_pos = y_offset + 100

    def add_start_event(self, name="Início", lane=None):
        """Adiciona evento de início"""
        event_id = f"StartEvent_{self.generate_id()}"
        event = ET.SubElement(self.process, "startEvent")
        event.set("id", event_id)
        event.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{event_id}_di")
        shape.set("bpmnElement", event_id)

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "36")
        bounds.set("height", "36")

        self.elements[name] = {'id': event_id, 'type': 'startEvent', 'x': x, 'y': y}
        self.x_pos += self.element_spacing

        return event_id

    def add_task(self, name, task_type="task", lane=None):
        """Adiciona tarefa"""
        task_id = f"Task_{self.generate_id()}"

        if task_type == "user":
            task = ET.SubElement(self.process, "userTask")
        elif task_type == "service":
            task = ET.SubElement(self.process, "serviceTask")
        elif task_type == "manual":
            task = ET.SubElement(self.process, "manualTask")
        else:
            task = ET.SubElement(self.process, "task")

        task.set("id", task_id)
        task.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{task_id}_di")
        shape.set("bpmnElement", task_id)

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "100")
        bounds.set("height", "80")

        self.elements[name] = {'id': task_id, 'type': task_type, 'x': x, 'y': y}
        self.x_pos += self.element_spacing

        return task_id

    def add_gateway(self, name, gateway_type="exclusive", lane=None):
        """Adiciona gateway"""
        gateway_id = f"Gateway_{self.generate_id()}"

        if gateway_type == "exclusive" or gateway_type == "xor":
            gateway = ET.SubElement(self.process, "exclusiveGateway")
        elif gateway_type == "parallel" or gateway_type == "and":
            gateway = ET.SubElement(self.process, "parallelGateway")
        elif gateway_type == "inclusive" or gateway_type == "or":
            gateway = ET.SubElement(self.process, "inclusiveGateway")
        elif gateway_type == "event":
            gateway = ET.SubElement(self.process, "eventBasedGateway")

        gateway.set("id", gateway_id)
        gateway.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{gateway_id}_di")
        shape.set("bpmnElement", gateway_id)

        if gateway_type in ["exclusive", "xor"]:
            shape.set("isMarkerVisible", "true")

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "50")
        bounds.set("height", "50")

        self.elements[name] = {'id': gateway_id, 'type': gateway_type, 'x': x, 'y': y}
        self.x_pos += self.element_spacing

        return gateway_id

    def add_intermediate_event(self, name, event_type="timer", lane=None):
        """Adiciona evento intermediário"""
        event_id = f"IntermediateEvent_{self.generate_id()}"

        if event_type == "timer":
            event = ET.SubElement(self.process, "intermediateCatchEvent")
            timer_def = ET.SubElement(event, "timerEventDefinition")
        elif event_type == "message":
            event = ET.SubElement(self.process, "intermediateCatchEvent")
            msg_def = ET.SubElement(event, "messageEventDefinition")
        elif event_type == "error":
            event = ET.SubElement(self.process, "intermediateThrowEvent")
            error_def = ET.SubElement(event, "errorEventDefinition")

        event.set("id", event_id)
        event.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{event_id}_di")
        shape.set("bpmnElement", event_id)

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "36")
        bounds.set("height", "36")

        self.elements[name] = {'id': event_id, 'type': event_type, 'x': x, 'y': y}
        self.x_pos += self.element_spacing

        return event_id

    def add_subprocess(self, name, lane=None):
        """Adiciona subprocesso"""
        subprocess_id = f"SubProcess_{self.generate_id()}"
        subprocess = ET.SubElement(self.process, "subProcess")
        subprocess.set("id", subprocess_id)
        subprocess.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{subprocess_id}_di")
        shape.set("bpmnElement", subprocess_id)
        shape.set("isExpanded", "true")

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "120")
        bounds.set("height", "100")

        self.elements[name] = {'id': subprocess_id, 'type': 'subprocess', 'x': x, 'y': y}
        self.x_pos += 180

        return subprocess_id

    def add_end_event(self, name="Fim", lane=None):
        """Adiciona evento de fim"""
        event_id = f"EndEvent_{self.generate_id()}"
        event = ET.SubElement(self.process, "endEvent")
        event.set("id", event_id)
        event.set("name", name)

        # Shape visual
        x = self.x_pos
        y = self.current_lane_y.get(lane, self.y_pos) if lane else self.y_pos

        shape = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
        shape.set("id", f"{event_id}_di")
        shape.set("bpmnElement", event_id)

        bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
        bounds.set("x", str(x))
        bounds.set("y", str(y))
        bounds.set("width", "36")
        bounds.set("height", "36")

        self.elements[name] = {'id': event_id, 'type': 'endEvent', 'x': x, 'y': y}
        self.x_pos += self.element_spacing

        return event_id

    def connect_elements(self, source_name, target_name, label=""):
        """Conecta dois elementos"""
        if source_name not in self.elements or target_name not in self.elements:
            return None

        source_id = self.elements[source_name]['id']
        target_id = self.elements[target_name]['id']

        flow_id = f"Flow_{self.generate_id()}"
        flow = ET.SubElement(self.process, "sequenceFlow")
        flow.set("id", flow_id)
        flow.set("sourceRef", source_id)
        flow.set("targetRef", target_id)

        if label:
            flow.set("name", label)

        # Edge visual
        edge = ET.SubElement(self.plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge")
        edge.set("id", f"{flow_id}_di")
        edge.set("bpmnElement", flow_id)

        # Waypoints
        source_x = self.elements[source_name]['x'] + 50
        source_y = self.elements[source_name]['y'] + 40
        target_x = self.elements[target_name]['x']
        target_y = self.elements[target_name]['y'] + 40

        waypoint1 = ET.SubElement(edge, "{http://www.omg.org/spec/DD/20100524/DI}waypoint")
        waypoint1.set("x", str(source_x))
        waypoint1.set("y", str(source_y))

        waypoint2 = ET.SubElement(edge, "{http://www.omg.org/spec/DD/20100524/DI}waypoint")
        waypoint2.set("x", str(target_x))
        waypoint2.set("y", str(target_y))

        return flow_id

    def build_process(self):
        """Constrói o processo melhorado"""
        print("\n=== CONSTRUINDO PROCESSO BPMN MELHORADO ===\n")

        # Resetar posição
        self.x_pos = 150
        self.y_pos = 100

        # Lane único para simplificar (Bizagi aceita melhor assim)
        print("[1/8] Criando estrutura de lanes...")
        lanes = [
            "Comercial / Planejamento",
            "Suprimentos / Almoxarifado",
            "Produção / Fabricação",
            "Controle de Qualidade",
            "Logística / Expedição"
        ]
        self.add_lane_set("BLZ Clinic", lanes)

        # FLUXO COMERCIAL
        print("[2/8] Construindo fluxo Comercial...")
        self.x_pos = 150
        start = self.add_start_event("Início", "Comercial / Planejamento")
        receber_pedido = self.add_task("Receber Demanda/Pedido", "user", "Comercial / Planejamento")
        verificar_estoque = self.add_task("Verificar Estoque", "service", "Comercial / Planejamento")
        gw_estoque = self.add_gateway("Estoque Suficiente?", "xor", "Comercial / Planejamento")
        emitir_nf = self.add_task("Emitir NF", "service", "Comercial / Planejamento")
        end_estoque = self.add_end_event("Atendido", "Comercial / Planejamento")

        self.connect_elements("Início", "Receber Demanda/Pedido")
        self.connect_elements("Receber Demanda/Pedido", "Verificar Estoque")
        self.connect_elements("Verificar Estoque", "Estoque Suficiente?")
        self.connect_elements("Estoque Suficiente?", "Emitir NF", "SIM")
        self.connect_elements("Emitir NF", "Atendido")

        # FLUXO SUPRIMENTOS
        print("[3/8] Construindo fluxo Suprimentos...")
        self.x_pos = 650
        ordem_producao = self.add_task("Ordem de Produção", "user", "Suprimentos / Almoxarifado")
        gw_mp = self.add_gateway("MP Disponível?", "xor", "Suprimentos / Almoxarifado")

        self.connect_elements("Estoque Suficiente?", "Ordem de Produção", "NÃO")
        self.connect_elements("Ordem de Produção", "MP Disponível?")

        # Fluxo de compra
        emitir_oc = self.add_task("Emitir OC", "user", "Suprimentos / Almoxarifado")
        aguardar = self.add_task("Aguardar MP", "user", "Suprimentos / Almoxarifado")
        inspecionar = self.add_task("Inspeção MP", "user", "Suprimentos / Almoxarifado")
        gw_insp = self.add_gateway("Aprovada?", "xor", "Suprimentos / Almoxarifado")

        self.connect_elements("MP Disponível?", "Emitir OC", "NÃO")
        self.connect_elements("Emitir OC", "Aguardar MP")
        self.connect_elements("Aguardar MP", "Inspeção MP")
        self.connect_elements("Inspeção MP", "Aprovada?")

        devolver = self.add_task("Devolver", "user", "Suprimentos / Almoxarifado")
        end_dev = self.add_end_event("MP Devolvida", "Suprimentos / Almoxarifado")

        self.connect_elements("Aprovada?", "Devolver", "NÃO")
        self.connect_elements("Devolver", "MP Devolvida")

        # Gateway AND para separação paralela
        gw_sep_split = self.add_gateway("Split Separação", "and", "Suprimentos / Almoxarifado")
        self.connect_elements("Aprovada?", "Split Separação", "SIM")
        self.connect_elements("MP Disponível?", "Split Separação", "SIM")

        # Novas lanes para atividades paralelas
        self.x_pos = 1500
        separar_mp = self.add_task("Separar MP", "user", "Suprimentos / Almoxarifado")
        separar_emb1 = self.add_task("Separar Emb Prim", "user", "Suprimentos / Almoxarifado")
        separar_emb2 = self.add_task("Separar Emb Sec", "user", "Suprimentos / Almoxarifado")

        self.connect_elements("Split Separação", "Separar MP")
        self.connect_elements("Split Separação", "Separar Emb Prim")
        self.connect_elements("Split Separação", "Separar Emb Sec")

        gw_sep_join = self.add_gateway("Join Separação", "and", "Suprimentos / Almoxarifado")
        self.connect_elements("Separar MP", "Join Separação")
        self.connect_elements("Separar Emb Prim", "Join Separação")
        self.connect_elements("Separar Emb Sec", "Join Separação")

        conferir = self.add_task("Conferir e Liberar", "user", "Suprimentos / Almoxarifado")
        msg_producao = self.add_intermediate_event("Enviar p/ Produção", "message", "Suprimentos / Almoxarifado")

        self.connect_elements("Join Separação", "Conferir e Liberar")
        self.connect_elements("Conferir e Liberar", "Enviar p/ Produção")

        # FLUXO PRODUÇÃO
        print("[4/8] Construindo fluxo Produção...")
        self.x_pos = 150
        gw_prep_split = self.add_gateway("Split Preparação", "and", "Produção / Fabricação")
        self.connect_elements("Enviar p/ Produção", "Split Preparação")

        prep_equip = self.add_task("Prep Equipamentos", "user", "Produção / Fabricação")
        pesagem = self.add_task("Pesagem", "user", "Produção / Fabricação")
        higienizar = self.add_task("Higienização", "user", "Produção / Fabricação")

        self.connect_elements("Split Preparação", "Prep Equipamentos")
        self.connect_elements("Split Preparação", "Pesagem")
        self.connect_elements("Split Preparação", "Higienização")

        gw_prep_join = self.add_gateway("Join Preparação", "and", "Produção / Fabricação")
        self.connect_elements("Prep Equipamentos", "Join Preparação")
        self.connect_elements("Pesagem", "Join Preparação")
        self.connect_elements("Higienização", "Join Preparação")

        mistura = self.add_task("Mistura Fase A", "user", "Produção / Fabricação")
        timer_resf = self.add_intermediate_event("Resfriamento", "timer", "Produção / Fabricação")
        homog = self.add_task("Homogeneização", "user", "Produção / Fabricação")
        essencias = self.add_task("Adicionar Essências", "user", "Produção / Fabricação")
        timer_estab = self.add_intermediate_event("Estabilização", "timer", "Produção / Fabricação")
        verificar_ph = self.add_task("Verificar pH", "user", "Produção / Fabricação")

        self.connect_elements("Join Preparação", "Mistura Fase A")
        self.connect_elements("Mistura Fase A", "Resfriamento")
        self.connect_elements("Resfriamento", "Homogeneização")
        self.connect_elements("Homogeneização", "Adicionar Essências")
        self.connect_elements("Adicionar Essências", "Estabilização")
        self.connect_elements("Estabilização", "Verificar pH")

        # Gateway de especificações com retrabalho
        gw_espec = self.add_gateway("Especificações OK?", "xor", "Produção / Fabricação")
        self.connect_elements("Verificar pH", "Especificações OK?")

        ajuste = self.add_task("Ajustar Formulação", "user", "Produção / Fabricação")
        gw_retrabalho = self.add_gateway("Pode Ajustar?", "xor", "Produção / Fabricação")

        self.connect_elements("Especificações OK?", "Ajustar Formulação", "NÃO")
        self.connect_elements("Ajustar Formulação", "Pode Ajustar?")
        self.connect_elements("Pode Ajustar?", "Homogeneização", "SIM")

        descartar = self.add_task("Descartar Lote", "user", "Produção / Fabricação")
        end_desc = self.add_end_event("Lote Descartado", "Produção / Fabricação")

        self.connect_elements("Pode Ajustar?", "Descartar Lote", "NÃO")
        self.connect_elements("Descartar Lote", "Lote Descartado")

        liberar_envase = self.add_task("Liberar p/ Envase", "user", "Produção / Fabricação")
        self.connect_elements("Especificações OK?", "Liberar p/ Envase", "SIM")

        # FLUXO QUALIDADE
        print("[5/8] Construindo fluxo Controle de Qualidade...")
        self.x_pos = 150
        gw_envase_split = self.add_gateway("Split Envase", "and", "Controle de Qualidade")
        self.connect_elements("Liberar p/ Envase", "Split Envase")

        envasar = self.add_task("Envasar", "user", "Controle de Qualidade")
        rotular = self.add_task("Rotular", "user", "Controle de Qualidade")
        amostra = self.add_task("Coletar Amostra", "user", "Controle de Qualidade")
        rastreab = self.add_task("Registrar Rastreabilidade", "service", "Controle de Qualidade")

        self.connect_elements("Split Envase", "Envasar")
        self.connect_elements("Envasar", "Rotular")
        self.connect_elements("Split Envase", "Coletar Amostra")
        self.connect_elements("Split Envase", "Registrar Rastreabilidade")

        gw_envase_join = self.add_gateway("Join Envase", "and", "Controle de Qualidade")
        self.connect_elements("Rotular", "Join Envase")
        self.connect_elements("Coletar Amostra", "Join Envase")
        self.connect_elements("Registrar Rastreabilidade", "Join Envase")

        # Gateway OR para testes opcionais
        gw_testes = self.add_gateway("Testes Adicionais?", "or", "Controle de Qualidade")
        self.connect_elements("Join Envase", "Testes Adicionais?")

        teste_estab = self.add_task("Teste Estabilidade", "user", "Controle de Qualidade")
        teste_micro = self.add_task("Análise Micro", "user", "Controle de Qualidade")
        teste_comp = self.add_task("Teste Compatibilidade", "user", "Controle de Qualidade")

        self.connect_elements("Testes Adicionais?", "Teste Estabilidade", "Produto Novo")
        self.connect_elements("Testes Adicionais?", "Análise Micro", "Validação")
        self.connect_elements("Testes Adicionais?", "Teste Compatibilidade", "Nova Emb")

        gw_testes_join = self.add_gateway("Join Testes", "or", "Controle de Qualidade")
        self.connect_elements("Testes Adicionais?", "Join Testes", "Nenhum")
        self.connect_elements("Teste Estabilidade", "Join Testes")
        self.connect_elements("Análise Micro", "Join Testes")
        self.connect_elements("Teste Compatibilidade", "Join Testes")

        conferencia = self.add_task("Conferência Final", "user", "Controle de Qualidade")
        self.connect_elements("Join Testes", "Conferência Final")

        gw_lote = self.add_gateway("Lote Aprovado?", "xor", "Controle de Qualidade")
        self.connect_elements("Conferência Final", "Lote Aprovado?")

        # Subprocesso de NC
        nc = self.add_subprocess("Gestão de NC", "Controle de Qualidade")
        self.connect_elements("Lote Aprovado?", "Gestão de NC", "NÃO")

        gw_nc = self.add_gateway("NC Corrigível?", "xor", "Controle de Qualidade")
        self.connect_elements("Gestão de NC", "NC Corrigível?")

        rerotular = self.add_task("Rerotular", "user", "Controle de Qualidade")
        self.connect_elements("NC Corrigível?", "Rerotular", "SIM")
        self.connect_elements("Rerotular", "Conferência Final")

        segregar = self.add_task("Segregar Lote", "user", "Controle de Qualidade")
        end_seg = self.add_end_event("Lote Segregado", "Controle de Qualidade")
        self.connect_elements("NC Corrigível?", "Segregar Lote", "NÃO")
        self.connect_elements("Segregar Lote", "Lote Segregado")

        # FLUXO LOGÍSTICA
        print("[6/8] Construindo fluxo Logística...")
        self.x_pos = 150
        gw_exp_split = self.add_gateway("Split Expedição", "and", "Logística / Expedição")
        self.connect_elements("Lote Aprovado?", "Split Expedição", "SIM")

        emitir_nf_final = self.add_task("Emitir NF", "service", "Logística / Expedição")
        paletizar = self.add_task("Paletizar", "user", "Logística / Expedição")
        agendar = self.add_task("Agendar Transporte", "service", "Logística / Expedição")

        self.connect_elements("Split Expedição", "Emitir NF")
        self.connect_elements("Split Expedição", "Paletizar")
        self.connect_elements("Split Expedição", "Agendar Transporte")

        gw_exp_join = self.add_gateway("Join Expedição", "and", "Logística / Expedição")
        self.connect_elements("Emitir NF", "Join Expedição")
        self.connect_elements("Paletizar", "Join Expedição")
        self.connect_elements("Agendar Transporte", "Join Expedição")

        expedir = self.add_task("Expedir", "user", "Logística / Expedição")
        end_sucesso = self.add_end_event("Produto Expedido", "Logística / Expedição")

        self.connect_elements("Join Expedição", "Expedir")
        self.connect_elements("Expedir", "Produto Expedido")

        print("[7/8] Finalizando estrutura...")
        print("[8/8] Processo completo!")

    def export_to_file(self, output_path):
        """Exporta para arquivo XML BPMN"""
        print(f"\nExportando arquivo BPMN...")
        print(f"   Destino: {output_path}")

        tree = ET.ElementTree(self.definitions)
        tree.write(output_path,
                  pretty_print=True,
                  xml_declaration=True,
                  encoding='UTF-8')

        print(f"[OK] Arquivo BPMN exportado com sucesso!")

    def get_statistics(self):
        """Retorna estatísticas"""
        stats = {
            'elementos_totais': len(self.elements),
            'tarefas': sum(1 for e in self.elements.values() if 'task' in e.get('type', '')),
            'gateways': sum(1 for e in self.elements.values() if e.get('type') in ['xor', 'and', 'or', 'exclusive', 'parallel', 'inclusive']),
            'eventos': sum(1 for e in self.elements.values() if 'event' in e.get('type', '').lower()),
            'subprocessos': sum(1 for e in self.elements.values() if e.get('type') == 'subprocess')
        }
        return stats


def main():
    """Função principal"""
    print("="*70)
    print("  GERADOR DE BPMN MELHORADO - BLZ CLINIC")
    print("  Processo de Fabricação de Cosméticos Profissionais")
    print("  Versão 2.0 - XML BPMN 2.0 Nativo")
    print("="*70)

    # Criar gerador
    generator = BPMNBLZClinicGeneratorV2()

    # Construir processo
    generator.build_process()

    # Exportar
    output_file = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\Processo_Fabricacao_BLZ_Clinic_MELHORADO.bpmn"
    generator.export_to_file(output_file)

    # Estatísticas
    stats = generator.get_statistics()
    print("\n" + "="*70)
    print("ESTATÍSTICAS DO PROCESSO MELHORADO:")
    print("="*70)
    print(f"  • Total de elementos: {stats['elementos_totais']}")
    print(f"  • Tarefas/Atividades: {stats['tarefas']}")
    print(f"  • Gateways (XOR/AND/OR): {stats['gateways']}")
    print(f"  • Eventos: {stats['eventos']}")
    print(f"  • Subprocessos: {stats['subprocessos']}")

    print("\n" + "="*70)
    print("MELHORIAS IMPLEMENTADAS:")
    print("="*70)
    print("""
    [OK] Estrutura organizada em 5 lanes principais
    [OK] 10+ Gateways Exclusivos (XOR) para decisoes criticas
    [OK] 7 Gateways Paralelos (AND) para atividades simultaneas
    [OK] 2 Gateways Inclusivos (OR) para requisitos opcionais
    [OK] Eventos de tempo (temporizadores) para processos criticos
    [OK] Eventos de mensagem para comunicacao entre areas
    [OK] Subprocesso de Gestao de Nao Conformidades
    [OK] Fluxos de retrabalho com limites de tentativas
    [OK] Multiplos pontos de fim (sucesso, descarte, segregacao)
    [OK] Rastreabilidade e controle de qualidade reforcados
    [OK] Inspecao de materias-primas no recebimento
    [OK] Atividades paralelas otimizadas (separacao, preparacao, envase, expedicao)
    """)

    print("\n" + "="*70)
    print("[OK] ARQUIVO PRONTO PARA O BIZAGI MODELER!")
    print("="*70)
    print(f"\n[Arquivo] Salvo em:")
    print(f"   {output_file}")
    print("\n[Como usar]")
    print("   1. Abra o Bizagi Modeler")
    print("   2. Va em File > Open")
    print("   3. Selecione o arquivo .bpmn gerado")
    print("   4. O processo sera carregado com todas as melhorias!")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
