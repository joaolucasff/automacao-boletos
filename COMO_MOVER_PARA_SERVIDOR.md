# 📁 Como Mover o Sistema para o Servidor

Este documento explica como mover o sistema de envio de boletos para um servidor compartilhado, permitindo que Juliana, Camila e outros usuários acessem o sistema de forma centralizada.

---

## 🎯 Objetivo

Centralizar o sistema em um servidor de rede para que múltiplos usuários possam:
- Acessar os mesmos boletos e notas fiscais
- Usar a mesma planilha de controle
- Trabalhar de forma colaborativa sem duplicação

---

## ⚡ Método Rápido (Recomendado)

### Passo 1: Copiar a pasta para o servidor

Copie o executável e arquivos necessários para o servidor:

```
De:   C:\Users\User-OEM\Desktop\BoletosAutomação\_build_server\dist\SistemaBoletosJotaJota.exe
Para: Z:\COBRANÇA\EnvioDeBoletosAutomatico\SistemaBoletosJotaJota.exe
```

**IMPORTANTE:** O sistema v11 usa arquitetura dinâmica - o config detecta automaticamente onde está rodando. Não precisa editar config.py!

---

### Passo 2: Atualizar o arquivo config.py

Abra o arquivo `config.py` no servidor e **mude apenas a linha 14**:

**ANTES:**
```python
BASE_DIR = r"C:\Users\User-OEM\Desktop\BoletosAutomação"
```

**DEPOIS:**
```python
BASE_DIR = r"\\SERVIDOR\Compartilhado\BoletosAutomação"
```

**Substitua `SERVIDOR` e `Compartilhado` pelos nomes corretos do seu servidor.**

---

### Passo 3: Testar a configuração

No servidor, execute o teste de configuração:

```bash
python config.py
```

Você verá uma mensagem confirmando se tudo está OK:

```
✅ Configuração válida! Sistema pronto para uso.
```

---

### Passo 4: Configurar os computadores dos usuários

Em cada computador (seu, Juliana, Camila), crie um atalho para a interface:

1. **Botão direito na área de trabalho** → Novo → Atalho
2. **Destino:** `\\SERVIDOR\Compartilhado\BoletosAutomação\InterfaceBoletos.py`
3. **Nome:** "Sistema de Boletos - Jota Jota"

Ou execute diretamente via linha de comando:

```bash
python \\SERVIDOR\Compartilhado\BoletosAutomação\InterfaceBoletos.py
```

---

## 🔄 Alternativa: Mapeamento de Rede

Se preferir usar uma letra de drive (Z:, Y:, etc), mapeie o servidor como unidade de rede:

### Windows:

1. Abra o **Explorador de Arquivos**
2. Clique em **Este Computador** → **Mapear unidade de rede**
3. Escolha uma letra (ex: `Z:`)
4. Digite o caminho: `\\SERVIDOR\Compartilhado\BoletosAutomação`
5. Marque "Reconectar ao fazer logon"

### Atualizar o config.py:

```python
BASE_DIR = r"Z:\BoletosAutomação"
```

---

## 📊 Estrutura de Pastas

Certifique-se de que a pasta copiada para o servidor contém:

```
BoletosAutomação/
├── config.py                              ← ARQUIVO PRINCIPAL DE CONFIGURAÇÃO
├── EnvioBoleto.py                         ← Script de envio
├── RenomeaçãoBoletos.py                   ← Script de renomeação
├── InterfaceBoletos.py                    ← Interface gráfica
├── Envio boletos - alterar dados.xlsx    ← Planilha de controle
├── BoletosEntrada/                        ← Boletos para renomear
├── BoletosRenomeados/                     ← Boletos renomeados
├── Notas/                                 ← Notas fiscais
├── Logs/                                  ← Logs do sistema
├── Erros/                                 ← Arquivos com erro
├── BoletosEnviados/                       ← Boletos já enviados
└── Outros/
    └── boletosTeste (temporario)/
        └── Imagem1.jpg                    ← Assinatura de email
```

---

## 🔒 Permissões Necessárias

Configure as permissões no servidor para que todos os usuários tenham:

- ✅ **Leitura**: em todos os arquivos
- ✅ **Escrita**: nas pastas de entrada/saída
- ✅ **Modificação**: na planilha Excel
- ✅ **Execução**: nos scripts Python

---

## 🧪 Teste Completo

Após configurar, teste o fluxo completo:

1. **Adicionar um boleto de teste** em `BoletosEntrada/`
2. **Executar a interface**: `python InterfaceBoletos.py`
3. **Renomear o boleto**
4. **Verificar** se apareceu em `BoletosRenomeados/`
5. **Adicionar nota fiscal correspondente** em `Notas/`
6. **Enviar boleto** (modo preview)
7. **Verificar** se Outlook abriu com o email

---

## ❓ Problemas Comuns

### Erro: "Pasta base não encontrada"

**Causa:** Caminho no `config.py` está errado

**Solução:** Verifique o caminho exato do servidor:
1. Abra o Explorador de Arquivos
2. Navegue até a pasta no servidor
3. Copie o caminho da barra de endereço
4. Cole no `config.py`

---

### Erro: "Acesso negado"

**Causa:** Usuário não tem permissões no servidor

**Solução:** Peça ao administrador da rede para:
1. Dar permissões de leitura/escrita/execução
2. Compartilhar a pasta com seu grupo de trabalho

---

### Erro: "Planilha não encontrada"

**Causa:** Arquivo Excel não foi copiado ou está com nome diferente

**Solução:** Verifique se o arquivo `Envio boletos - alterar dados.xlsx` existe na pasta raiz

---

### Lentidão ao abrir arquivos

**Causa:** Conexão lenta com o servidor

**Solução:**
1. Verifique a velocidade da rede
2. Se muito lento, considere mapear como unidade (Z:)
3. Ou trabalhe localmente e sincronize depois

---

## 📞 Suporte

Se tiver problemas após seguir este guia:

1. Execute `python config.py` e envie a saída
2. Verifique os logs em `Logs/`
3. Confirme que todos os arquivos foram copiados corretamente

---

## ✅ Checklist Final

Antes de começar a usar em produção:

- [ ] Pasta copiada para o servidor
- [ ] `config.py` atualizado com caminho correto
- [ ] Teste de configuração passou (`python config.py`)
- [ ] Todos os usuários conseguem acessar a pasta
- [ ] Permissões configuradas corretamente
- [ ] Planilha Excel abre sem erros
- [ ] Imagem de assinatura está acessível
- [ ] Teste completo de renomeação funcionou
- [ ] Teste completo de envio funcionou
- [ ] Outlook abre corretamente com os emails

---

## 🎉 Pronto!

Após seguir estes passos, o sistema estará centralizado no servidor e pronto para uso por toda a equipe!

**Lembre-se:** A partir de agora, para mudar qualquer caminho, basta editar **apenas a linha 14** do arquivo `config.py`!
