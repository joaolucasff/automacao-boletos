# ================================================================
# CONFIGURAÇÃO CENTRALIZADA - Sistema de Envio de Boletos
# ================================================================
#
# Este arquivo centraliza TODOS os caminhos do sistema.
#
# COMO MOVER PARA O SERVIDOR:
# 1. Copie toda a pasta BoletosAutomação para o servidor
#    Exemplo: \\SERVIDOR\Compartilhado\BoletosAutomação
#
# 2. Mude APENAS a linha BASE_DIR abaixo para o novo caminho
#    Exemplo: BASE_DIR = r"\\SERVIDOR\Compartilhado\BoletosAutomação"
#
# 3. Pronto! Todos os scripts vão funcionar automaticamente
#
# ================================================================

import os

# ==================== CAMINHO BASE ====================
# 🔧 MUDE APENAS ESTA LINHA QUANDO MOVER PARA O SERVIDOR:
BASE_DIR = r"C:\Users\User-OEM\Desktop\BoletosAutomação"

# Exemplos de como configurar após mover:
# BASE_DIR = r"\\SERVIDOR\Compartilhado\BoletosAutomação"  # Servidor de rede
# BASE_DIR = r"Z:\BoletosAutomação"                         # Drive mapeado
# BASE_DIR = r"C:\Compartilhado\BoletosAutomação"          # Pasta local compartilhada

# ==================== PASTAS DO SISTEMA ====================
# Entrada e processamento
PASTA_ENTRADA = os.path.join(BASE_DIR, "BoletosEntrada")
PASTA_DESTINO = os.path.join(BASE_DIR, "BoletosRenomeados")
PASTA_RENOMEADOS = PASTA_DESTINO  # Alias para compatibilidade

# Notas fiscais e documentos
PASTA_NOTAS = os.path.join(BASE_DIR, "Notas")

# Organização de saída
PASTA_AUDITORIA = os.path.join(BASE_DIR, "Auditoria")
PASTA_LOGS = PASTA_AUDITORIA  # Alias para compatibilidade
PASTA_ERROS = os.path.join(BASE_DIR, "Erros")
PASTA_ENVIADOS = os.path.join(BASE_DIR, "BoletosEnviados")

# Arquivos de controle
PASTA_OUTROS = os.path.join(BASE_DIR, "Outros")

# ==================== ARQUIVOS ====================
# Planilha de controle
ARQUIVO_PLANILHA = os.path.join(BASE_DIR, "Envio boletos - alterar dados.xlsx")
ABA_PLANILHA = "Alterar dados"

# Assinatura de email
ASSINATURA_IMG = os.path.join(PASTA_OUTROS, "boletosTeste (temporario)", "Imagem1.jpg")

# Scripts principais
SCRIPT_RENOMEAR = os.path.join(BASE_DIR, "RenomeaçãoBoletos.py")
SCRIPT_ENVIAR = os.path.join(BASE_DIR, "EnvioBoleto.py")

# Logs
ARQUIVO_LOG_RENOMEACAO = os.path.join(PASTA_LOGS, "log_erros.txt")

# ==================== CONFIGURAÇÕES DE EMAIL ====================
EMAIL_CC_FIXO = "joaolucasfurtadofiel17@gmail.com"
EMAIL_CONTA_COBRANCA = "cobranca@jotajota.net.br"

# ==================== CONFIGURAÇÃO DE FIDCs ====================
FIDC_CONFIG = {
    "CAPITAL": {
        "nome": "CAPITAL",
        "nome_completo": "CAPITAL RS FIDC NP MULTISSETORIAL",
        "cnpj": "12.910.463/0001-70",
        "cc_emails": ["adm@jotajota.net.br"],
        "palavras_chave": ["CAPITAL RS", "CAPITAL RS FIDC"],
        "cor": "#0e639c"
    },
    "NOVAX": {
        "nome": "NOVAX",
        "nome_completo": "Novax Fundo de Invest. Em Dir. Cred.",
        "cnpj": "28.879.551/0001-96",
        "cc_emails": ["adm@jotajota.net.br", "controladoria@novaxfidc.com.br"],
        "palavras_chave": ["NOVAX", "NOVAX FIDC", "NOVAX FUNDO"],
        "cor": "#107c10"
    },
    "CREDVALE": {
        "nome": "CREDVALE",
        "nome_completo": "CREDVALE FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS MULTISSETORIAL",
        "cnpj": "28.194.817/0001-67",
        "cc_emails": ["adm@jotajota.net.br", "nichole@credvalefidc.com.br"],
        "palavras_chave": ["CREDVALE", "CREDVALE FUNDO", "CREDVALE FIDC"],
        "cor": "#d83b01"
    },
    "SQUID": {
        "nome": "SQUID",
        "nome_completo": "SQUID FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS",
        "cnpj": "28.849.641/0001-34",
        "cc_emails": ["adm@jotajota.net.br"],
        "palavras_chave": ["SQUID", "SQUID FIDC", "SQUID FUNDO"],
        "cor": "#8764b8"
    }
}

# FIDC padrão caso não consiga detectar
FIDC_PADRAO = "CAPITAL"

# ==================== CONFIGURAÇÕES GERAIS ====================
# Modo de operação
MODO_PREVIEW = True  # True = abre emails no Outlook sem enviar automaticamente

# Sistema de dados (v6.0 - XML Based)
USAR_PLANILHA = False  # Sistema agora usa XMLs das notas fiscais
USAR_IA = False  # Desabilitado para evitar travamento

# Validações e segurança
VALIDACAO_CNPJ_OBRIGATORIA = True  # Exige CNPJ para validação cruzada
TOLERANCIA_VALOR_CENTAVOS = 0  # Tolerância ZERO - valor deve ser EXATO
MAX_EMAILS_POR_CLIENTE = 2  # Máximo de emails válidos por cliente

# Configurações de IA (para extração de dados)
IA_TIMEOUT = 10  # Timeout em segundos para chamadas IA
IA_MODEL = "deepseek-r1:1.5b"  # Modelo Ollama
IA_TEMPERATURE = 0  # 0 = mais determinístico

# ==================== FUNÇÕES AUXILIARES ====================
def criar_pastas_necessarias():
    """
    Cria todas as pastas necessárias caso não existam.
    Execute esta função ao iniciar o sistema.
    """
    pastas = [
        PASTA_ENTRADA,
        PASTA_DESTINO,
        PASTA_NOTAS,
        PASTA_AUDITORIA,
        PASTA_ERROS,
        PASTA_ENVIADOS,
        PASTA_OUTROS
    ]

    for pasta in pastas:
        os.makedirs(pasta, exist_ok=True)

    return True

def validar_configuracao():
    """
    Valida se todos os caminhos essenciais existem.
    Retorna: (sucesso: bool, erros: list)
    """
    erros = []

    # Validar pasta base
    if not os.path.exists(BASE_DIR):
        erros.append(f"Pasta base não encontrada: {BASE_DIR}")
        return False, erros

    # Validar planilha
    if not os.path.exists(ARQUIVO_PLANILHA):
        erros.append(f"Planilha não encontrada: {ARQUIVO_PLANILHA}")

    # Validar assinatura
    if not os.path.exists(ASSINATURA_IMG):
        erros.append(f"Imagem de assinatura não encontrada: {ASSINATURA_IMG}")

    # Criar pastas se não existirem
    criar_pastas_necessarias()

    return len(erros) == 0, erros

def get_info_sistema():
    """
    Retorna informações sobre a configuração atual.
    Útil para debug e verificação.
    """
    import os
    return {
        "base_dir": BASE_DIR,
        "config_file": __file__,  # Mostra de onde o config.py foi carregado
        "modo_preview": MODO_PREVIEW,
        "usar_ia": USAR_IA,
        "fidcs_disponiveis": list(FIDC_CONFIG.keys()),
        "planilha_existe": os.path.exists(ARQUIVO_PLANILHA),
        "assinatura_existe": os.path.exists(ASSINATURA_IMG),
        "pasta_entrada_existe": os.path.exists(PASTA_ENTRADA),
        "boletos_entrada": len([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith('.pdf')]) if os.path.exists(PASTA_ENTRADA) else 0
    }

def salvar_emails_cc(fidc_key: str, emails: list) -> tuple[bool, str]:
    """
    Salva emails CC de um FIDC no arquivo config.py.
    Usado pela interface para permitir edição dos emails sem alterar código.

    Args:
        fidc_key: Chave do FIDC ("CAPITAL", "NOVAX", "CREDVALE", "SQUID")
        emails: Lista de emails para salvar

    Returns:
        (sucesso: bool, mensagem: str)
    """
    import re
    import shutil
    from datetime import datetime

    # Validar FIDC
    if fidc_key not in FIDC_CONFIG:
        return False, f"FIDC inválido: {fidc_key}"

    # Validar emails
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    for email in emails:
        if not email_regex.match(email.strip()):
            return False, f"Email inválido: {email}"

    try:
        # Caminho do config.py
        config_path = __file__

        # Criar backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{config_path}.backup_{timestamp}"
        shutil.copy2(config_path, backup_path)

        # Ler arquivo
        with open(config_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Criar nova lista de emails formatada
        emails_formatados = ', '.join([f'"{email.strip()}"' for email in emails])
        nova_linha_emails = f'"cc_emails": [{emails_formatados}]'

        # Substituir apenas a linha cc_emails do FIDC específico
        # Padrão: procurar dentro do bloco do FIDC
        padrao = rf'("{fidc_key}":\s*\{{[^}}]*)"cc_emails":\s*\[[^\]]*\]'
        substituicao = rf'\1{nova_linha_emails}'

        conteudo_novo = re.sub(padrao, substituicao, conteudo, flags=re.DOTALL)

        # Verificar se houve substituição
        if conteudo == conteudo_novo:
            return False, "Não foi possível encontrar a linha de emails no arquivo"

        # Salvar arquivo
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_novo)

        # Atualizar FIDC_CONFIG em memória
        FIDC_CONFIG[fidc_key]["cc_emails"] = [email.strip() for email in emails]

        return True, f"Emails salvos com sucesso! Backup: {backup_path}"

    except Exception as e:
        return False, f"Erro ao salvar emails: {str(e)}"

# ==================== INICIALIZAÇÃO ====================
if __name__ == "__main__":
    # Teste de configuração
    print("=" * 70)
    print("TESTE DE CONFIGURAÇÃO - Sistema de Envio de Boletos")
    print("=" * 70)
    print(f"\nPasta base: {BASE_DIR}")
    print(f"Modo preview: {'SIM' if MODO_PREVIEW else 'NÃO'}")
    print(f"Usar IA: {'SIM' if USAR_IA else 'NÃO'}")
    print(f"\nFIDCs configurados: {', '.join(FIDC_CONFIG.keys())}")

    print("\n" + "-" * 70)
    print("Validando configuração...")
    print("-" * 70)

    sucesso, erros = validar_configuracao()

    if sucesso:
        print("\n✅ Configuração válida! Sistema pronto para uso.")
    else:
        print("\n❌ Erros encontrados:")
        for erro in erros:
            print(f"   - {erro}")

    print("\n" + "=" * 70)
