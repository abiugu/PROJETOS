# sem funcao

fluxo_caixa = []

print("-----------")
print("Fluxo de caixa")
print("1 - adicionar receita")
print("2 - adicionar despesa")
print("\n# Digite outro numero para encerrar #\n")


def adicionar_receita():
    nome = input("Nome: ")
    valor = float(input("Valor: "))
    fluxo_caixa.append({
        "nome": nome,
        "valor": valor
    })


def adicionar_despesa():
    nome = input("Nome: ")
    valor = float(input("Valor: "))
    fluxo_caixa.append({
        "nome": nome,
        "valor": -valor
    })


while True:
    opcao = int(input("Digite a opção: "))

    if opcao == 1:
        adicionar_receita()

    elif opcao == 2:
        adicionar_despesa()
    else:
        break

    total = 0
    for fc in fluxo_caixa:
        print("Nome: ", fc['nome'], ", valor: R$", fc['valor'])
        total = total + fc['valor']

        print(("Saldo atual: R$"), total)

