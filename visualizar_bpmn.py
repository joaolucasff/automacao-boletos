"""
Script para criar visualização e documentação do BPMN melhorado
Gera PNG e PDF com resumo do processo
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from datetime import datetime

def create_process_visualization():
    """Cria visualização simplificada do processo"""
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Título
    ax.text(50, 98, 'PROCESSO DE FABRICAÇÃO BLZ CLINIC - MELHORADO',
            ha='center', va='top', fontsize=20, fontweight='bold')
    ax.text(50, 95, 'Processo de Cosméticos Profissionais com Melhorias BPMN',
            ha='center', va='top', fontsize=12, style='italic')

    # Definir posições verticais para cada lane
    lanes = [
        ('COMERCIAL / PLANEJAMENTO', 85),
        ('SUPRIMENTOS / ALMOXARIFADO', 68),
        ('PRODUÇÃO / FABRICAÇÃO', 51),
        ('CONTROLE DE QUALIDADE', 34),
        ('LOGÍSTICA / EXPEDIÇÃO', 17)
    ]

    # Desenhar lanes
    colors = ['#E3F2FD', '#FFF3E0', '#F3E5F5', '#E8F5E9', '#FFF9C4']
    for idx, (lane_name, y_pos) in enumerate(lanes):
        # Retângulo da lane
        lane_box = FancyBboxPatch((2, y_pos-5), 96, 12,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor=colors[idx],
                                 linewidth=2,
                                 alpha=0.6)
        ax.add_patch(lane_box)

        # Nome da lane
        ax.text(4, y_pos+4, lane_name,
               ha='left', va='center', fontsize=11, fontweight='bold')

    # LANE 1: COMERCIAL
    y = 88
    x_start = 8
    # Evento de início
    circle = plt.Circle((x_start, y), 1.5, color='green', ec='black', linewidth=2)
    ax.add_patch(circle)
    ax.text(x_start, y-3, 'Início', ha='center', fontsize=8)

    # Tarefas
    tasks_comercial = [
        (x_start+6, 'Receber\nPedido'),
        (x_start+14, 'Verificar\nEstoque'),
    ]

    for x, task_name in tasks_comercial:
        task_box = FancyBboxPatch((x-2.5, y-1.5), 5, 3,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor='#BBDEFB',
                                 linewidth=1.5)
        ax.add_patch(task_box)
        ax.text(x, y, task_name, ha='center', va='center', fontsize=7)

    # Gateway XOR
    x_gateway = x_start + 22
    diamond = mpatches.FancyBboxPatch((x_gateway-1.5, y-1.5), 3, 3,
                                     boxstyle="round,pad=0.05",
                                     edgecolor='orange',
                                     facecolor='yellow',
                                     linewidth=2)
    ax.add_patch(diamond)
    ax.text(x_gateway, y, 'XOR', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(x_gateway, y-3, 'Estoque\nSuficiente?', ha='center', fontsize=6)

    # Fim (caminho SIM)
    x_end = x_start + 28
    circle_end = plt.Circle((x_end, y+2), 1.5, color='red', ec='black', linewidth=3)
    ax.add_patch(circle_end)
    ax.text(x_end, y+4.5, 'FIM', ha='center', fontsize=7)
    ax.text(x_end-2, y+2.5, 'SIM', ha='center', fontsize=6, color='green')

    # Seta para baixo (caminho NÃO)
    ax.arrow(x_gateway, y-1.5, 0, -7, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
    ax.text(x_gateway+1.5, y-5, 'NÃO', ha='left', fontsize=6, color='red')

    # LANE 2: SUPRIMENTOS
    y = 71
    x_start_sup = x_gateway

    tasks_suprimentos = [
        (x_start_sup+7, 'Emitir\nOC'),
        (x_start_sup+14, 'Inspeção\nMP'),
    ]

    for x, task_name in tasks_suprimentos:
        task_box = FancyBboxPatch((x-2.5, y-1.5), 5, 3,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor='#FFE0B2',
                                 linewidth=1.5)
        ax.add_patch(task_box)
        ax.text(x, y, task_name, ha='center', va='center', fontsize=7)

    # Gateway AND (Separação Paralela)
    x_and = x_start_sup + 24
    and_box = FancyBboxPatch((x_and-1.5, y-1.5), 3, 3,
                            boxstyle="round,pad=0.05",
                            edgecolor='green',
                            facecolor='lightgreen',
                            linewidth=2)
    ax.add_patch(and_box)
    ax.text(x_and, y, 'AND', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(x_and, y-3, 'Split\nSeparação', ha='center', fontsize=6)

    # 3 tarefas paralelas
    parallel_tasks = [
        (x_and+7, y+2, 'Separar\nMP'),
        (x_and+7, y, 'Separar\nEmb 1'),
        (x_and+7, y-2, 'Separar\nEmb 2')
    ]

    for x, y_task, task_name in parallel_tasks:
        task_box = FancyBboxPatch((x-2, y_task-1), 4, 2,
                                 boxstyle="round,pad=0.05",
                                 edgecolor='black',
                                 facecolor='#FFE0B2',
                                 linewidth=1)
        ax.add_patch(task_box)
        ax.text(x, y_task, task_name, ha='center', va='center', fontsize=6)

    # LANE 3: PRODUÇÃO
    y_prod = 54
    x_start_prod = 8

    # Gateway AND (Preparação Paralela)
    and_prod = FancyBboxPatch((x_start_prod-1, y_prod-1.5), 3, 3,
                             boxstyle="round,pad=0.05",
                             edgecolor='green',
                             facecolor='lightgreen',
                             linewidth=2)
    ax.add_patch(and_prod)
    ax.text(x_start_prod+0.5, y_prod, 'AND', ha='center', va='center', fontsize=8, fontweight='bold')

    # Tarefas de produção
    prod_tasks = [
        (x_start_prod+8, 'Mistura\nFase A'),
        (x_start_prod+16, 'Homogeneização'),
        (x_start_prod+24, 'Adicionar\nEssências'),
    ]

    for x, task_name in prod_tasks:
        task_box = FancyBboxPatch((x-2.5, y_prod-1.5), 5, 3,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor='#E1BEE7',
                                 linewidth=1.5)
        ax.add_patch(task_box)
        ax.text(x, y_prod, task_name, ha='center', va='center', fontsize=7)

    # Eventos de tempo
    timer1 = plt.Circle((x_start_prod+12, y_prod), 1, color='white', ec='orange', linewidth=2)
    ax.add_patch(timer1)
    ax.text(x_start_prod+12, y_prod, '⏱', ha='center', va='center', fontsize=10)
    ax.text(x_start_prod+12, y_prod-2.5, 'Timer\nResfr.', ha='center', fontsize=5)

    # Gateway XOR (Especificações OK?)
    x_spec = x_start_prod + 32
    spec_box = mpatches.FancyBboxPatch((x_spec-1.5, y_prod-1.5), 3, 3,
                                      boxstyle="round,pad=0.05",
                                      edgecolor='orange',
                                      facecolor='yellow',
                                      linewidth=2)
    ax.add_patch(spec_box)
    ax.text(x_spec, y_prod, 'XOR', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(x_spec, y_prod-3, 'pH OK?', ha='center', fontsize=6)

    # Loop de retrabalho
    ax.annotate('', xy=(x_start_prod+16, y_prod-1), xytext=(x_spec, y_prod-4),
               arrowprops=dict(arrowstyle='->', color='red', lw=1.5, linestyle='dashed'))
    ax.text(x_spec-3, y_prod-3.5, 'Retrabalho', ha='center', fontsize=6, color='red')

    # LANE 4: QUALIDADE
    y_qual = 37
    x_start_qual = 8

    # Gateway AND (Envase Paralelo)
    and_qual = FancyBboxPatch((x_start_qual-1, y_qual-1.5), 3, 3,
                             boxstyle="round,pad=0.05",
                             edgecolor='green',
                             facecolor='lightgreen',
                             linewidth=2)
    ax.add_patch(and_qual)
    ax.text(x_start_qual+0.5, y_qual, 'AND', ha='center', va='center', fontsize=8, fontweight='bold')

    qual_tasks = [
        (x_start_qual+8, 'Envasar'),
        (x_start_qual+16, 'Rotular'),
        (x_start_qual+24, 'Coleta\nAmostra'),
    ]

    for x, task_name in qual_tasks:
        task_box = FancyBboxPatch((x-2.5, y_qual-1.5), 5, 3,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor='#C8E6C9',
                                 linewidth=1.5)
        ax.add_patch(task_box)
        ax.text(x, y_qual, task_name, ha='center', va='center', fontsize=7)

    # Gateway OR (Testes Opcionais)
    x_or = x_start_qual + 32
    or_box = FancyBboxPatch((x_or-1.5, y_qual-1.5), 3, 3,
                           boxstyle="round,pad=0.05",
                           edgecolor='purple',
                           facecolor='#E1BEE7',
                           linewidth=2)
    ax.add_patch(or_box)
    ax.text(x_or, y_qual, 'OR', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(x_or, y_qual-3, 'Testes\nOpc.', ha='center', fontsize=6)

    # Subprocesso
    x_sub = x_or + 8
    subprocess_box = FancyBboxPatch((x_sub-3, y_qual-2), 6, 4,
                                   boxstyle="round,pad=0.1",
                                   edgecolor='black',
                                   facecolor='#FFF9C4',
                                   linewidth=2)
    ax.add_patch(subprocess_box)
    ax.text(x_sub, y_qual, 'Gestão de\nNão Conform.', ha='center', va='center', fontsize=7, fontweight='bold')
    # Marcador de subprocesso
    ax.text(x_sub, y_qual-1.5, '[+]', ha='center', fontsize=10)

    # LANE 5: LOGÍSTICA
    y_log = 20
    x_start_log = 8

    # Gateway AND (Expedição Paralela)
    and_log = FancyBboxPatch((x_start_log-1, y_log-1.5), 3, 3,
                            boxstyle="round,pad=0.05",
                            edgecolor='green',
                            facecolor='lightgreen',
                            linewidth=2)
    ax.add_patch(and_log)
    ax.text(x_start_log+0.5, y_log, 'AND', ha='center', va='center', fontsize=8, fontweight='bold')

    log_tasks = [
        (x_start_log+8, 'Emitir\nNF'),
        (x_start_log+16, 'Paletizar'),
        (x_start_log+24, 'Agendar\nTransporte'),
    ]

    for x, task_name in log_tasks:
        task_box = FancyBboxPatch((x-2.5, y_log-1.5), 5, 3,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='black',
                                 facecolor='#FFF9C4',
                                 linewidth=1.5)
        ax.add_patch(task_box)
        ax.text(x, y_log, task_name, ha='center', va='center', fontsize=7)

    # Expedição e Fim
    x_exp = x_start_log + 32
    exp_box = FancyBboxPatch((x_exp-2.5, y_log-1.5), 5, 3,
                            boxstyle="round,pad=0.1",
                            edgecolor='black',
                            facecolor='#FFF9C4',
                            linewidth=1.5)
    ax.add_patch(exp_box)
    ax.text(x_exp, y_log, 'Expedir', ha='center', va='center', fontsize=7)

    x_fim = x_exp + 6
    circle_fim = plt.Circle((x_fim, y_log), 1.5, color='red', ec='black', linewidth=3)
    ax.add_patch(circle_fim)
    ax.text(x_fim, y_log-3, 'FIM\nSucesso', ha='center', fontsize=7, fontweight='bold')

    # Legenda
    legend_x = 5
    legend_y = 8

    ax.text(legend_x, legend_y+4, 'LEGENDA:', fontsize=10, fontweight='bold')

    # Círculo verde (início)
    leg_start = plt.Circle((legend_x+1, legend_y+2), 0.5, color='green', ec='black')
    ax.add_patch(leg_start)
    ax.text(legend_x+2.5, legend_y+2, 'Evento de Início', fontsize=7, va='center')

    # Círculo vermelho (fim)
    leg_end = plt.Circle((legend_x+1, legend_y), 0.5, color='red', ec='black', linewidth=2)
    ax.add_patch(leg_end)
    ax.text(legend_x+2.5, legend_y, 'Evento de Fim', fontsize=7, va='center')

    # Tarefa
    leg_task = FancyBboxPatch((legend_x+18, legend_y+1.5), 2, 1,
                             boxstyle="round,pad=0.05",
                             edgecolor='black',
                             facecolor='lightblue')
    ax.add_patch(leg_task)
    ax.text(legend_x+21.5, legend_y+2, 'Tarefa/Atividade', fontsize=7, va='center')

    # Gateway XOR
    leg_xor = FancyBboxPatch((legend_x+32, legend_y+1.5), 1, 1,
                            boxstyle="round,pad=0.05",
                            edgecolor='orange',
                            facecolor='yellow')
    ax.add_patch(leg_xor)
    ax.text(legend_x+32.5, legend_y+2, 'XOR', fontsize=6, va='center', ha='center', fontweight='bold')
    ax.text(legend_x+34.5, legend_y+2, 'Gateway Exclusivo', fontsize=7, va='center')

    # Gateway AND
    leg_and = FancyBboxPatch((legend_x+46, legend_y+1.5), 1, 1,
                            boxstyle="round,pad=0.05",
                            edgecolor='green',
                            facecolor='lightgreen')
    ax.add_patch(leg_and)
    ax.text(legend_x+46.5, legend_y+2, 'AND', fontsize=6, va='center', ha='center', fontweight='bold')
    ax.text(legend_x+48.5, legend_y+2, 'Gateway Paralelo', fontsize=7, va='center')

    # Gateway OR
    leg_or = FancyBboxPatch((legend_x+60, legend_y+1.5), 1, 1,
                           boxstyle="round,pad=0.05",
                           edgecolor='purple',
                           facecolor='#E1BEE7')
    ax.add_patch(leg_or)
    ax.text(legend_x+60.5, legend_y+2, 'OR', fontsize=6, va='center', ha='center', fontweight='bold')
    ax.text(legend_x+62, legend_y+2, 'Gateway Inclusivo', fontsize=7, va='center')

    # Timer
    leg_timer = plt.Circle((legend_x+73, legend_y+2), 0.4, color='white', ec='orange', linewidth=1.5)
    ax.add_patch(leg_timer)
    ax.text(legend_x+74.5, legend_y+2, 'Evento de Tempo', fontsize=7, va='center')

    # Subprocesso
    leg_sub = FancyBboxPatch((legend_x+84, legend_y+1.3), 2.5, 1.4,
                            boxstyle="round,pad=0.05",
                            edgecolor='black',
                            facecolor='#FFF9C4',
                            linewidth=1.5)
    ax.add_patch(leg_sub)
    ax.text(legend_x+85.25, legend_y+2, 'Sub', fontsize=6, va='center', ha='center')
    ax.text(legend_x+85.25, legend_y+1.5, '[+]', fontsize=7, va='center', ha='center')
    ax.text(legend_x+87.5, legend_y+2, 'Subprocesso', fontsize=7, va='center')

    # Rodapé
    ax.text(50, 2, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")} | BLZ Clinic - Processo Melhorado',
           ha='center', fontsize=8, style='italic', color='gray')

    plt.tight_layout()
    return fig


def main():
    """Função principal"""
    print("="*70)
    print("  VISUALIZADOR DE BPMN MELHORADO - BLZ CLINIC")
    print("="*70)

    print("\n[1/2] Gerando visualizacao PNG...")
    fig = create_process_visualization()

    # Salvar PNG
    output_png = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\Processo_Fabricacao_BLZ_Clinic_VISUAL.png"
    fig.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] PNG salvo em: {output_png}")

    # Salvar PDF
    print("\n[2/2] Gerando documentacao PDF...")
    output_pdf = "C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\Processo_Fabricacao_BLZ_Clinic_VISUAL.pdf"
    fig.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"[OK] PDF salvo em: {output_pdf}")

    plt.close()

    print("\n" + "="*70)
    print("[OK] VISUALIZACAO CONCLUIDA!")
    print("="*70)
    print("\nArquivos gerados:")
    print(f"  1. Diagrama PNG: {output_png}")
    print(f"  2. Diagrama PDF: {output_pdf}")
    print(f"  3. Arquivo BPMN: C:\\Users\\User-OEM\\Documents\\DocumentoBPMN\\Processo_Fabricacao_BLZ_Clinic_MELHORADO.bpmn")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
