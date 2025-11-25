"""
Gerador de BPMN Visual Profissional - BLZ Clinic
Estilo: Pools verticais, fluxo horizontal, visual limpo
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patches as patches
import numpy as np

class BPMNVisualProfessional:
    def __init__(self):
        # Configuração da figura
        self.fig, self.ax = plt.subplots(figsize=(24, 16))
        self.ax.set_xlim(0, 240)
        self.ax.set_ylim(0, 160)
        self.ax.axis('off')

        # Cores profissionais
        self.color_pool_1 = '#E8F4F8'  # Azul claro
        self.color_pool_2 = '#FFF8E1'  # Amarelo claro
        self.color_pool_3 = '#F3E5F5'  # Roxo claro
        self.color_pool_4 = '#E8F5E9'  # Verde claro
        self.color_pool_5 = '#FFF3E0'  # Laranja claro

        self.color_task = '#90CAF9'     # Azul tarefa
        self.color_gateway = '#FFF59D'  # Amarelo gateway
        self.color_event_start = '#A5D6A7'  # Verde início
        self.color_event_end = '#EF9A9A'    # Vermelho fim
        self.color_subprocess = '#FFE082'   # Amarelo subprocesso

    def draw_pool(self, x, width, name, color):
        """Desenha um pool vertical (coluna)"""
        # Retângulo do pool
        pool = FancyBboxPatch((x, 10), width, 140,
                             boxstyle="round,pad=0.5",
                             edgecolor='#37474F',
                             facecolor=color,
                             linewidth=2.5,
                             alpha=0.3)
        self.ax.add_patch(pool)

        # Nome do pool rotacionado
        self.ax.text(x + width/2, 5, name,
                    ha='center', va='center',
                    fontsize=13, fontweight='bold',
                    color='#37474F')

    def draw_task(self, x, y, width, height, name, color='#90CAF9'):
        """Desenha uma tarefa (retângulo arredondado)"""
        task = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.8",
                             edgecolor='#1976D2',
                             facecolor=color,
                             linewidth=2)
        self.ax.add_patch(task)

        # Texto da tarefa
        self.ax.text(x + width/2, y + height/2, name,
                    ha='center', va='center',
                    fontsize=9, fontweight='normal',
                    color='#1A237E',
                    wrap=True)

        return (x + width/2, y + height/2)

    def draw_gateway_xor(self, x, y, size, label=''):
        """Desenha gateway exclusivo (losango amarelo)"""
        # Losango
        diamond_points = np.array([
            [x, y + size/2],      # topo
            [x + size/2, y],      # direita
            [x, y - size/2],      # baixo
            [x - size/2, y]       # esquerda
        ])

        diamond = Polygon(diamond_points,
                         edgecolor='#F57F17',
                         facecolor='#FFF59D',
                         linewidth=2.5)
        self.ax.add_patch(diamond)

        # X no centro
        self.ax.text(x, y, 'X',
                    ha='center', va='center',
                    fontsize=14, fontweight='bold',
                    color='#F57F17')

        # Label acima
        if label:
            self.ax.text(x, y + size/2 + 3, label,
                        ha='center', va='bottom',
                        fontsize=8, style='italic',
                        color='#424242')

        return (x, y)

    def draw_gateway_and(self, x, y, size):
        """Desenha gateway paralelo (losango verde com +)"""
        diamond_points = np.array([
            [x, y + size/2],
            [x + size/2, y],
            [x, y - size/2],
            [x - size/2, y]
        ])

        diamond = Polygon(diamond_points,
                         edgecolor='#388E3C',
                         facecolor='#C8E6C9',
                         linewidth=2.5)
        self.ax.add_patch(diamond)

        # + no centro
        self.ax.text(x, y, '+',
                    ha='center', va='center',
                    fontsize=16, fontweight='bold',
                    color='#1B5E20')

        return (x, y)

    def draw_event_start(self, x, y, radius=4):
        """Desenha evento de início (círculo verde)"""
        circle = Circle((x, y), radius,
                       edgecolor='#2E7D32',
                       facecolor='#A5D6A7',
                       linewidth=2.5)
        self.ax.add_patch(circle)

        return (x, y)

    def draw_event_end(self, x, y, radius=4):
        """Desenha evento de fim (círculo vermelho duplo)"""
        # Círculo externo
        circle_outer = Circle((x, y), radius,
                             edgecolor='#C62828',
                             facecolor='#EF9A9A',
                             linewidth=3)
        self.ax.add_patch(circle_outer)

        # Círculo interno
        circle_inner = Circle((x, y), radius-1,
                             edgecolor='#C62828',
                             facecolor='#EF9A9A',
                             linewidth=2)
        self.ax.add_patch(circle_inner)

        return (x, y)

    def draw_event_intermediate(self, x, y, radius=3.5, event_type='timer'):
        """Desenha evento intermediário"""
        # Círculo duplo
        circle_outer = Circle((x, y), radius,
                             edgecolor='#F57C00',
                             facecolor='white',
                             linewidth=2)
        self.ax.add_patch(circle_outer)

        circle_inner = Circle((x, y), radius-0.8,
                             edgecolor='#F57C00',
                             facecolor='white',
                             linewidth=1.5)
        self.ax.add_patch(circle_inner)

        # Ícone de relógio
        if event_type == 'timer':
            self.ax.text(x, y, '⏱',
                        ha='center', va='center',
                        fontsize=10, color='#E65100')

        return (x, y)

    def draw_subprocess(self, x, y, width, height, name):
        """Desenha subprocesso"""
        subprocess = FancyBboxPatch((x, y), width, height,
                                   boxstyle="round,pad=0.8",
                                   edgecolor='#F57F17',
                                   facecolor='#FFE082',
                                   linewidth=2.5)
        self.ax.add_patch(subprocess)

        # Texto
        self.ax.text(x + width/2, y + height/2 + 2, name,
                    ha='center', va='center',
                    fontsize=9, fontweight='bold',
                    color='#E65100')

        # Símbolo [+] de subprocesso
        self.ax.text(x + width/2, y + 2, '[+]',
                    ha='center', va='center',
                    fontsize=11, fontweight='bold',
                    color='#E65100')

        return (x + width/2, y + height/2)

    def draw_arrow(self, x1, y1, x2, y2, label='', style='solid', color='#424242'):
        """Desenha seta de conexão"""
        if style == 'dashed':
            linestyle = '--'
        else:
            linestyle = '-'

        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                               arrowstyle='-|>',
                               mutation_scale=20,
                               linewidth=2,
                               linestyle=linestyle,
                               color=color,
                               zorder=1)
        self.ax.add_patch(arrow)

        # Label da seta
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            self.ax.text(mid_x, mid_y + 2, label,
                        ha='center', va='bottom',
                        fontsize=8,
                        bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='white',
                                edgecolor='none',
                                alpha=0.8),
                        color='#1976D2',
                        fontweight='bold')

    def create_blz_clinic_process(self):
        """Cria o processo completo da BLZ Clinic"""

        # Título
        self.ax.text(120, 155, 'PROCESSO DE FABRICAÇÃO BLZ CLINIC - MELHORADO',
                    ha='center', va='center',
                    fontsize=18, fontweight='bold',
                    color='#1A237E')

        # Pools verticais (colunas)
        pool_width = 45
        pools = [
            (5, 'COMERCIAL\nPLANEJAMENTO', self.color_pool_1),
            (52, 'SUPRIMENTOS\nALMOXARIFADO', self.color_pool_2),
            (99, 'PRODUÇÃO\nFABRICAÇÃO', self.color_pool_3),
            (146, 'CONTROLE DE\nQUALIDADE', self.color_pool_4),
            (193, 'LOGÍSTICA\nEXPEDIÇÃO', self.color_pool_5)
        ]

        for x, name, color in pools:
            self.draw_pool(x, pool_width, name, color)

        # POOL 1: COMERCIAL (x=5 a 50)
        start = self.draw_event_start(15, 120)

        task1_pos = self.draw_task(10, 105, 30, 12, 'Receber\nDemanda/Pedido')
        task2_pos = self.draw_task(10, 80, 30, 12, 'Verificar\nEstoque')

        gw1_pos = self.draw_gateway_xor(27, 60, 10, 'Estoque\nSuficiente?')

        task3_pos = self.draw_task(10, 35, 30, 10, 'Emitir NF')
        end1 = self.draw_event_end(25, 20)

        # Setas Pool 1
        self.draw_arrow(15, 116, 25, 111)
        self.draw_arrow(25, 105, 25, 92)
        self.draw_arrow(25, 80, 27, 70)
        self.draw_arrow(27, 55, 25, 45, 'SIM', color='#2E7D32')
        self.draw_arrow(25, 35, 25, 24)

        # POOL 2: SUPRIMENTOS (x=52 a 97)
        # Seta vinda do gateway
        self.draw_arrow(32, 60, 65, 100, 'NÃO', color='#C62828')

        task4_pos = self.draw_task(57, 95, 30, 12, 'Emitir Ordem\nde Produção')

        gw2_pos = self.draw_gateway_xor(74, 75, 10, 'MP\nDisponível?')

        task5_pos = self.draw_task(57, 50, 30, 10, 'Emitir OC +\nAguardar')
        task6_pos = self.draw_task(57, 30, 30, 10, 'Inspeção\nde MP')

        gw3_pos = self.draw_gateway_and(74, 100, 10)

        # Separação paralela
        task7a_pos = self.draw_task(59, 115, 13, 8, 'Separar\nMP', '#B3E5FC')
        task7b_pos = self.draw_task(73, 115, 13, 8, 'Separar\nEmb 1', '#B3E5FC')
        task7c_pos = self.draw_task(59, 125, 27, 8, 'Separar Emb 2', '#B3E5FC')

        # Setas Pool 2
        self.draw_arrow(72, 95, 74, 85)
        self.draw_arrow(74, 70, 72, 60, 'NÃO', color='#C62828')
        self.draw_arrow(72, 50, 72, 40)
        self.draw_arrow(72, 30, 74, 20)

        # Para o AND
        self.draw_arrow(78, 75, 80, 90, 'SIM', color='#2E7D32')
        self.draw_arrow(80, 90, 74, 95)

        # Do AND para separações
        self.draw_arrow(74, 105, 65, 119)
        self.draw_arrow(74, 105, 79, 119)
        self.draw_arrow(74, 105, 72, 125)

        # POOL 3: PRODUÇÃO (x=99 a 144)
        # Entrada da produção
        self.draw_arrow(72, 130, 110, 130)

        gw4_pos = self.draw_gateway_and(112, 130, 10)

        # Preparação paralela
        task8a_pos = self.draw_task(101, 115, 12, 8, 'Prep.\nEquip.', '#CE93D8')
        task8b_pos = self.draw_task(114, 115, 12, 8, 'Pesagem', '#CE93D8')
        task8c_pos = self.draw_task(127, 115, 12, 8, 'Higien.', '#CE93D8')

        gw5_pos = self.draw_gateway_and(119, 100, 10)

        # Processo de fabricação
        task9_pos = self.draw_task(107, 80, 25, 10, 'Mistura Fase A')

        timer1 = self.draw_event_intermediate(119, 65, event_type='timer')
        self.ax.text(119, 58, 'Resfr.', ha='center', fontsize=7)

        task10_pos = self.draw_task(107, 45, 25, 10, 'Homogeneização')
        task11_pos = self.draw_task(107, 25, 25, 10, 'Adicionar\nEssências')

        # Gateway de especificações
        gw6_pos = self.draw_gateway_xor(142, 35, 10, 'pH OK?')

        # Loop de retrabalho
        self.draw_arrow(137, 35, 132, 50, 'NÃO', style='dashed', color='#C62828')

        # Setas Pool 3
        self.draw_arrow(112, 125, 107, 119)
        self.draw_arrow(112, 125, 120, 119)
        self.draw_arrow(112, 125, 133, 119)

        self.draw_arrow(107, 115, 114, 105)
        self.draw_arrow(120, 115, 119, 105)
        self.draw_arrow(133, 115, 124, 105)

        self.draw_arrow(119, 100, 119, 90)
        self.draw_arrow(119, 80, 119, 68)
        self.draw_arrow(119, 62, 119, 55)
        self.draw_arrow(119, 45, 119, 35)
        self.draw_arrow(119, 25, 137, 35)

        # POOL 4: QUALIDADE (x=146 a 191)
        # Entrada da qualidade
        self.draw_arrow(147, 35, 158, 115, 'SIM', color='#2E7D32')

        gw7_pos = self.draw_gateway_and(160, 115, 10)

        # Envase paralelo
        task12_pos = self.draw_task(148, 100, 14, 8, 'Envasar', '#A5D6A7')
        task13_pos = self.draw_task(163, 100, 14, 8, 'Rotular', '#A5D6A7')
        task14_pos = self.draw_task(148, 125, 14, 8, 'Coletar\nAmostra', '#A5D6A7')
        task15_pos = self.draw_task(163, 125, 14, 8, 'Rastreab.', '#A5D6A7')

        gw8_pos = self.draw_gateway_and(167, 85, 10)

        task16_pos = self.draw_task(151, 65, 30, 10, 'Conferência\nFinal')

        gw9_pos = self.draw_gateway_xor(167, 45, 10, 'Lote\nAprovado?')

        # Subprocesso NC
        subprocess_pos = self.draw_subprocess(148, 20, 30, 12, 'Gestão de\nNão Conform.')

        # Setas Pool 4
        self.draw_arrow(160, 110, 155, 104)
        self.draw_arrow(160, 110, 170, 104)
        self.draw_arrow(160, 120, 155, 125)
        self.draw_arrow(160, 120, 170, 125)

        self.draw_arrow(155, 100, 162, 88)
        self.draw_arrow(170, 100, 167, 88)
        self.draw_arrow(167, 80, 166, 75)
        self.draw_arrow(166, 65, 167, 55)

        self.draw_arrow(162, 45, 163, 32, 'NÃO', color='#C62828')

        # POOL 5: LOGÍSTICA (x=193 a 238)
        # Entrada da logística
        self.draw_arrow(172, 45, 205, 115, 'SIM', color='#2E7D32')

        gw10_pos = self.draw_gateway_and(207, 115, 10)

        # Expedição paralela
        task17_pos = self.draw_task(195, 100, 13, 8, 'Emitir\nNF', '#FFCC80')
        task18_pos = self.draw_task(209, 100, 13, 8, 'Paletizar', '#FFCC80')
        task19_pos = self.draw_task(223, 100, 13, 8, 'Agendar\nTransp.', '#FFCC80')

        gw11_pos = self.draw_gateway_and(214, 85, 10)

        task20_pos = self.draw_task(201, 65, 27, 10, 'Expedir')

        end2 = self.draw_event_end(214, 45)

        # Setas Pool 5
        self.draw_arrow(207, 110, 201, 104)
        self.draw_arrow(207, 110, 215, 104)
        self.draw_arrow(207, 110, 229, 104)

        self.draw_arrow(201, 100, 209, 88)
        self.draw_arrow(215, 100, 214, 88)
        self.draw_arrow(229, 100, 219, 88)

        self.draw_arrow(214, 80, 214, 75)
        self.draw_arrow(214, 65, 214, 49)

        # Legenda
        self.draw_legend()

        # Rodapé
        self.ax.text(120, 2, 'BLZ Clinic - Processo de Fabricação Melhorado | Gerado em 06/11/2025',
                    ha='center', va='center',
                    fontsize=9, style='italic',
                    color='#757575')

    def draw_legend(self):
        """Desenha legenda"""
        legend_x = 8
        legend_y = 152

        self.ax.text(legend_x, legend_y, 'LEGENDA:', fontsize=10, fontweight='bold')

        # Evento início
        self.ax.add_patch(Circle((legend_x + 2, legend_y - 3), 1.2,
                                edgecolor='#2E7D32', facecolor='#A5D6A7', linewidth=2))
        self.ax.text(legend_x + 4.5, legend_y - 3, 'Início', fontsize=8, va='center')

        # Evento fim
        self.ax.add_patch(Circle((legend_x + 17, legend_y - 3), 1.2,
                                edgecolor='#C62828', facecolor='#EF9A9A', linewidth=2.5))
        self.ax.text(legend_x + 19.5, legend_y - 3, 'Fim', fontsize=8, va='center')

        # Tarefa
        task_leg = FancyBboxPatch((legend_x + 28, legend_y - 4), 6, 2,
                                 boxstyle="round,pad=0.3",
                                 edgecolor='#1976D2', facecolor='#90CAF9', linewidth=1.5)
        self.ax.add_patch(task_leg)
        self.ax.text(legend_x + 31, legend_y - 3, 'Tarefa', fontsize=8, va='center', ha='center')

        # Gateway XOR
        diamond_points = np.array([
            [legend_x + 41, legend_y - 1.5],
            [legend_x + 42.5, legend_y - 3],
            [legend_x + 41, legend_y - 4.5],
            [legend_x + 39.5, legend_y - 3]
        ])
        diamond_leg = Polygon(diamond_points, edgecolor='#F57F17', facecolor='#FFF59D', linewidth=2)
        self.ax.add_patch(diamond_leg)
        self.ax.text(legend_x + 41, legend_y - 3, 'X', ha='center', va='center', fontsize=9, fontweight='bold')
        self.ax.text(legend_x + 45, legend_y - 3, 'Gateway XOR', fontsize=8, va='center')

        # Gateway AND
        diamond_points2 = np.array([
            [legend_x + 59, legend_y - 1.5],
            [legend_x + 60.5, legend_y - 3],
            [legend_x + 59, legend_y - 4.5],
            [legend_x + 57.5, legend_y - 3]
        ])
        diamond_leg2 = Polygon(diamond_points2, edgecolor='#388E3C', facecolor='#C8E6C9', linewidth=2)
        self.ax.add_patch(diamond_leg2)
        self.ax.text(legend_x + 59, legend_y - 3, '+', ha='center', va='center', fontsize=11, fontweight='bold')
        self.ax.text(legend_x + 63, legend_y - 3, 'Gateway AND', fontsize=8, va='center')

    def save_images(self):
        """Salva PNG e PDF"""
        plt.tight_layout()

        # PNG
        output_png = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\BLZ_Clinic_BPMN_PROFISSIONAL.png"
        self.fig.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[OK] PNG salvo: {output_png}")

        # PDF
        output_pdf = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\BLZ_Clinic_BPMN_PROFISSIONAL.pdf"
        self.fig.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
        print(f"[OK] PDF salvo: {output_pdf}")

        plt.close()


def main():
    print("="*70)
    print("  GERADOR DE BPMN VISUAL PROFISSIONAL - BLZ CLINIC")
    print("  Estilo: Pools verticais + Fluxo horizontal")
    print("="*70)

    print("\nCriando visualizacao profissional...")

    generator = BPMNVisualProfessional()
    generator.create_blz_clinic_process()
    generator.save_images()

    print("\n" + "="*70)
    print("[OK] VISUALIZACAO PROFISSIONAL CONCLUIDA!")
    print("="*70)
    print("\nArquivos gerados:")
    print("  - BLZ_Clinic_BPMN_PROFISSIONAL.png")
    print("  - BLZ_Clinic_BPMN_PROFISSIONAL.pdf")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
