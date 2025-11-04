# InterfaceBoletos.py - Interface Gráfica Moderna (Dark Theme)
# Sistema de Envio de Boletos - Jota Jota
# Versão: 1.0.0 - 29/10/2025

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import os
import sys
import io
import threading
import re
from pathlib import Path
import pythoncom

# Importar configuração centralizada (versão servidor com caminhos dinâmicos)
from config_server import (
    BASE_DIR,
    PASTA_ENTRADA,
    PASTA_DESTINO,
    PASTA_NOTAS,
    FIDC_CONFIG,
    criar_pastas_necessarias
)

# Importar funções dos scripts de processamento
from RenomeaçãoBoletos import processar_boletos
from EnvioBoleto import executar as executar_envio_boletos

# Cores do tema Dark Moderno
CORES = {
    'bg_principal': '#1e1e1e',      # Fundo principal (quase preto)
    'bg_secundario': '#2d2d2d',     # Fundo dos cards
    'bg_botao': '#0e639c',          # Azul escuro Microsoft
    'bg_botao_hover': '#1177bb',    # Azul hover
    'bg_selecionado': '#094771',    # Azul escuro selecionado
    'texto': '#ffffff',             # Texto branco
    'texto_secundario': '#cccccc',  # Texto cinza claro
    'sucesso': '#107c10',           # Verde sucesso
    'aviso': '#ffa500',             # Laranja aviso
    'erro': '#e81123',              # Vermelho erro
    'borda': '#3f3f3f'              # Borda sutil
}

# FIDCs disponíveis (importados do config.py, mantendo compatibilidade com nomes)
FIDCS = FIDC_CONFIG

# ==================== CLASSE PRINCIPAL ====================
class InterfaceBoletos:
    def __init__(self, root):
        criar_pastas_necessarias()

        self.root = root
        self.root.title("Sistema de Envio de Boletos - Jota Jota")
        self.root.geometry("900x700")
        self.root.configure(bg=CORES['bg_principal'])

        # Variáveis
        self.fidc_selecionado = None
        self.processo_ativo = False

        # Configurar estilo
        self.configurar_estilo()

        # Criar interface
        self.criar_interface()

        # Atualizar status inicial
        self.atualizar_status()

    def configurar_estilo(self):
        """Configura o estilo visual dos componentes"""
        style = ttk.Style()
        style.theme_use('clam')

        # Estilo da barra de progresso
        style.configure("Dark.Horizontal.TProgressbar",
                       troughcolor=CORES['bg_secundario'],
                       background=CORES['bg_botao'],
                       borderwidth=0)

    def criar_interface(self):
        """Cria toda a interface gráfica"""
        # Container principal
        main_container = tk.Frame(self.root, bg=CORES['bg_principal'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Cabeçalho
        self.criar_cabecalho(main_container)

        # Seleção de FIDC
        self.criar_secao_fidc(main_container)

        # Botões de ação
        self.criar_secao_acoes(main_container)

        # Status
        self.criar_secao_status(main_container)

        # Log
        self.criar_secao_log(main_container)

    def criar_cabecalho(self, parent):
        """Cria o cabeçalho da aplicação"""
        header_frame = tk.Frame(parent, bg=CORES['bg_principal'])
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Título
        titulo = tk.Label(header_frame,
                         text="Sistema de Envio de Boletos",
                         font=('Segoe UI', 24, 'bold'),
                         fg=CORES['texto'],
                         bg=CORES['bg_principal'])
        titulo.pack()

        # Subtítulo
        subtitulo = tk.Label(header_frame,
                            text="Jota Jota - Automação de Processos",
                            font=('Segoe UI', 10),
                            fg=CORES['texto_secundario'],
                            bg=CORES['bg_principal'])
        subtitulo.pack()

    def criar_secao_fidc(self, parent):
        """Cria a seção de seleção de FIDC"""
        # Container
        fidc_container = tk.Frame(parent, bg=CORES['bg_principal'])
        fidc_container.pack(fill=tk.X, pady=(0, 20))

        # Título da seção
        titulo = tk.Label(fidc_container,
                         text="Qual operação será enviada hoje?",
                         font=('Segoe UI', 14, 'bold'),
                         fg=CORES['texto'],
                         bg=CORES['bg_principal'])
        titulo.pack(pady=(0, 15))

        # Grid de botões FIDC
        grid_frame = tk.Frame(fidc_container, bg=CORES['bg_principal'])
        grid_frame.pack()

        self.botoes_fidc = {}

        # Primeira linha (Capital e Novax)
        linha1 = tk.Frame(grid_frame, bg=CORES['bg_principal'])
        linha1.pack(pady=5)

        self.criar_botao_fidc(linha1, 'CAPITAL', 0)
        self.criar_botao_fidc(linha1, 'NOVAX', 1)

        # Segunda linha (Credvale e Squid)
        linha2 = tk.Frame(grid_frame, bg=CORES['bg_principal'])
        linha2.pack(pady=5)

        self.criar_botao_fidc(linha2, 'CREDVALE', 0)
        self.criar_botao_fidc(linha2, 'SQUID', 1)

    def criar_botao_fidc(self, parent, fidc_key, column):
        """Cria um botão de FIDC"""
        info = FIDCS[fidc_key]

        btn = tk.Button(parent,
                       text=info['nome'],
                       font=('Segoe UI', 13, 'bold'),
                       fg=CORES['texto'],
                       bg=CORES['bg_secundario'],
                       activebackground=info['cor'],
                       activeforeground=CORES['texto'],
                       relief=tk.FLAT,
                       width=15,
                       height=2,
                       cursor='hand2',
                       command=lambda: self.selecionar_fidc(fidc_key))

        btn.grid(row=0, column=column, padx=10)

        # Efeitos hover
        btn.bind('<Enter>', lambda e: btn.config(bg=info['cor']))
        btn.bind('<Leave>', lambda e: btn.config(
            bg=info['cor'] if self.fidc_selecionado == fidc_key else CORES['bg_secundario']
        ))

        # Duplo clique para mostrar emails em cópia
        btn.bind('<Double-Button-1>', lambda e: self.mostrar_emails_fidc(fidc_key))

        self.botoes_fidc[fidc_key] = btn

    def criar_secao_acoes(self, parent):
        """Cria a seção de botões de ação"""
        # Container
        acoes_container = tk.Frame(parent, bg=CORES['bg_principal'])
        acoes_container.pack(fill=tk.X, pady=(0, 20))

        # Frame dos botões
        botoes_frame = tk.Frame(acoes_container, bg=CORES['bg_principal'])
        botoes_frame.pack()

        # Botão Renomear
        self.btn_renomear = tk.Button(botoes_frame,
                                      text="📁 RENOMEAR BOLETOS",
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=CORES['texto'],
                                      bg=CORES['bg_botao'],
                                      activebackground=CORES['bg_botao_hover'],
                                      activeforeground=CORES['texto'],
                                      relief=tk.FLAT,
                                      width=25,
                                      height=2,
                                      cursor='hand2',
                                      state=tk.DISABLED,
                                      command=self.renomear_boletos)
        self.btn_renomear.grid(row=0, column=0, padx=10)

        # Botão Enviar
        self.btn_enviar = tk.Button(botoes_frame,
                                    text="📧 ENVIAR BOLETOS",
                                    font=('Segoe UI', 12, 'bold'),
                                    fg=CORES['texto'],
                                    bg=CORES['sucesso'],
                                    activebackground='#0f9b0f',
                                    activeforeground=CORES['texto'],
                                    relief=tk.FLAT,
                                    width=25,
                                    height=2,
                                    cursor='hand2',
                                    state=tk.DISABLED,
                                    command=self.enviar_boletos)
        self.btn_enviar.grid(row=0, column=1, padx=10)

        # Efeitos hover
        self.btn_renomear.bind('<Enter>', lambda e: self.btn_renomear.config(bg=CORES['bg_botao_hover']) if self.btn_renomear['state'] == tk.NORMAL else None)
        self.btn_renomear.bind('<Leave>', lambda e: self.btn_renomear.config(bg=CORES['bg_botao']) if self.btn_renomear['state'] == tk.NORMAL else None)

        self.btn_enviar.bind('<Enter>', lambda e: self.btn_enviar.config(bg='#0f9b0f') if self.btn_enviar['state'] == tk.NORMAL else None)
        self.btn_enviar.bind('<Leave>', lambda e: self.btn_enviar.config(bg=CORES['sucesso']) if self.btn_enviar['state'] == tk.NORMAL else None)

    def criar_secao_status(self, parent):
        """Cria a seção de status"""
        # Container
        status_container = tk.Frame(parent, bg=CORES['bg_secundario'], relief=tk.FLAT)
        status_container.pack(fill=tk.X, pady=(0, 10), ipady=10)

        # Grid de status
        self.labels_status = {}

        status_items = [
            ('fidc', 'FIDC Selecionado:', 'Nenhum'),
            ('xmls', '📁 XMLs Disponíveis:', '...'),
            ('entrada', 'Boletos na Entrada:', '...'),
            ('destino', 'Boletos Renomeados:', '...')
        ]

        for idx, (key, label, valor_inicial) in enumerate(status_items):
            # Label
            lbl = tk.Label(status_container,
                          text=label,
                          font=('Segoe UI', 9, 'bold'),
                          fg=CORES['texto_secundario'],
                          bg=CORES['bg_secundario'])
            lbl.grid(row=idx//3, column=(idx%3)*2, sticky='w', padx=(20, 5), pady=2)

            # Valor
            val = tk.Label(status_container,
                          text=valor_inicial,
                          font=('Segoe UI', 9),
                          fg=CORES['texto'],
                          bg=CORES['bg_secundario'])
            val.grid(row=idx//3, column=(idx%3)*2+1, sticky='w', padx=(0, 20), pady=2)

            self.labels_status[key] = val

        # Label de status de processamento (substitui barra de progresso)
        self.label_processo = tk.Label(status_container,
                                       text="",
                                       font=('Segoe UI', 10, 'bold'),
                                       fg=CORES['aviso'],
                                       bg=CORES['bg_secundario'])
        self.label_processo.grid(row=3, column=0, columnspan=6, sticky='ew', padx=20, pady=(10, 0))

    def criar_secao_log(self, parent):
        """Cria a seção de log"""
        # Container
        log_container = tk.Frame(parent, bg=CORES['bg_principal'])
        log_container.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo = tk.Label(log_container,
                         text="Log de Execução",
                         font=('Segoe UI', 10, 'bold'),
                         fg=CORES['texto'],
                         bg=CORES['bg_principal'],
                         anchor='w')
        titulo.pack(fill=tk.X, pady=(0, 5))

        # Text area com scroll
        self.log_text = scrolledtext.ScrolledText(log_container,
                                                  font=('Consolas', 9),
                                                  fg=CORES['texto'],
                                                  bg=CORES['bg_secundario'],
                                                  insertbackground=CORES['texto'],
                                                  relief=tk.FLAT,
                                                  height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Tags de cores para o log
        self.log_text.tag_config('sucesso', foreground=CORES['sucesso'])
        self.log_text.tag_config('aviso', foreground=CORES['aviso'])
        self.log_text.tag_config('erro', foreground=CORES['erro'])
        self.log_text.tag_config('info', foreground=CORES['bg_botao'])

        # Mensagem inicial
        self.adicionar_log("Sistema iniciado. Selecione um FIDC para começar.", 'info')

        # Mostrar de onde está carregando (debug)
        from config_server import get_info_sistema
        info = get_info_sistema()
        self.adicionar_log(f"Carregando de: {info['base_dir']}", 'info')
        self.adicionar_log(f"Boletos na entrada: {info['boletos_entrada']}", 'info')

    # ==================== MÉTODOS DE CONTROLE ====================

    def selecionar_fidc(self, fidc_key):
        """Seleciona um FIDC"""
        self.fidc_selecionado = fidc_key

        # Atualizar visual dos botões
        for key, btn in self.botoes_fidc.items():
            if key == fidc_key:
                btn.config(bg=FIDCS[key]['cor'])
            else:
                btn.config(bg=CORES['bg_secundario'])

        # Atualizar status
        self.labels_status['fidc'].config(
            text=FIDCS[fidc_key]['nome'],
            fg=FIDCS[fidc_key]['cor']
        )

        # Habilitar botões
        self.btn_renomear.config(state=tk.NORMAL)
        self.btn_enviar.config(state=tk.NORMAL)

        # Log
        self.adicionar_log(f"FIDC selecionado: {FIDCS[fidc_key]['nome']}", 'sucesso')

        # Atualizar status
        self.atualizar_status()

    def mostrar_emails_fidc(self, fidc_key):
        """Mostra popup editável de emails CC para o FIDC selecionado (duplo clique)"""
        info = FIDCS[fidc_key]

        # Criar janela popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Editar Emails CC - {info['nome']}")
        popup.geometry("550x450")
        popup.configure(bg=CORES['bg_principal'])
        popup.resizable(False, False)

        # Centralizar na tela
        popup.transient(self.root)
        popup.grab_set()

        # Frame principal
        main_frame = tk.Frame(popup, bg=CORES['bg_principal'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        titulo = tk.Label(main_frame,
                         text=f"📧 Informações - {info['nome']}",
                         font=('Segoe UI', 14, 'bold'),
                         fg=CORES['texto'],
                         bg=CORES['bg_principal'])
        titulo.pack(pady=(0, 10))

        # Nome completo e CNPJ
        info_frame = tk.Frame(main_frame, bg=CORES['bg_secundario'], relief=tk.FLAT)
        info_frame.pack(fill=tk.X, pady=(0, 15), ipady=10)

        tk.Label(info_frame, text="Nome Completo:", font=('Segoe UI', 9, 'bold'),
                fg=CORES['texto_secundario'], bg=CORES['bg_secundario']).pack(anchor='w', padx=15)
        tk.Label(info_frame, text=info['nome_completo'], font=('Segoe UI', 9),
                fg=CORES['texto'], bg=CORES['bg_secundario']).pack(anchor='w', padx=15, pady=(0, 5))

        tk.Label(info_frame, text="CNPJ:", font=('Segoe UI', 9, 'bold'),
                fg=CORES['texto_secundario'], bg=CORES['bg_secundario']).pack(anchor='w', padx=15)
        tk.Label(info_frame, text=info['cnpj'], font=('Segoe UI', 9),
                fg=CORES['texto'], bg=CORES['bg_secundario']).pack(anchor='w', padx=15)

        # Lista de emails CC
        tk.Label(main_frame, text="📬 Emails em Cópia (CC):",
                font=('Segoe UI', 10, 'bold'),
                fg=CORES['texto'],
                bg=CORES['bg_principal']).pack(anchor='w', pady=(10, 5))

        # Frame da lista
        lista_frame = tk.Frame(main_frame, bg=CORES['bg_secundario'])
        lista_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Listbox com scrollbar
        scrollbar = tk.Scrollbar(lista_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(lista_frame,
                            font=('Consolas', 9),
                            fg=CORES['texto'],
                            bg=CORES['bg_secundario'],
                            selectbackground=info['cor'],
                            selectforeground=CORES['texto'],
                            relief=tk.FLAT,
                            yscrollcommand=scrollbar.set,
                            height=8)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Preencher lista
        for email in info['cc_emails']:
            listbox.insert(tk.END, email)

        # Botões de gerenciamento
        btn_frame = tk.Frame(main_frame, bg=CORES['bg_principal'])
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        def adicionar_email():
            """Adiciona novo email"""
            # Mini popup para entrada
            email = tk.simpledialog.askstring("Adicionar Email",
                                             "Digite o novo email:",
                                             parent=popup)
            if email:
                import re
                email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                if email_regex.match(email.strip()):
                    listbox.insert(tk.END, email.strip())
                else:
                    messagebox.showerror("Erro", "Email inválido!", parent=popup)

        def remover_email():
            """Remove email selecionado"""
            selecionado = listbox.curselection()
            if selecionado:
                listbox.delete(selecionado)
            else:
                messagebox.showwarning("Aviso", "Selecione um email para remover!", parent=popup)

        tk.Button(btn_frame, text="➕ Adicionar Email", font=('Segoe UI', 9),
                 fg=CORES['texto'], bg=CORES['sucesso'], relief=tk.FLAT,
                 cursor='hand2', command=adicionar_email).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="➖ Remover Email", font=('Segoe UI', 9),
                 fg=CORES['texto'], bg=CORES['erro'], relief=tk.FLAT,
                 cursor='hand2', command=remover_email).pack(side=tk.LEFT, padx=5)

        # Botões finais
        final_frame = tk.Frame(main_frame, bg=CORES['bg_principal'])
        final_frame.pack(fill=tk.X)

        def salvar():
            """Salva emails"""
            emails = list(listbox.get(0, tk.END))
            if len(emails) == 0:
                messagebox.showwarning("Aviso", "Adicione pelo menos 1 email!", parent=popup)
                return

            # Importar função de salvar
            from config_server import salvar_emails_cc
            sucesso, mensagem = salvar_emails_cc(fidc_key, emails)

            if sucesso:
                messagebox.showinfo("Sucesso", mensagem, parent=popup)
                self.adicionar_log(f"Emails CC do FIDC {info['nome']} atualizados", 'sucesso')
                popup.destroy()
            else:
                messagebox.showerror("Erro", mensagem, parent=popup)

        tk.Button(final_frame, text="💾 SALVAR", font=('Segoe UI', 10, 'bold'),
                 fg=CORES['texto'], bg=CORES['bg_botao'], width=15, height=2,
                 relief=tk.FLAT, cursor='hand2', command=salvar).pack(side=tk.LEFT, padx=5)

        tk.Button(final_frame, text="❌ CANCELAR", font=('Segoe UI', 10),
                 fg=CORES['texto'], bg=CORES['bg_secundario'], width=15, height=2,
                 relief=tk.FLAT, cursor='hand2', command=popup.destroy).pack(side=tk.LEFT, padx=5)

        # Log
        self.adicionar_log(f"Editando emails do FIDC {info['nome']}", 'info')

    def atualizar_status(self):
        """Atualiza as informações de status"""
        # Contar XMLs disponíveis
        try:
            xmls_count = len([f for f in os.listdir(PASTA_NOTAS) if f.lower().endswith('.xml')])
            if xmls_count > 0:
                self.labels_status['xmls'].config(text=f"{xmls_count} arquivos", fg=CORES['sucesso'])
            else:
                self.labels_status['xmls'].config(text="⚠️ Nenhum XML", fg=CORES['erro'])
                # Bloquear botões se não houver XMLs
                if self.fidc_selecionado:
                    self.btn_renomear.config(state=tk.DISABLED)
                    self.btn_enviar.config(state=tk.DISABLED)
        except:
            self.labels_status['xmls'].config(text="Pasta não encontrada", fg=CORES['erro'])

        # Contar boletos na entrada
        try:
            entrada_count = len([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith('.pdf')])
            self.labels_status['entrada'].config(text=f"{entrada_count} PDFs", fg=CORES['texto'])
        except:
            self.labels_status['entrada'].config(text="Pasta não encontrada", fg=CORES['erro'])

        # Contar boletos renomeados
        try:
            destino_count = len([f for f in os.listdir(PASTA_DESTINO) if f.lower().endswith('.pdf')])
            self.labels_status['destino'].config(text=f"{destino_count} PDFs", fg=CORES['texto'])
        except:
            self.labels_status['destino'].config(text="Pasta não encontrada", fg=CORES['erro'])

        # Reabilitar botões se XMLs estiverem OK e FIDC selecionado
        try:
            xmls_count = len([f for f in os.listdir(PASTA_NOTAS) if f.lower().endswith('.xml')])
            if xmls_count > 0 and self.fidc_selecionado:
                self.btn_renomear.config(state=tk.NORMAL)
                self.btn_enviar.config(state=tk.NORMAL)
        except:
            pass

    def adicionar_log(self, mensagem, tipo='info'):
        """Adiciona mensagem ao log"""
        self.log_text.insert(tk.END, f"{mensagem}\n", tipo)
        self.log_text.see(tk.END)
        self.root.update()

    def executar_script(self, funcao_executar, nome_processo):
        """Executa uma função de processamento em background"""
        if self.processo_ativo:
            messagebox.showwarning("Aviso", "Já existe um processo em execução!")
            return

        self.processo_ativo = True
        self.label_processo.config(text=f"⏳ {nome_processo}... Processando")
        self.adicionar_log(f"Iniciando: {nome_processo}...", 'info')

        def rodar():
            sucesso = False
            # Inicializar COM para esta thread (necessário para win32com/Outlook)
            pythoncom.CoInitialize()

            try:
                # Capturar stdout para mostrar no log
                old_stdout = sys.stdout
                sys.stdout = captured_output = io.StringIO()

                # Executar a função
                funcao_executar()

                # Restaurar stdout
                sys.stdout = old_stdout

                # Obter output capturado
                output = captured_output.getvalue()

                # Processar saída
                if output:
                    linhas_totais = output.split('\n')
                    total_linhas = len([l for l in linhas_totais if l.strip()])

                    for idx, linha in enumerate(linhas_totais, 1):
                        if linha.strip():
                            # Atualizar percentual aproximado
                            percentual = int((idx / total_linhas) * 100) if total_linhas > 0 else 0
                            self.label_processo.config(text=f"⏳ {nome_processo}... ({percentual}%)")

                            # Detectar tipo de mensagem
                            if '[OK]' in linha or 'sucesso' in linha.lower():
                                self.adicionar_log(linha.strip(), 'sucesso')
                            elif '[ERRO]' in linha or 'erro' in linha.lower():
                                self.adicionar_log(linha.strip(), 'erro')
                            elif '[AVISO]' in linha or 'aviso' in linha.lower():
                                self.adicionar_log(linha.strip(), 'aviso')
                            else:
                                self.adicionar_log(linha.strip(), 'info')

                # Considerar sucesso se não houve exceção
                sucesso = True
                self.label_processo.config(text=f"[OK] {nome_processo} concluido! (100%)")
                self.adicionar_log(f"{nome_processo} concluido com sucesso!", 'sucesso')
                messagebox.showinfo("Sucesso", f"{nome_processo} concluido!")

            except Exception as e:
                # Restaurar stdout em caso de erro
                sys.stdout = old_stdout

                self.adicionar_log(f"Erro ao executar: {str(e)}", 'erro')
                self.label_processo.config(text=f"[ERRO] Erro ao executar {nome_processo}")
                messagebox.showerror("Erro", f"Erro ao executar {nome_processo}:\n{str(e)}")

            finally:
                # Garantir que stdout sempre seja restaurado
                if sys.stdout != old_stdout:
                    sys.stdout = old_stdout

                # Finalizar COM desta thread
                pythoncom.CoUninitialize()

                self.processo_ativo = False
                # Limpar label de processo após 3 segundos
                self.root.after(3000, lambda: self.label_processo.config(text=""))
                self.atualizar_status()

        # Executar em thread separada
        thread = threading.Thread(target=rodar, daemon=True)
        thread.start()

    def renomear_boletos(self):
        """Executa o script de renomeação"""
        if not self.fidc_selecionado:
            messagebox.showwarning("Aviso", "Selecione um FIDC primeiro!")
            return

        # Verificar se há boletos
        try:
            count = len([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith('.pdf')])
            if count == 0:
                messagebox.showwarning("Aviso", "Não há boletos na pasta de entrada!")
                return
        except:
            messagebox.showerror("Erro", "Pasta de entrada não encontrada!")
            return

        self.executar_script(processar_boletos, "Renomeação de Boletos")

    def calcular_valor_total_boletos(self):
        """Calcula valor total dos boletos a partir dos nomes dos arquivos"""
        try:
            arquivos = [f for f in os.listdir(PASTA_DESTINO) if f.lower().endswith('.pdf')]
            valor_total = 0.0

            for arquivo in arquivos:
                # Extrair valor do nome: "... - R$ X.XXX,XX.pdf"
                match = re.search(r'R\$\s*([\d\.,]+)\.pdf$', arquivo)
                if match:
                    valor_str = match.group(1)
                    # Converter para float (substituir . por "" e , por .)
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                    try:
                        valor_total += float(valor_str)
                    except:
                        pass

            return valor_total
        except:
            return 0.0

    def mostrar_popup_resumo(self, count):
        """Mostra popup de resumo antes de enviar boletos"""
        info = FIDCS[self.fidc_selecionado]

        # Calcular valor total
        valor_total = self.calcular_valor_total_boletos()

        # Criar janela popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Confirmação de Envio - {info['nome']}")
        popup.geometry("550x550")  # AUMENTADO para garantir espaço para botões
        popup.configure(bg=CORES['bg_principal'])
        popup.resizable(False, False)

        # Centralizar na tela
        popup.transient(self.root)
        popup.grab_set()

        # Frame principal
        main_frame = tk.Frame(popup, bg=CORES['bg_principal'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        titulo = tk.Label(main_frame,
                         text=f"Confirmacao de Envio - {info['nome']}",
                         font=('Segoe UI', 14, 'bold'),
                         fg=CORES['texto'],
                         bg=CORES['bg_principal'])
        titulo.pack(pady=(0, 15))

        # Card de informações (SEM expand=True para não empurrar botões)
        info_frame = tk.Frame(main_frame, bg=CORES['bg_secundario'], relief=tk.FLAT)
        info_frame.pack(fill=tk.X, expand=False, pady=(0, 15), ipady=15)

        # Quantidade
        tk.Label(info_frame, text="Quantidade de Boletos:",
                font=('Segoe UI', 10, 'bold'),
                fg=CORES['texto_secundario'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(5, 2))
        tk.Label(info_frame, text=f"{count} boletos",
                font=('Segoe UI', 12, 'bold'),
                fg=info['cor'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(0, 10))

        # Valor total
        tk.Label(info_frame, text="Valor Total da Operacao:",
                font=('Segoe UI', 10, 'bold'),
                fg=CORES['texto_secundario'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(5, 2))
        valor_formatado = f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        tk.Label(info_frame, text=valor_formatado,
                font=('Segoe UI', 12, 'bold'),
                fg=CORES['sucesso'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(0, 10))

        # Destinatários
        tk.Label(info_frame, text="Destinatarios Unicos:",
                font=('Segoe UI', 10, 'bold'),
                fg=CORES['texto_secundario'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(5, 2))
        tk.Label(info_frame, text=f"{count} emails",
                font=('Segoe UI', 12),
                fg=CORES['texto'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(0, 10))

        # Emails em cópia
        tk.Label(info_frame, text="Emails em Copia (CC):",
                font=('Segoe UI', 10, 'bold'),
                fg=CORES['texto_secundario'],
                bg=CORES['bg_secundario']).pack(anchor='w', padx=20, pady=(5, 2))

        for email in info['cc_emails']:
            tk.Label(info_frame, text=f"  • {email}",
                    font=('Consolas', 9),
                    fg=CORES['texto'],
                    bg=CORES['bg_secundario']).pack(anchor='w', padx=30)

        # Aviso modo preview
        aviso_frame = tk.Frame(main_frame, bg=CORES['aviso'], relief=tk.FLAT)
        aviso_frame.pack(fill=tk.X, pady=(0, 15), ipady=8)
        tk.Label(aviso_frame, text="[!] MODO PREVIEW: Emails abrirao no Outlook para revisao",
                font=('Segoe UI', 9, 'bold'),
                fg=CORES['bg_principal'],
                bg=CORES['aviso']).pack()

        # Variável de retorno
        self.popup_result = False

        def confirmar():
            self.popup_result = True
            popup.destroy()

        def cancelar():
            self.popup_result = False
            popup.destroy()

        # Botões (USANDO GRID PARA CONTROLE PRECISO)
        btn_frame = tk.Frame(main_frame, bg=CORES['bg_principal'], height=80)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        btn_frame.pack_propagate(False)  # Impede que o frame encolha

        # Configurar grid do btn_frame
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # Botão ENVIAR (verde) - SEM emojis
        btn_enviar = tk.Button(btn_frame,
                               text="ENVIAR",
                               font=('Segoe UI', 14, 'bold'),
                               fg='#FFFFFF',
                               bg='#107c10',
                               activebackground='#0f9b0f',
                               activeforeground='#FFFFFF',
                               width=15,
                               height=2,
                               relief=tk.GROOVE,
                               borderwidth=3,
                               cursor='hand2',
                               command=confirmar)
        btn_enviar.grid(row=0, column=0, padx=15, pady=10, sticky='ew')

        # Botão CANCELAR (vermelho) - SEM emojis
        btn_cancelar = tk.Button(btn_frame,
                                 text="CANCELAR",
                                 font=('Segoe UI', 14, 'bold'),
                                 fg='#FFFFFF',
                                 bg='#e81123',
                                 activebackground='#ff2233',
                                 activeforeground='#FFFFFF',
                                 width=15,
                                 height=2,
                                 relief=tk.GROOVE,
                                 borderwidth=3,
                                 cursor='hand2',
                                 command=cancelar)
        btn_cancelar.grid(row=0, column=1, padx=15, pady=10, sticky='ew')

        # Aguardar resposta
        popup.wait_window()
        return self.popup_result

    def enviar_boletos(self):
        """Executa o script de envio"""
        if not self.fidc_selecionado:
            messagebox.showwarning("Aviso", "Selecione um FIDC primeiro!")
            return

        # Verificar se há boletos renomeados
        try:
            count = len([f for f in os.listdir(PASTA_DESTINO) if f.lower().endswith('.pdf')])
            if count == 0:
                messagebox.showwarning("Aviso", "Não há boletos renomeados para enviar!")
                return
        except:
            messagebox.showerror("Erro", "Pasta de destino não encontrada!")
            return

        # Mostrar popup de resumo
        resposta = self.mostrar_popup_resumo(count)

        if resposta:
            self.executar_script(executar_envio_boletos, "Envio de Boletos")

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceBoletos(root)
    root.mainloop()
