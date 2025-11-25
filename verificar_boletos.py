import os

pasta = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletoscapital\boletos'

print("Verificando pasta de boletos...")
print(f"Caminho: {pasta}")
print(f"Existe: {os.path.exists(pasta)}")

if os.path.exists(pasta):
    arquivos = [f for f in os.listdir(pasta) if f.endswith('.pdf')]
    print(f"\nTotal de PDFs: {len(arquivos)}")
    print("\nPrimeiros 10 arquivos:")
    for arq in arquivos[:10]:
        print(f"  {arq}")
else:
    # Verificar pasta pai
    pasta_pai = r'C:\Users\User-OEM\Desktop\BoletosAutomação\testenovax.cred.capital.squid\boletoscapital'
    print(f"\nVerificando pasta pai: {pasta_pai}")
    if os.path.exists(pasta_pai):
        print("Conteúdo da pasta pai:")
        conteudo = os.listdir(pasta_pai)
        for item in conteudo:
            caminho_completo = os.path.join(pasta_pai, item)
            tipo = "DIR" if os.path.isdir(caminho_completo) else "FILE"
            print(f"  [{tipo}] {item}")
