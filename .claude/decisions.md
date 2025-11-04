# Decisões Técnicas - Sistema de Envio de Boletos

> Registro de decisões importantes tomadas durante o desenvolvimento

---

## [2025-10-31] Remover Emojis Unicode da Interface

### Contexto
Os botões "ENVIAR" e "CANCELAR" no popup de confirmação estavam invisíveis no Windows.

### Problema
- Tkinter no Windows não renderiza emojis Unicode corretamente
- Botões tinham texto: `"✅ ENVIAR"` e `"❌ CANCELAR"`
- Resultado: Botões apareciam em branco, sem texto visível

### Decisão
Remover TODOS os emojis Unicode da interface e substituir por:
- Texto ASCII puro para botões: `"ENVIAR"`, `"CANCELAR"`
- Marcadores ASCII para status: `[OK]`, `[ERRO]`, `[!]`
- Cores e bordas para indicação visual

### Implementação
```python
# ANTES (com emojis)
tk.Button(text="✅ ENVIAR", relief=tk.FLAT, ...)

# DEPOIS (sem emojis)
tk.Button(text="ENVIAR",
          relief=tk.RAISED,
          borderwidth=2,
          bg='#107c10',  # Verde
          fg='#FFFFFF',  # Branco
          ...)
```

### Alternativas Consideradas
1. ❌ Usar fonte que suporte emojis → Complexo, não garantido no Windows
2. ❌ Usar imagens PNG → Overhead desnecessário
3. ✅ **Texto puro + cores + bordas** → Simples, universal, performático

### Status
⏳ Parcialmente implementado - aguardando validação do usuário

---

## [2025-10-31] Centralização de Configurações em config.py

### Contexto
Informações de FIDCs, emails CC, e caminhos de pastas estavam espalhados no código.

### Problema
- Difícil atualizar emails de cópia
- Mudanças exigiam edição de múltiplos arquivos
- Risco de inconsistências

### Decisão
Criar arquivo `config.py` centralizado com:
- Dicionário `FIDC_CONFIG` com todos os FIDCs
- Constantes para caminhos de pastas
- Função `salvar_emails_cc()` para persistência em JSON

### Implementação
```python
# config.py
FIDC_CONFIG = {
    'CAPITAL': {
        'nome': 'CAPITAL',
        'nome_completo': 'Capital Empreendedor FIDC',
        'cnpj': '12.345.678/0001-90',
        'cc_emails': ['email1@example.com', 'email2@example.com'],
        'cor': '#0078d4'
    },
    # ...
}
```

### Benefícios
- ✅ Interface permite edição de emails via duplo clique
- ✅ Alterações persistidas em `fidc_config.json`
- ✅ Único ponto de verdade para configurações

### Status
✅ Implementado e funcionando

---

## [2025-10-31] Modo PREVIEW para Envio de Emails

### Contexto
Sistema precisa enviar boletos por email, mas são documentos financeiros críticos.

### Problema
- Envio automático é arriscado (erro pode enviar para destinatário errado)
- Necessidade de revisão humana antes do envio

### Decisão
Implementar **modo PREVIEW**:
- Sistema cria emails no Outlook mas NÃO envia
- Cada email abre para revisão manual
- Usuário pode editar, revisar e enviar manualmente

### Implementação
```python
# Criar email mas NÃO chamar .Send()
mail = outlook.CreateItem(0)
mail.To = destinatario
mail.Subject = assunto
mail.Body = corpo
mail.Attachments.Add(caminho_boleto)
mail.Display(False)  # Abrir sem enviar
# NÃO: mail.Send()
```

### Alternativas Consideradas
1. ❌ Envio automático direto → Muito arriscado
2. ❌ Confirmação única para todos → Usuário não pode revisar cada email
3. ✅ **PREVIEW email por email** → Controle total, seguro

### Limitações
- Processo manual (mais lento)
- Requer Outlook instalado e configurado

### Status
✅ Implementado e preferido pelo usuário

---

## [2025-10-31] Extração Multi-Padrão de Dados de XML/PDF

### Contexto
XMLs de notas fiscais e PDFs de boletos têm formatos variados de diferentes bancos/emissores.

### Problema
- Regex único falha em arquivos com formato diferente
- Sistema travava ao não encontrar dados

### Decisão
Implementar **busca com fallback em múltiplos padrões**:
- 5 padrões diferentes para extrair valores
- 3 padrões para número de documento
- Se um falha, tenta o próximo

### Implementação
```python
# Padrões de valor (ordenados por especificidade)
padroes_valor = [
    r'<vNF>([\d,.]+)</vNF>',
    r'Valor Total.*?R\$\s*([\d.,]+)',
    r'(?:Total|Valor).*?([\d]{1,3}(?:\.\d{3})*,\d{2})',
    # ... mais padrões
]

for padrao in padroes_valor:
    match = re.search(padrao, conteudo)
    if match:
        valor = processar_valor(match.group(1))
        break
```

### Benefícios
- ✅ Robustez: funciona com variações de formato
- ✅ Recuperação: fallback automático
- ✅ Logging: mostra qual padrão funcionou

### Limitações
- Pode aceitar falsos positivos se padrões forem muito genéricos
- Difícil manter com muitos padrões

### Status
✅ Implementado com 5 padrões para valores

---

## [2025-10-31] Estrutura Dual de Arquivos (Raiz vs src/)

### Contexto
Projeto tinha arquivos duplicados: `InterfaceBoletos.py` na raiz e em `src/`.

### Problema
- Confusão sobre qual arquivo editar
- Imports quebrando dependendo de onde executa

### Decisão Temporária
- Manter `src/InterfaceBoletos.py` como versão ativa
- Adicionar `sys.path` fix para importar `config.py` da raiz
- Usar `Abrir_Interface.py` como launcher unificado

### Implementação
```python
# src/InterfaceBoletos.py
import sys
from pathlib import Path

BASE_DIR_LOCAL = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR_LOCAL))

from config import FIDC_CONFIG  # Agora funciona!
```

### Decisão Futura
⏳ **Consolidar em estrutura única:**
```
BoletosAutomação/
├── src/
│   ├── interface_boletos.py
│   ├── renomear_boletos.py
│   ├── enviar_boletos.py
│   └── config.py  # Mover para src/
└── main.py  # Launcher único
```

### Status
⏳ Temporário - precisa refatoração futura

---

## [2025-10-31] Dark Theme na Interface

### Contexto
Interface Tkinter padrão é clara e pouco moderna.

### Decisão
Implementar **tema escuro personalizado** inspirado no VS Code:
- Fundo: `#1e1e1e` (quase preto)
- Cards: `#2d2d2d` (cinza escuro)
- Texto: `#ffffff` (branco)
- Cores semânticas: verde (sucesso), vermelho (erro), laranja (aviso)

### Benefícios
- ✅ Visual moderno e profissional
- ✅ Reduz fadiga visual
- ✅ Destaca informações importantes com cores

### Implementação
```python
CORES = {
    'bg_principal': '#1e1e1e',
    'bg_secundario': '#2d2d2d',
    'sucesso': '#107c10',
    'erro': '#e81123',
    # ...
}
```

### Status
✅ Implementado

---

## Template para Novas Decisões

```markdown
## [YYYY-MM-DD] Título da Decisão

### Contexto
[Situação que motivou a decisão]

### Problema
[Problema específico a resolver]

### Decisão
[Decisão tomada e justificativa]

### Implementação
[Código ou pseudocódigo relevante]

### Alternativas Consideradas
1. Opção A → Motivo de rejeição
2. Opção B → Motivo de rejeição
3. ✅ **Opção C** → Escolhida

### Benefícios
- Benefício 1
- Benefício 2

### Limitações
- Limitação 1
- Limitação 2

### Status
[✅ Implementado | ⏳ Parcial | ❌ Revertido]
```

---
**Última atualização:** 2025-10-31
