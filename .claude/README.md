# 📚 Documentação Claude - Sistema de Envio de Boletos

Esta pasta contém a documentação para facilitar a continuidade das conversas com Claude Code.

## Arquivos

### 📄 `context.md` - Contexto Geral do Projeto
**Use quando:** Iniciar nova sessão ou explicar o projeto
**Contém:**
- Visão geral do sistema
- Stack técnica
- Estrutura de pastas
- FIDCs suportados
- Fluxo de trabalho
- Problemas conhecidos

**Comando:**
```bash
claude chat --file .claude/context.md "Sua pergunta ou tarefa"
```

---

### 🎯 `decisions.md` - Decisões Técnicas
**Use quando:** Entender o "porquê" de escolhas técnicas
**Contém:**
- Decisões arquiteturais importantes
- Problemas resolvidos e como
- Alternativas consideradas
- Trade-offs

**Exemplo:**
- Por que usar modo PREVIEW ao invés de envio automático?
- Por que remover emojis Unicode?
- Por que centralizar config em `config.py`?

---

### 📅 `session-YYYY-MM-DD.md` - Sessões Diárias
**Use quando:** Retomar trabalho de uma sessão anterior
**Contém:**
- Problema trabalhado
- Soluções implementadas
- Arquivos modificados
- Testes realizados
- Pendências

**Comando para continuar:**
```bash
claude chat --file .claude/session-2025-10-31.md "Continuar de onde paramos"
```

---

## Como Usar

### Cenário 1: Iniciar Nova Funcionalidade
```bash
claude chat --file .claude/context.md "Preciso adicionar suporte para um novo FIDC chamado XYZ"
```

### Cenário 2: Continuar Bug de Ontem
```bash
claude chat --file .claude/session-2025-10-31.md "Vamos continuar o bug dos botões invisíveis"
```

### Cenário 3: Entender Por Que Algo Foi Feito Assim
```bash
claude chat --file .claude/decisions.md "Por que usamos modo PREVIEW ao invés de envio automático?"
```

### Cenário 4: Resumo Completo
```bash
claude chat --file .claude/context.md --file .claude/session-2025-10-31.md "Me traga up to speed"
```

### Cenário 5: Dentro do Chat
```
Leia os arquivos em .claude/ para entender o contexto do projeto.
Precisamos [sua tarefa aqui].
```

---

## Estrutura de Arquivos

```
.claude/
├── README.md              # Este arquivo
├── context.md             # Contexto geral (sempre atual)
├── decisions.md           # Decisões técnicas (histórico)
├── session-2025-10-31.md  # Sessão de hoje
└── session-YYYY-MM-DD.md  # Sessões futuras
```

---

## Quando Criar Novo Arquivo de Sessão

Crie um novo `session-YYYY-MM-DD.md` quando:
- ✅ Trabalhar em um problema/feature diferente
- ✅ Nova data (novo dia de trabalho)
- ✅ Sessão anterior ficou muito longa (>500 linhas)

**NÃO** crie novo arquivo se:
- ❌ Apenas continuando trabalho do mesmo dia
- ❌ Pequenas correções/ajustes
- ❌ Dúvidas rápidas

---

## Template para Nova Sessão

Copie e adapte:

```markdown
# Sessão YYYY-MM-DD - [Título do Trabalho]

## Resumo da Sessão
[O que foi feito hoje]

## Problema Inicial
### Sintoma
[O que estava acontecendo]

### Impacto
[Gravidade: 🔴 Crítico | 🟡 Importante | 🟢 Baixo]

## Solução Implementada
[O que foi feito]

## Arquivos Modificados
1. `caminho/arquivo.py` - [descrição]

## Testes Realizados
- [x] Teste 1
- [ ] Teste pendente

## Status Atual
### ✅ Concluído
- [x] Item concluído

### ⏳ Pendente
- [ ] Item pendente

## Próxima Sessão
[O que fazer na próxima vez]
```

---

## Manutenção

### Atualizar `context.md`
Quando houver mudanças estruturais:
- Nova tecnologia adicionada
- Mudança de arquitetura
- Novo problema conhecido importante
- Decisão que afeta todo o projeto

### Atualizar `decisions.md`
Sempre que tomar decisão técnica importante:
- Escolha de biblioteca/framework
- Padrão de código novo
- Mudança de abordagem
- Solução para problema complexo

### Criar Nova Sessão
No início de cada dia/tarefa nova

---

## Dicas

### ✅ Boas Práticas
- Sempre referencie pelo menos `context.md` ao iniciar
- Documente decisões importantes em `decisions.md`
- Mantenha sessões focadas (1 problema principal)
- Use checkboxes `[ ]` para rastrear pendências

### ❌ Evite
- Documentação muito genérica
- Copiar código completo (só trechos relevantes)
- Sessões muito longas (>1000 linhas)
- Deixar pendências sem documentar

---

**Criado em:** 2025-10-31
**Mantido por:** Claude Code + Usuário
**Propósito:** Melhorar continuidade entre sessões de desenvolvimento
