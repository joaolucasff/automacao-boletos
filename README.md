# Sistema de Automação de Boletos - Jota Jota

Sistema completo de automação para processamento, renomeação e envio de boletos bancários com integração de IA.

## 📋 Funcionalidades

- **Renomeação Inteligente**: Extração automática de dados de boletos PDF usando IA (Ollama/Mistral) com fallback para Regex
- **Envio Automatizado**: Sistema de email integrado com Outlook e validação tripla (CNPJ, Nome, Valor)
- **Interface Gráfica**: Interface moderna em tema dark para gerenciamento do fluxo
- **Suporte a 4 FIDCs**: Capital RS, Novax, Credvale e Squid
- **Logs Detalhados**: Rastreamento completo de todas as operações

## 🗂️ Estrutura do Projeto

```
BoletosAutomação/
│
├── src/                              # Código-fonte principal
│   ├── InterfaceBoletos.py          # Interface gráfica (v1.0.0)
│   ├── RenomeaçãoBoletos.py         # Módulo de renomeação (v9)
│   └── EnvioBoleto.py               # Módulo de envio (v6.0.0)
│
├── config/                           # Configurações
│   └── Envio boletos - alterar dados.xlsx
│
├── venv/                             # Ambiente virtual Python
│
├── BoletosEntrada/                   # [OPERACIONAL] Boletos para processar
├── BoletosRenomeados/                # [OPERACIONAL] Boletos processados
├── BoletosEnviados/                  # [OPERACIONAL] Boletos enviados
├── Notas/                            # [OPERACIONAL] Notas fiscais de referência
├── Logs/                             # [OPERACIONAL] Logs de execução
├── Erros/                            # [OPERACIONAL] Arquivos com erro
│
├── Outros/                           # Arquivos de desenvolvimento (arquivados)
│
├── Sistema_Boletos_JotaJota.exe     # Executável standalone
│
├── requirements.txt                  # Dependências Python
├── .gitignore                        # Arquivos ignorados pelo Git
└── README.md                         # Este arquivo

```

## 🚀 Instalação

### 1. Ativar o Ambiente Virtual

```bash
# Windows
.\venv\Scripts\activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Ollama (Opcional - para IA)

Para usar os recursos de IA, instale o Ollama:

```bash
# Baixe em: https://ollama.ai
ollama pull mistral
ollama pull deepseek-r1
```

## 💻 Como Usar

### Opção 1: Interface Gráfica (Recomendado)

```bash
python src/InterfaceBoletos.py
```

ou simplesmente execute:

```
Sistema_Boletos_JotaJota.exe
```

### Opção 2: Scripts Individuais

**Renomear Boletos:**
```bash
python src/RenomeaçãoBoletos.py
```

**Enviar Boletos:**
```bash
python src/EnvioBoleto.py
```

## 🔄 Fluxo de Trabalho

1. **Entrada**: Coloque os boletos PDF na pasta `BoletosEntrada/`
2. **Renomeação**: Execute a renomeação via interface (extrai CNPJ, vencimento, valor)
3. **Processamento**: Boletos renomeados vão para `BoletosRenomeados/`
4. **Validação**: Sistema valida contra notas em `Notas/`
5. **Envio**: Emails são criados no Outlook com anexos e destinatários corretos
6. **Arquivo**: Boletos enviados vão para `BoletosEnviados/`

## 📊 FIDCs Suportados

- **Capital RS** - CAPITAL RS FIDC NP MULTISSETORIAL
- **Novax** - Novax Fundo de Investimento em Direitos Creditórios
- **Credvale** - CREDVALE FUNDO DE INVESTIMENTO
- **Squid** - SQUID FUNDO DE INVESTIMENTO

## 🤖 Tecnologias

- **Python 3.x**
- **pdfplumber** - Extração de dados de PDF
- **openpyxl** - Manipulação de Excel
- **pywin32** - Integração com Outlook
- **Ollama + LangChain** - IA para extração inteligente
- **tkinter** - Interface gráfica

## 📝 Logs

Todos os logs são salvos em `Logs/` com o formato:
```
log_exec_YYYYMMDD_HHMMSS.txt
```

Cada log contém:
- Timestamp de execução
- Total de emails enviados
- Erros encontrados
- Métodos de matching utilizados
- Detalhes de cada operação

## ⚙️ Configuração

Edite o arquivo `config/Envio boletos - alterar dados.xlsx` para:
- Adicionar novos destinatários
- Atualizar CNPJs de empresas
- Modificar valores de referência

## 🔒 Segurança

- Dados sensíveis (PDFs, Excel) não são versionados (ver `.gitignore`)
- Use o MODO_PREVIEW para testar antes de enviar emails
- Logs não contém informações confidenciais

## 📦 Versões dos Módulos

- **InterfaceBoletos.py**: v1.0.0 (29/10/2025)
- **RenomeaçãoBoletos.py**: v9 (IA com Ollama/Mistral)
- **EnvioBoleto.py**: v6.0.0 (IA com DeepSeek + fallback)

## 🛠️ Desenvolvimento

Para criar um novo executável:

```bash
pyinstaller --onefile --windowed --name=Sistema_Boletos_JotaJota src/InterfaceBoletos.py
```

## 📧 Suporte

Para dúvidas ou problemas, verifique os logs em `Logs/` ou consulte a documentação técnica em `docs/`.

---

**Desenvolvido por:** Jota Jota
**Última atualização:** 30/10/2025
