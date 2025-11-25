# 📘 Como Usar o Sistema de Boletos JotaJota

**Versão do Sistema:** v11 (Arquitetura em Camadas)
**Última atualização:** 05/11/2025

---

## 🎯 O que este sistema faz?

O Sistema de Boletos automatiza dois processos principais:

1. **Renomear boletos** com base nas informações dos XMLs das notas fiscais
2. **Enviar boletos por email** para os clientes com validação completa

Tudo de forma automática, rápida e organizada!

---

## 🚀 Como Abrir o Sistema

### No Servidor (Produção)

1. Acesse a pasta no servidor: `Z:\COBRANÇA\EnvioDeBoletosAutomatico\`
2. Dê duplo clique em: `SistemaBoletosJotaJota.exe`
3. A interface gráfica será aberta

**Ou use o atalho na área de trabalho:**
- Executar `criar_atalho_para_usuarios.bat` uma vez para criar atalho
- Depois, apenas clique no atalho "Sistema de Boletos - Jota Jota"

### Localmente (Desenvolvimento)

1. Navegue até: `C:\Users\User-OEM\Desktop\BoletosAutomação\`
2. Execute: `python InterfaceBoletos.py`

---

## 📋 Estrutura de Pastas

Entenda onde cada arquivo vai:

```
EnvioDeBoletosAutomatico/
│
├── Boletos/
│   ├── Entrada/          ← 📥 COLOQUE OS BOLETOS PDF AQUI
│   ├── Renomeados/       ← ✅ Boletos renomeados (prontos para envio)
│   └── Enviados/         ← 📧 Boletos já enviados (backup)
│
├── Notas/                ← 📄 COLOQUE OS XMLS DAS NOTAS AQUI
│
├── Auditoria/            ← 📊 Relatórios de processamento
│
└── Erros/                ← ❌ Arquivos com problema
```

---

## 🔄 Fluxo Completo de Trabalho

### Passo 1: Preparar os Arquivos

**Boletos:**
1. Baixe os boletos em PDF
2. Copie para: `Boletos\Entrada\`

**Notas Fiscais:**
1. Baixe os XMLs das notas fiscais (formato `.xml`)
2. Copie para: `Notas\`

> 💡 **Dica:** O sistema busca automaticamente os XMLs correspondentes aos boletos!

---

## 📝 ETAPA 1: Renomear Boletos

### O que faz?

Renomeia os boletos com informações extraídas dos XMLs:

**Formato do nome:**
```
NOME DO CLIENTE - NF 305818 - 25-11 - R$ 2.073,97.pdf
```

### Como usar:

1. Abra o sistema
2. Clique no botão **"Renomear Boletos"**
3. Aguarde o processamento
4. Veja o relatório na tela

### O sistema faz automaticamente:

✅ Lê o PDF do boleto
✅ Detecta o FIDC (CAPITAL, NOVAX, CREDVALE, SQUID)
✅ Busca o XML correspondente pelo CNPJ e número da nota
✅ Extrai nome do cliente, número da nota, vencimento e valor
✅ Renomeia o arquivo com padrão profissional
✅ Move para `Boletos\Renomeados\`
✅ Gera relatório de emails em `Auditoria\`

### Exemplo prático:

**ANTES:**
```
Boletos\Entrada\boleto_12345.pdf
```

**DEPOIS:**
```
Boletos\Renomeados\LC EMPREENDIMENTO IMOBILIARIO SPE LTDA - NF 305817 - 14-10 - R$ 4.347,33.pdf
```

---

## 📧 ETAPA 2: Enviar Boletos

### O que faz?

Cria emails personalizados para cada cliente com:
- Boleto(s) anexado(s)
- Nota(s) fiscal(is) anexada(s)
- Corpo de email profissional
- CCs automáticos por FIDC
- Validação em 5 camadas

### Como usar:

1. Certifique-se de que os boletos estão em `Boletos\Renomeados\`
2. Certifique-se de que os XMLs estão em `Notas\`
3. Abra o sistema
4. Clique no botão **"Enviar Boletos"**
5. Aguarde o processamento
6. **Revise cada email** que abrir no Outlook
7. Clique em **"Enviar"** em cada email

### O sistema faz automaticamente:

✅ Valida CNPJ do boleto com o XML
✅ Valida valor do boleto (parcela correta)
✅ Busca emails válidos no XML
✅ Agrupa múltiplos boletos do mesmo cliente
✅ Cria email profissional no Outlook
✅ Anexa boletos e notas
✅ Adiciona assinatura da empresa
✅ Configura CCs por FIDC
✅ Move boletos enviados para `Boletos\Enviados\`
✅ Gera relatórios detalhados em `Auditoria\`

### Corpo do Email (exemplo):

```
Boa tarde,

Prezado cliente,
LC EMPREENDIMENTO IMOBILIARIO SPE LTDA,

Enviamos anexo o(s) seu(s) boleto(s) emitido(s) conforme a(as) nota(as): 305817
Valor: R$ 4.347,33, Vencimento: 14/10
Valor: R$ 4.347,33, Vencimento: 28/10
Valor: R$ 4.347,33, Vencimento: 30/09

O(s) boleto(s) está(ão) com beneficiário nominal a CAPITAL RS FIDC NP MULTISSETORIAL, CNPJ: 12.910.463/0001-70.

Vide boleto(s) e nota(s) em anexo.
Favor confirmar recebimento.

Em caso de dúvidas, nossa equipe permanece à disposição para esclarecimentos.

Atenciosamente,
Equipe de Cobrança
```

---

## 🔍 Sistema de Validação (5 Camadas)

O sistema valida cada boleto em 5 etapas:

### Camada 1: XML
✅ Verifica se existe XML correspondente ao número da nota

### Camada 2: CNPJ
✅ Compara CNPJ do boleto com CNPJ do XML

### Camada 3: Nome
✅ Valida nome do cliente (similaridade > 70%)

### Camada 4: Valor
✅ Compara valor do boleto com duplicata no XML (tolerância zero)

### Camada 5: Email
✅ Verifica se existem emails válidos no XML (mínimo 1, máximo 2)

> ⚠️ **Importante:** Se alguma camada falhar, o boleto é **rejeitado** e vai para a pasta `Erros\`

---

## 📊 Relatórios e Auditoria

Após cada execução, o sistema gera relatórios em `Auditoria\`:

### 1. Relatório de Aprovados
`aprovados_YYYYMMDD_HHMMSS.txt`

Lista todos os boletos enviados com sucesso

### 2. Relatório de Rejeitados
`rejeitados_YYYYMMDD_HHMMSS.txt`

Lista boletos com erro e o motivo

### 3. Relatório JSON
`auditoria_YYYYMMDD_HHMMSS.json`

Dados estruturados completos (para análise)

### 4. Relatório de Emails (Renomeação)
`relatorio_emails_YYYYMMDD_HHMMSS.txt`

Lista todos os emails extraídos agrupados por FIDC

---

## 🎨 Sistema de FIDCs

O sistema identifica automaticamente 4 FIDCs:

### 🔵 CAPITAL RS
- **CNPJ:** 12.910.463/0001-70
- **Palavras-chave:** "CAPITAL RS", "CAPITAL RS FIDC"
- **CCs:** adm@jotajota.net.br

### 🟢 NOVAX
- **CNPJ:** 28.879.551/0001-96
- **Palavras-chave:** "NOVAX", "NOVAX FIDC"
- **CCs:** adm@jotajota.net.br, controladoria@novaxfidc.com.br

### 🟠 CREDVALE
- **CNPJ:** 28.194.817/0001-67
- **Palavras-chave:** "CREDVALE", "CREDVALE FUNDO"
- **CCs:** adm@jotajota.net.br, nichole@credvalefidc.com.br

### 🟣 SQUID
- **CNPJ:** 28.849.641/0001-34
- **Palavras-chave:** "SQUID", "SQUID FIDC"
- **CCs:** adm@jotajota.net.br

---

## ⚙️ Configurações Importantes

### Modo Preview (Padrão: ATIVO)

O sistema está configurado em **modo preview**:
- ✅ Abre os emails no Outlook sem enviar
- ✅ Você revisa cada email
- ✅ Você clica "Enviar" manualmente

> 💡 **Recomendado:** Manter sempre em modo preview para segurança!

### Conta de Email

O sistema usa a conta: **cobranca@jotajota.net.br**

> ⚠️ Esta conta precisa estar configurada no Outlook

---

## ❌ Problemas Comuns e Soluções

### Erro: "XML não encontrado"

**Causa:** Não existe XML na pasta `Notas\` para o número da nota do boleto

**Solução:**
1. Verifique o número da nota no boleto
2. Baixe o XML correspondente
3. Coloque em `Notas\`
4. Execute novamente

---

### Erro: "CNPJ não corresponde"

**Causa:** CNPJ do boleto é diferente do CNPJ no XML

**Solução:**
1. Verifique se o XML é da nota correta
2. Confira se o boleto é do cliente correto
3. Se estiver tudo certo, pode ser erro no PDF (entre em contato com suporte)

---

### Erro: "Valor não corresponde"

**Causa:** Valor no boleto é diferente da duplicata no XML

**Solução:**
1. Verifique se o boleto é da parcela correta
2. Confira os valores no XML (tag `<dup>`)
3. Veja se há diferença de centavos (sistema exige valor EXATO)

---

### Erro: "Nenhum email encontrado"

**Causa:** XML não tem emails válidos

**Solução:**
1. Abra o XML em um editor de texto
2. Procure pela tag `<email>`
3. Se não tiver ou estiver incompleto, contate o cliente para atualizar

---

### Outlook não abre os emails

**Causa:** Conta de cobrança não configurada

**Solução:**
1. Abra o Outlook
2. Verifique se a conta `cobranca@jotajota.net.br` está ativa
3. Configure se necessário

---

## 🔧 Arquitetura v11 - Extractors Isolados

O sistema atual usa **arquitetura em camadas** (v11):

### Vantagens:

✅ **Cada FIDC é independente**
Mudanças no CAPITAL não afetam NOVAX, CREDVALE ou SQUID

✅ **Match inteligente por número de nota**
Sistema prioriza match direto pelo número da nota (mais preciso)

✅ **Fallback robusto**
Se não encontrar por número, busca por CNPJ + vencimento

✅ **Zero regressões**
Alterações em um extractor não quebram outros

---

## 📞 Suporte e Ajuda

### Em caso de dúvidas:

1. Consulte este documento primeiro
2. Verifique os relatórios em `Auditoria\`
3. Veja os logs de erro em `Erros\`
4. Entre em contato com o suporte técnico

### Arquivos úteis:

- `COMO_USAR.md` ← Este documento
- `COMO_MOVER_PARA_SERVIDOR.md` ← Guia de instalação no servidor
- `TESTE_PRODUCAO_V11.md` ← Documentação técnica
- `ORGANIZACAO.md` ← Estrutura do código

---

## ✅ Checklist Diário

Antes de processar os boletos:

- [ ] Boletos PDF em `Boletos\Entrada\`
- [ ] XMLs das notas em `Notas\`
- [ ] Outlook aberto com conta de cobrança
- [ ] Sistema aberto (`SistemaBoletosJotaJota.exe`)

Durante o processamento:

- [ ] Renomear boletos primeiro
- [ ] Verificar relatório de renomeação
- [ ] Conferir se todos os boletos foram renomeados
- [ ] Enviar boletos
- [ ] Revisar cada email no Outlook
- [ ] Conferir anexos (boleto + nota)
- [ ] Verificar destinatários e CCs
- [ ] Enviar emails

Após o envio:

- [ ] Conferir relatório de aprovados
- [ ] Verificar se há rejeitados
- [ ] Boletos movidos para `Enviados\`
- [ ] Arquivar relatórios de auditoria

---

## 🎉 Dicas Profissionais

### 1. Organize seus XMLs
Mantenha apenas os XMLs necessários na pasta `Notas\`. Arquive os antigos.

### 2. Use nomes descritivos
Se baixar boletos manualmente, renomeie com algo significativo antes de processar.

### 3. Revise sempre os emails
Mesmo com validação automática, sempre revise antes de enviar.

### 4. Mantenha backup
Os relatórios em `Auditoria\` são importantes. Faça backup regular.

### 5. Processe em lotes
Agrupe boletos por dia ou semana para facilitar a organização.

---

## 📈 Estatísticas do Sistema

Com a arquitetura v11, o sistema alcançou:

- ✅ **100% de taxa de sucesso** em testes (117 boletos)
- ✅ **Zero erros** de matching com match inteligente
- ✅ **Extração automática** de emails dos XMLs
- ✅ **Validação rigorosa** em 5 camadas
- ✅ **Relatórios profissionais** para auditoria

---

**Sistema de Boletos JotaJota - Desenvolvido com ❤️ para automatizar seu trabalho!**
