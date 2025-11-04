# Contexto do Projeto - Sistema de Envio de Boletos Jota Jota

## Sobre o Projeto
Sistema automatizado para envio de boletos bancários por email via Outlook, desenvolvido para a empresa Jota Jota. O sistema processa XMLs de notas fiscais, renomeia boletos com informações extraídas, e envia emails personalizados para cada destinatário com cópias para equipes específicas de cada FIDC.

## Stack Técnica
- **Linguagem:** Python 3.11+
- **Interface Gráfica:** Tkinter (tema dark moderno)
- **Automação de Email:** pywin32 (integração com Outlook via COM)
- **Processamento de Dados:**
  - openpyxl (leitura de planilhas Excel)
  - PyPDF2 (leitura de PDFs)
  - lxml (parsing de XMLs de notas fiscais)
- **Ambiente:** Windows (devido integração COM com Outlook)
- **Versionamento:** Git (repositório local)

## Estrutura do Projeto
```
BoletosAutomação/
├── .claude/                    # Documentação de contexto (esta pasta)
├── .venv/                      # Ambiente virtual Python
├── src/                        # Código-fonte principal
│   ├── InterfaceBoletos.py    # Interface gráfica (ARQUIVO PRINCIPAL)
│   ├── RenomeaçãoBoletos.py   # Script de renomeação
│   └── EnvioBoleto.py         # Script de envio de emails
├── Boletos/                    # Boletos originais (entrada)
├── BoletosRenomeados/         # Boletos processados (destino)
├── BoletosEnviados/           # Boletos já enviados (arquivo)
├── Notas/                     # XMLs de notas fiscais
├── config.py                  # Configurações centralizadas (FIDCs, pastas, emails)
├── Abrir_Interface.py         # Launcher do sistema
└── Planilha Boleto.xlsx       # Planilha com emails dos destinatários
```

## FIDCs Suportados
O sistema trabalha com 4 FIDCs (Fundos de Investimento em Direitos Creditórios):

1. **CAPITAL** (azul) - Capital Empreendedor
2. **NOVAX** (roxo) - Novax FIDC
3. **CREDVALE** (laranja) - Credvale FIDC
4. **SQUID** (verde) - Squid FIDC

Cada FIDC possui:
- Nome completo
- CNPJ
- Lista de emails em cópia (CC) editável via duplo clique
- Cor identificadora na interface

## Fluxo de Trabalho
1. **Preparação:** Usuário coloca boletos (PDFs) na pasta `Boletos/` e XMLs na pasta `Notas/`
2. **Seleção:** Usuário seleciona o FIDC na interface gráfica
3. **Renomeação:** Sistema lê XMLs, extrai dados (número documento, CNPJ, valor) e renomeia PDFs
   - Formato: `CNPJ - Nome Empresa - Nº Documento - R$ Valor.pdf`
4. **Validação:** Popup mostra resumo (quantidade, valor total, destinatários, emails CC)
5. **Envio:** Sistema abre cada email no Outlook (modo PREVIEW) para revisão manual antes do envio
6. **Arquivo:** Após envio, boletos são movidos para `BoletosEnviados/`

## Decisões Técnicas Importantes

### 1. Modo PREVIEW (Não Automático)
- **Decisão:** Emails abrem no Outlook para revisão manual, não são enviados automaticamente
- **Motivo:** Segurança e controle humano antes do envio de documentos financeiros

### 2. Extração Robusta de Dados
- **Problema:** XMLs e PDFs podem ter formatos variados
- **Solução:** Múltiplos padrões de regex para extrair valores e números de documento
- **Validação:** Sistema tenta 5 métodos diferentes antes de falhar

### 3. Interface sem Emojis Unicode
- **Problema:** Windows não renderiza emojis Unicode corretamente em Tkinter
- **Solução:** Substituir todos os emojis por texto ASCII ([OK], [ERRO], [!])
- **Exemplo:** `✅ ENVIAR` → `ENVIAR` (botão verde com bordas)

### 4. Configuração Centralizada
- **Arquivo:** `config.py`
- **Conteúdo:** Todos os caminhos de pastas, scripts, e configurações de FIDCs
- **Benefício:** Fácil manutenção e atualização de emails CC

### 5. Estrutura Dual de Arquivos
- **Raiz:** `InterfaceBoletos.py` (versão antiga, mantida por compatibilidade)
- **src/:** `InterfaceBoletos.py` (versão atual em uso)
- **Launcher:** `Abrir_Interface.py` importa da raiz, mas pode ser ajustado

## Padrões do Código

### Nomenclatura
- Variáveis: `snake_case` (ex: `fidc_selecionado`)
- Classes: `PascalCase` (ex: `InterfaceBoletos`)
- Constantes: `UPPER_CASE` (ex: `CORES`, `FIDCS`)
- Arquivos: `PascalCase.py` (ex: `EnvioBoleto.py`)

### Cores da Interface (Dark Theme)
```python
CORES = {
    'bg_principal': '#1e1e1e',    # Fundo principal
    'bg_secundario': '#2d2d2d',   # Cards
    'bg_botao': '#0e639c',        # Azul Microsoft
    'sucesso': '#107c10',         # Verde
    'aviso': '#ffa500',           # Laranja
    'erro': '#e81123',            # Vermelho
    'texto': '#ffffff'            # Branco
}
```

### Logging
- Tags coloridas: `'sucesso'`, `'erro'`, `'aviso'`, `'info'`
- Formato: `[OK]`, `[ERRO]`, `[AVISO]` para compatibilidade ASCII

### Tratamento de Erros
- Try-except em todas as operações de I/O
- Mensagens amigáveis via `messagebox`
- Log detalhado no console para debug

## Problemas Conhecidos

### 1. Botões Invisíveis no Popup (RESOLVIDO PARCIALMENTE)
- **Status:** Em investigação
- **Sintoma:** Botões ENVIAR e CANCELAR não aparecem no popup de confirmação
- **Causa Provável:** Emojis Unicode + problemas de layout/geometria no Tkinter Windows
- **Tentativas:**
  - ✅ Remover emojis Unicode dos botões
  - ✅ Alterar `relief=FLAT` para `relief=RAISED`
  - ✅ Adicionar `borderwidth=2`
  - ✅ Aumentar padding (`padx=10, pady=5`)
  - ✅ Cores hexadecimais explícitas
  - ⏳ Testar em ambiente real (pendente validação do usuário)

### 2. Arquivos Duplicados
- **Problema:** Dois arquivos `InterfaceBoletos.py` (raiz e src/)
- **Solução Temporária:** Editando `src/InterfaceBoletos.py` + adicionado path fix
- **Ação Futura:** Consolidar em um único arquivo

## Como Continuar uma Sessão

### Opção 1: Referenciar este arquivo
```bash
claude chat --file .claude/context.md "Continuar trabalhando no bug dos botões invisíveis"
```

### Opção 2: Ler sessão específica
```bash
claude chat --file .claude/session-2025-10-31.md "Retomar o trabalho de ontem"
```

### Opção 3: Mencionar no prompt
```
Leia o arquivo .claude/context.md para entender o projeto.
Precisamos continuar resolvendo o problema dos botões invisíveis no popup.
```

## Informações de Ambiente
- **SO:** Windows 10/11
- **Python:** Instalado via venv em `.venv/`
- **Outlook:** Instalado localmente (requisito para pywin32)
- **Pasta do Projeto:** `C:\Users\User-OEM\Desktop\BoletosAutomação`

## Próximos Passos Planejados
1. ✅ Validar se botões aparecem no popup após correções
2. Consolidar arquivos duplicados (raiz vs src/)
3. Adicionar testes automatizados
4. Implementar modo de envio automático (opcional, com confirmação extra)
5. Melhorar extração de dados com ML/OCR (futuro)

---
**Última atualização:** 2025-10-31
**Mantido por:** Claude Code + Usuário
