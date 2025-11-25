"""
Verifica se há parcelas faltantes comparando XMLs com boletos renomeados
"""

import os
import re
from xml_nfe_reader import indexar_xmls_por_nota

# Carregar XMLs
print("Carregando XMLs...")
mapa = indexar_xmls_por_nota('Notas')

# Listar boletos renomeados
pasta = 'BoletosRenomeados'
arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.pdf')]

# Contar boletos por nota
boletos_por_nota = {}
for arquivo in arquivos:
    match = re.search(r'NF (\d+)', arquivo)
    if match:
        nota = match.group(1)
        if nota not in boletos_por_nota:
            boletos_por_nota[nota] = []
        boletos_por_nota[nota].append(arquivo)

print("\n" + "=" * 80)
print("COMPARACAO: XMLs vs Boletos Renomeados")
print("=" * 80)

total_parcelas_xml = 0
total_boletos_pasta = 0
notas_com_diferenca = []

for num, dados in sorted(mapa.items()):
    if len(num) != 6:  # Pular chaves longas
        continue

    dups = dados.get('duplicatas', [])
    parcelas_xml = len(dups) if dups else 1  # Se não tem duplicata, é 1 boleto
    boletos_pasta = len(boletos_por_nota.get(num, []))

    total_parcelas_xml += parcelas_xml
    total_boletos_pasta += boletos_pasta

    # Se tem diferença
    if parcelas_xml != boletos_pasta:
        valor_total_nota = dados.get('valor_total', 0)
        notas_com_diferenca.append({
            'numero': num,
            'nome': dados['nome'][:50],
            'xml_parcelas': parcelas_xml,
            'boletos_pasta': boletos_pasta,
            'faltam': parcelas_xml - boletos_pasta,
            'valor_total': valor_total_nota,
            'duplicatas': dups
        })

if notas_com_diferenca:
    print("\n[ATENCAO] Encontradas notas com parcelas faltantes:")
    print()

    valor_faltando_total = 0

    for nota in notas_com_diferenca:
        print(f"Nota {nota['numero']} - {nota['nome']}")
        print(f"  XML: {nota['xml_parcelas']} parcelas | Pasta: {nota['boletos_pasta']} boletos | Faltam: {nota['faltam']}")
        print(f"  Valor total da nota: R$ {nota['valor_total']}")

        if nota['duplicatas']:
            print(f"  Parcelas no XML:")
            for i, dup in enumerate(nota['duplicatas'], 1):
                print(f"    {i}. Venc {dup['vencimento']} | R$ {dup['valor']}")

            # Calcular valor faltando
            if nota['faltam'] > 0:
                # Assumir que faltam as últimas parcelas
                parcelas_faltantes = nota['duplicatas'][-nota['faltam']:]
                valor_faltante = sum(d['valor'] for d in parcelas_faltantes)
                valor_faltando_total += valor_faltante
                print(f"  Valor das parcelas faltantes: R$ {valor_faltante:.2f}")
        print()

    print("=" * 80)
    print(f"VALOR TOTAL FALTANDO: R$ {valor_faltando_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print("=" * 80)
else:
    print("\n[OK] Todas as notas tem o numero correto de boletos!")

print(f"\nRESUMO:")
print(f"  Total de parcelas nos XMLs: {total_parcelas_xml}")
print(f"  Total de boletos na pasta: {total_boletos_pasta}")
print(f"  Diferenca: {total_parcelas_xml - total_boletos_pasta}")
