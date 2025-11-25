"""
Gerador de BPMN Profissional usando NetworkX + Graphviz
Características:
- Linhas RETAS (sem curvas)
- Layout automático (sem sobreposições)
- Gera PNG/PDF profissional
- Gera arquivo .bpmn para Bizagi
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
import numpy as np
from lxml import etree as ET
import uuid

class BPMNNetworkXGenerator:
    def __init__(self):
        self.G = nx.DiGraph()
        self.pos = None
        self.fig = None
        self.ax = None

        # Cores profissionais
        self.colors = {
            'start': '#A5D6A7',
            'end': '#EF9A9A',
            'task': '#90CAF9',
            'subprocess': '#FFE082',
            'gateway_xor': '#FFF59D',
            'gateway_and': '#C8E6C9',
            'pool_1': '#E8F4F8',
            'pool_2': '#FFF8E1',
            'pool_3': '#F3E5F5',
            'pool_4': '#E8F5E9',
            'pool_5': '#FFF3E0'
        }

    def create_blz_process_graph(self):
        """Cria o grafo do processo BLZ Clinic"""
        print("[1/5] Criando modelo do processo...")

        # Adicionar nós do processo
        nodes = [
            # COMERCIAL
            ('start', {'type': 'start', 'label': 'Início', 'pool': 'Comercial'}),
            ('receber_pedido', {'type': 'task', 'label': 'Receber\nDemanda/Pedido', 'pool': 'Comercial'}),
            ('verificar_estoque', {'type': 'task', 'label': 'Verificar\nEstoque', 'pool': 'Comercial'}),
            ('gw_estoque', {'type': 'gateway_xor', 'label': 'Estoque\nSuficiente?', 'pool': 'Comercial'}),
            ('emitir_nf_estoque', {'type': 'task', 'label': 'Emitir NF', 'pool': 'Comercial'}),
            ('end_estoque', {'type': 'end', 'label': 'Fim\nEstoque', 'pool': 'Comercial'}),

            # SUPRIMENTOS
            ('ordem_producao', {'type': 'task', 'label': 'Emitir Ordem\nde Produção', 'pool': 'Suprimentos'}),
            ('gw_mp', {'type': 'gateway_xor', 'label': 'MP\nDisponível?', 'pool': 'Suprimentos'}),
            ('emitir_oc', {'type': 'task', 'label': 'Emitir OC +\nAguardar', 'pool': 'Suprimentos'}),
            ('inspecao_mp', {'type': 'task', 'label': 'Inspeção\nde MP', 'pool': 'Suprimentos'}),
            ('gw_inspecao', {'type': 'gateway_xor', 'label': 'Inspeção\nOK?', 'pool': 'Suprimentos'}),
            ('devolver_mp', {'type': 'task', 'label': 'Devolver\nFornecedor', 'pool': 'Suprimentos'}),
            ('end_devolucao', {'type': 'end', 'label': 'Fim\nMP Devolvida', 'pool': 'Suprimentos'}),
            ('gw_separacao_split', {'type': 'gateway_and', 'label': 'Split', 'pool': 'Suprimentos'}),
            ('separar_mp', {'type': 'task', 'label': 'Separar\nMP', 'pool': 'Suprimentos'}),
            ('separar_emb1', {'type': 'task', 'label': 'Separar\nEmb Prim', 'pool': 'Suprimentos'}),
            ('separar_emb2', {'type': 'task', 'label': 'Separar\nEmb Sec', 'pool': 'Suprimentos'}),
            ('gw_separacao_join', {'type': 'gateway_and', 'label': 'Join', 'pool': 'Suprimentos'}),
            ('conferir', {'type': 'task', 'label': 'Conferir e\nLiberar', 'pool': 'Suprimentos'}),

            # PRODUÇÃO
            ('gw_prep_split', {'type': 'gateway_and', 'label': 'Split', 'pool': 'Producao'}),
            ('prep_equip', {'type': 'task', 'label': 'Prep.\nEquipamentos', 'pool': 'Producao'}),
            ('pesagem', {'type': 'task', 'label': 'Pesagem\nInsumos', 'pool': 'Producao'}),
            ('higienizacao', {'type': 'task', 'label': 'Higienização', 'pool': 'Producao'}),
            ('gw_prep_join', {'type': 'gateway_and', 'label': 'Join', 'pool': 'Producao'}),
            ('mistura', {'type': 'task', 'label': 'Mistura\nFase A', 'pool': 'Producao'}),
            ('homogeneizacao', {'type': 'task', 'label': 'Homogeneização\n+ Turbo', 'pool': 'Producao'}),
            ('adicionar_essencias', {'type': 'task', 'label': 'Adicionar\nEssências', 'pool': 'Producao'}),
            ('verificar_ph', {'type': 'task', 'label': 'Verificar\npH/Visc', 'pool': 'Producao'}),
            ('gw_especificacoes', {'type': 'gateway_xor', 'label': 'pH\nOK?', 'pool': 'Producao'}),
            ('ajustar', {'type': 'task', 'label': 'Ajustar\nFormulação', 'pool': 'Producao'}),
            ('gw_retrabalho', {'type': 'gateway_xor', 'label': 'Pode\nAjustar?', 'pool': 'Producao'}),
            ('descartar', {'type': 'task', 'label': 'Descartar\nLote', 'pool': 'Producao'}),
            ('end_descarte', {'type': 'end', 'label': 'Fim\nDescartado', 'pool': 'Producao'}),
            ('liberar_envase', {'type': 'task', 'label': 'Liberar p/\nEnvase', 'pool': 'Producao'}),

            # QUALIDADE
            ('gw_envase_split', {'type': 'gateway_and', 'label': 'Split', 'pool': 'Qualidade'}),
            ('envasar', {'type': 'task', 'label': 'Envasar\nProduto', 'pool': 'Qualidade'}),
            ('rotular', {'type': 'task', 'label': 'Rotular', 'pool': 'Qualidade'}),
            ('coletar_amostra', {'type': 'task', 'label': 'Coletar\nAmostra', 'pool': 'Qualidade'}),
            ('rastreabilidade', {'type': 'task', 'label': 'Registrar\nRastreab.', 'pool': 'Qualidade'}),
            ('gw_envase_join', {'type': 'gateway_and', 'label': 'Join', 'pool': 'Qualidade'}),
            ('conferencia_final', {'type': 'task', 'label': 'Conferência\nFinal', 'pool': 'Qualidade'}),
            ('gw_lote', {'type': 'gateway_xor', 'label': 'Lote\nAprovado?', 'pool': 'Qualidade'}),
            ('gestao_nc', {'type': 'subprocess', 'label': 'Gestão de\nNão Conform.', 'pool': 'Qualidade'}),
            ('gw_nc', {'type': 'gateway_xor', 'label': 'NC\nCorrigível?', 'pool': 'Qualidade'}),
            ('rerotular', {'type': 'task', 'label': 'Rerotular', 'pool': 'Qualidade'}),
            ('segregar', {'type': 'task', 'label': 'Segregar\nLote', 'pool': 'Qualidade'}),
            ('end_segregado', {'type': 'end', 'label': 'Fim\nSegregado', 'pool': 'Qualidade'}),

            # LOGÍSTICA
            ('gw_exp_split', {'type': 'gateway_and', 'label': 'Split', 'pool': 'Logistica'}),
            ('emitir_nf_final', {'type': 'task', 'label': 'Emitir NF\nFinal', 'pool': 'Logistica'}),
            ('paletizar', {'type': 'task', 'label': 'Paletizar', 'pool': 'Logistica'}),
            ('agendar_transporte', {'type': 'task', 'label': 'Agendar\nTransporte', 'pool': 'Logistica'}),
            ('gw_exp_join', {'type': 'gateway_and', 'label': 'Join', 'pool': 'Logistica'}),
            ('expedir', {'type': 'task', 'label': 'Expedir\nProduto', 'pool': 'Logistica'}),
            ('end_sucesso', {'type': 'end', 'label': 'Fim\nSucesso', 'pool': 'Logistica'}),
        ]

        for node_id, attrs in nodes:
            self.G.add_node(node_id, **attrs)

        # Adicionar arestas (fluxo de sequência)
        edges = [
            # COMERCIAL
            ('start', 'receber_pedido'),
            ('receber_pedido', 'verificar_estoque'),
            ('verificar_estoque', 'gw_estoque'),
            ('gw_estoque', 'emitir_nf_estoque', 'SIM'),
            ('emitir_nf_estoque', 'end_estoque'),
            ('gw_estoque', 'ordem_producao', 'NÃO'),

            # SUPRIMENTOS
            ('ordem_producao', 'gw_mp'),
            ('gw_mp', 'emitir_oc', 'NÃO'),
            ('emitir_oc', 'inspecao_mp'),
            ('inspecao_mp', 'gw_inspecao'),
            ('gw_inspecao', 'devolver_mp', 'NÃO'),
            ('devolver_mp', 'end_devolucao'),
            ('gw_inspecao', 'gw_separacao_split', 'SIM'),
            ('gw_mp', 'gw_separacao_split', 'SIM'),
            ('gw_separacao_split', 'separar_mp'),
            ('gw_separacao_split', 'separar_emb1'),
            ('gw_separacao_split', 'separar_emb2'),
            ('separar_mp', 'gw_separacao_join'),
            ('separar_emb1', 'gw_separacao_join'),
            ('separar_emb2', 'gw_separacao_join'),
            ('gw_separacao_join', 'conferir'),

            # PRODUÇÃO
            ('conferir', 'gw_prep_split'),
            ('gw_prep_split', 'prep_equip'),
            ('gw_prep_split', 'pesagem'),
            ('gw_prep_split', 'higienizacao'),
            ('prep_equip', 'gw_prep_join'),
            ('pesagem', 'gw_prep_join'),
            ('higienizacao', 'gw_prep_join'),
            ('gw_prep_join', 'mistura'),
            ('mistura', 'homogeneizacao'),
            ('homogeneizacao', 'adicionar_essencias'),
            ('adicionar_essencias', 'verificar_ph'),
            ('verificar_ph', 'gw_especificacoes'),
            ('gw_especificacoes', 'ajustar', 'NÃO'),
            ('ajustar', 'gw_retrabalho'),
            ('gw_retrabalho', 'homogeneizacao', 'SIM'),
            ('gw_retrabalho', 'descartar', 'NÃO'),
            ('descartar', 'end_descarte'),
            ('gw_especificacoes', 'liberar_envase', 'SIM'),

            # QUALIDADE
            ('liberar_envase', 'gw_envase_split'),
            ('gw_envase_split', 'envasar'),
            ('envasar', 'rotular'),
            ('gw_envase_split', 'coletar_amostra'),
            ('gw_envase_split', 'rastreabilidade'),
            ('rotular', 'gw_envase_join'),
            ('coletar_amostra', 'gw_envase_join'),
            ('rastreabilidade', 'gw_envase_join'),
            ('gw_envase_join', 'conferencia_final'),
            ('conferencia_final', 'gw_lote'),
            ('gw_lote', 'gestao_nc', 'NÃO'),
            ('gestao_nc', 'gw_nc'),
            ('gw_nc', 'rerotular', 'SIM'),
            ('rerotular', 'conferencia_final'),
            ('gw_nc', 'segregar', 'NÃO'),
            ('segregar', 'end_segregado'),
            ('gw_lote', 'gw_exp_split', 'SIM'),

            # LOGÍSTICA
            ('gw_exp_split', 'emitir_nf_final'),
            ('gw_exp_split', 'paletizar'),
            ('gw_exp_split', 'agendar_transporte'),
            ('emitir_nf_final', 'gw_exp_join'),
            ('paletizar', 'gw_exp_join'),
            ('agendar_transporte', 'gw_exp_join'),
            ('gw_exp_join', 'expedir'),
            ('expedir', 'end_sucesso'),
        ]

        for edge in edges:
            if len(edge) == 3:
                self.G.add_edge(edge[0], edge[1], label=edge[2])
            else:
                self.G.add_edge(edge[0], edge[1])

        print(f"   Criado grafo com {self.G.number_of_nodes()} nos e {self.G.number_of_edges()} arestas")

    def calculate_hierarchical_layout(self):
        """Calcula layout hierárquico manual (fallback sem Graphviz)"""
        print("[2/5] Calculando layout hierarquico...")

        # Tentar usar Graphviz primeiro
        try:
            from networkx.drawing.nx_pydot import graphviz_layout
            self.pos = graphviz_layout(self.G, prog='dot')
            print("   Usando Graphviz para layout otimo")
            return
        except:
            pass

        # Fallback: layout hierárquico manual
        print("   Graphviz nao disponivel, usando layout hierarquico manual")

        # Agrupar por pool
        pools = {}
        for node, attrs in self.G.nodes(data=True):
            pool = attrs.get('pool', 'Unknown')
            if pool not in pools:
                pools[pool] = []
            pools[pool].append(node)

        # Posicionar nós
        self.pos = {}
        pool_order = ['Comercial', 'Suprimentos', 'Producao', 'Qualidade', 'Logistica']
        x_spacing = 200
        y_spacing = 80

        for pool_idx, pool_name in enumerate(pool_order):
            nodes_in_pool = pools.get(pool_name, [])
            x_base = pool_idx * x_spacing

            for node_idx, node in enumerate(nodes_in_pool):
                x = x_base
                y = node_idx * y_spacing
                self.pos[node] = (x, y)

    def draw_bpmn_diagram(self):
        """Desenha diagrama BPMN profissional"""
        print("[3/5] Desenhando diagrama BPMN...")

        self.fig, self.ax = plt.subplots(figsize=(26, 18))

        # Configurar eixos
        x_vals = [x for x, y in self.pos.values()]
        y_vals = [y for x, y in self.pos.values()]
        margin = 100
        self.ax.set_xlim(min(x_vals) - margin, max(x_vals) + margin)
        self.ax.set_ylim(min(y_vals) - margin, max(y_vals) + margin)
        self.ax.axis('off')

        # Título
        self.ax.text((min(x_vals) + max(x_vals)) / 2, max(y_vals) + 80,
                    'PROCESSO DE FABRICAÇÃO BLZ CLINIC - MELHORADO',
                    ha='center', fontsize=20, fontweight='bold', color='#1A237E')

        # Desenhar arestas PRIMEIRO (para ficarem atrás)
        self.draw_edges()

        # Desenhar nós
        for node, (x, y) in self.pos.items():
            attrs = self.G.nodes[node]
            node_type = attrs['type']
            label = attrs['label']

            if node_type == 'start':
                self.draw_start_event(x, y, label)
            elif node_type == 'end':
                self.draw_end_event(x, y, label)
            elif node_type == 'task':
                self.draw_task(x, y, label)
            elif node_type == 'subprocess':
                self.draw_subprocess(x, y, label)
            elif node_type == 'gateway_xor':
                self.draw_gateway_xor(x, y, label)
            elif node_type == 'gateway_and':
                self.draw_gateway_and(x, y, label)

        # Legenda
        self.draw_legend()

        # Rodapé
        self.ax.text((min(x_vals) + max(x_vals)) / 2, min(y_vals) - 60,
                    'BLZ Clinic - Processo Melhorado | Gerado com NetworkX | 06/11/2025',
                    ha='center', fontsize=10, style='italic', color='#757575')

        print("   Diagrama desenhado")

    def draw_edges(self):
        """Desenha arestas com linhas retas"""
        for edge in self.G.edges():
            source, target = edge
            x1, y1 = self.pos[source]
            x2, y2 = self.pos[target]

            # Linha reta
            self.ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2, zorder=1)

            # Seta
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            if length > 0:
                dx_norm = dx / length
                dy_norm = dy / length
                arrow_x = x2 - dx_norm * 15
                arrow_y = y2 - dy_norm * 15
                self.ax.annotate('', xy=(x2, y2), xytext=(arrow_x, arrow_y),
                               arrowprops=dict(arrowstyle='->', lw=2, color='black'))

            # Label da aresta
            label = self.G.edges[edge].get('label', '')
            if label:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                self.ax.text(mid_x, mid_y + 8, label,
                           ha='center', fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='none'),
                           color='#1976D2', zorder=10)

    def draw_start_event(self, x, y, label):
        """Desenha evento de início"""
        circle = Circle((x, y), 15, facecolor=self.colors['start'],
                       edgecolor='#2E7D32', linewidth=3, zorder=5)
        self.ax.add_patch(circle)
        self.ax.text(x, y - 25, label, ha='center', fontsize=8)

    def draw_end_event(self, x, y, label):
        """Desenha evento de fim"""
        circle = Circle((x, y), 15, facecolor=self.colors['end'],
                       edgecolor='#C62828', linewidth=4, zorder=5)
        self.ax.add_patch(circle)
        self.ax.text(x, y - 25, label, ha='center', fontsize=8)

    def draw_task(self, x, y, label):
        """Desenha tarefa"""
        rect = FancyBboxPatch((x-40, y-20), 80, 40, boxstyle="round,pad=3",
                             facecolor=self.colors['task'], edgecolor='#1976D2',
                             linewidth=2, zorder=5)
        self.ax.add_patch(rect)
        self.ax.text(x, y, label, ha='center', va='center', fontsize=9)

    def draw_subprocess(self, x, y, label):
        """Desenha subprocesso"""
        rect = FancyBboxPatch((x-45, y-25), 90, 50, boxstyle="round,pad=3",
                             facecolor=self.colors['subprocess'], edgecolor='#F57F17',
                             linewidth=3, zorder=5)
        self.ax.add_patch(rect)
        self.ax.text(x, y + 5, label, ha='center', va='center', fontsize=9, fontweight='bold')
        self.ax.text(x, y - 15, '[+]', ha='center', fontsize=12, fontweight='bold')

    def draw_gateway_xor(self, x, y, label):
        """Desenha gateway exclusivo"""
        diamond = Polygon([(x, y+20), (x+20, y), (x, y-20), (x-20, y)],
                         facecolor=self.colors['gateway_xor'], edgecolor='#F57F17',
                         linewidth=3, zorder=5)
        self.ax.add_patch(diamond)
        self.ax.text(x, y, 'X', ha='center', va='center', fontsize=14, fontweight='bold')
        self.ax.text(x, y + 28, label, ha='center', fontsize=7, style='italic')

    def draw_gateway_and(self, x, y, label):
        """Desenha gateway paralelo"""
        diamond = Polygon([(x, y+20), (x+20, y), (x, y-20), (x-20, y)],
                         facecolor=self.colors['gateway_and'], edgecolor='#388E3C',
                         linewidth=3, zorder=5)
        self.ax.add_patch(diamond)
        self.ax.text(x, y, '+', ha='center', va='center', fontsize=18, fontweight='bold')
        self.ax.text(x, y + 28, label, ha='center', fontsize=7, style='italic')

    def draw_legend(self):
        """Desenha legenda"""
        legend_elements = [
            mpatches.Patch(facecolor=self.colors['start'], edgecolor='#2E7D32', label='Início', linewidth=2),
            mpatches.Patch(facecolor=self.colors['end'], edgecolor='#C62828', label='Fim', linewidth=2),
            mpatches.Patch(facecolor=self.colors['task'], edgecolor='#1976D2', label='Tarefa', linewidth=2),
            mpatches.Patch(facecolor=self.colors['gateway_xor'], edgecolor='#F57F17', label='Gateway XOR', linewidth=2),
            mpatches.Patch(facecolor=self.colors['gateway_and'], edgecolor='#388E3C', label='Gateway AND', linewidth=2),
            mpatches.Patch(facecolor=self.colors['subprocess'], edgecolor='#F57F17', label='Subprocesso', linewidth=2),
        ]
        self.ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.9)

    def save_images(self):
        """Salva PNG e PDF"""
        print("[4/5] Salvando imagens...")

        plt.tight_layout()

        output_png = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\BLZ_Clinic_BPMN_NetworkX.png"
        self.fig.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"   PNG salvo: {output_png}")

        output_pdf = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\BLZ_Clinic_BPMN_NetworkX.pdf"
        self.fig.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
        print(f"   PDF salvo: {output_pdf}")

        plt.close()

    def generate_bpmn_xml(self):
        """Gera arquivo BPMN XML para Bizagi"""
        print("[5/5] Gerando arquivo BPMN XML para Bizagi...")

        # Criar estrutura BPMN 2.0
        nsmap = {
            None: "http://www.omg.org/spec/BPMN/20100524/MODEL",
            "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            "dc": "http://www.omg.org/spec/DD/20100524/DC",
            "di": "http://www.omg.org/spec/DD/20100524/DI"
        }

        definitions = ET.Element("definitions", nsmap=nsmap)
        definitions.set("id", "Definitions_" + str(uuid.uuid4())[:8])
        definitions.set("targetNamespace", "http://bpmn.io/schema/bpmn")

        # Processo
        process = ET.SubElement(definitions, "process")
        process.set("id", "Process_BLZ_Clinic")
        process.set("isExecutable", "true")

        # Diagrama para visualização
        diagram = ET.SubElement(definitions, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram")
        diagram.set("id", "BPMNDiagram_1")
        plane = ET.SubElement(diagram, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane")
        plane.set("id", "BPMNPlane_1")
        plane.set("bpmnElement", "Process_BLZ_Clinic")

        # Mapeamento de IDs
        node_id_map = {}

        # Adicionar nós ao processo
        for node, attrs in self.G.nodes(data=True):
            node_type = attrs['type']
            label = attrs['label'].replace('\n', ' ')
            node_id = f"{node_type}_{str(uuid.uuid4())[:8]}"
            node_id_map[node] = node_id

            if node_type == 'start':
                element = ET.SubElement(process, "startEvent")
            elif node_type == 'end':
                element = ET.SubElement(process, "endEvent")
            elif node_type == 'task':
                element = ET.SubElement(process, "task")
            elif node_type == 'subprocess':
                element = ET.SubElement(process, "subProcess")
            elif node_type == 'gateway_xor':
                element = ET.SubElement(process, "exclusiveGateway")
            elif node_type == 'gateway_and':
                element = ET.SubElement(process, "parallelGateway")

            element.set("id", node_id)
            element.set("name", label)

            # Adicionar shape visual
            x, y = self.pos[node]
            shape = ET.SubElement(plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape")
            shape.set("id", f"{node_id}_di")
            shape.set("bpmnElement", node_id)

            bounds = ET.SubElement(shape, "{http://www.omg.org/spec/DD/20100524/DC}Bounds")
            bounds.set("x", str(x))
            bounds.set("y", str(y))

            if node_type in ['start', 'end']:
                bounds.set("width", "36")
                bounds.set("height", "36")
            elif node_type in ['gateway_xor', 'gateway_and']:
                bounds.set("width", "50")
                bounds.set("height", "50")
            else:
                bounds.set("width", "100")
                bounds.set("height", "80")

        # Adicionar fluxos de sequência
        for source, target, attrs in self.G.edges(data=True):
            flow_id = f"Flow_{str(uuid.uuid4())[:8]}"
            flow = ET.SubElement(process, "sequenceFlow")
            flow.set("id", flow_id)
            flow.set("sourceRef", node_id_map[source])
            flow.set("targetRef", node_id_map[target])

            label = attrs.get('label', '')
            if label:
                flow.set("name", label)

            # Adicionar edge visual
            edge = ET.SubElement(plane, "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge")
            edge.set("id", f"{flow_id}_di")
            edge.set("bpmnElement", flow_id)

            x1, y1 = self.pos[source]
            x2, y2 = self.pos[target]

            waypoint1 = ET.SubElement(edge, "{http://www.omg.org/spec/DD/20100524/DI}waypoint")
            waypoint1.set("x", str(x1))
            waypoint1.set("y", str(y1))

            waypoint2 = ET.SubElement(edge, "{http://www.omg.org/spec/DD/20100524/DI}waypoint")
            waypoint2.set("x", str(x2))
            waypoint2.set("y", str(y2))

        # Salvar arquivo
        tree = ET.ElementTree(definitions)
        output_file = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\BLZ_Clinic_PROCESSO.bpmn"
        tree.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        print(f"   BPMN XML salvo: {output_file}")
        print("   Pronto para abrir no Bizagi Modeler!")


def main():
    print("="*80)
    print("  GERADOR DE BPMN COM NETWORKX + GRAPHVIZ")
    print("  Linhas retas + Layout automático sem sobreposições")
    print("="*80 + "\n")

    generator = BPMNNetworkXGenerator()
    generator.create_blz_process_graph()
    generator.calculate_hierarchical_layout()
    generator.draw_bpmn_diagram()
    generator.save_images()
    generator.generate_bpmn_xml()

    print("\n" + "="*80)
    print("[OK] PROCESSO CONCLUIDO!")
    print("="*80)


if __name__ == "__main__":
    main()
