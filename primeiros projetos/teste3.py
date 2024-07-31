notas = []

for x in range(3):
    matricula = input("matricula: ")
    nome = input("nome: ")
    nota = float(input("nota: "))
    resultado = [matricula, nome, nota]
    notas.append(resultado)

print("quantidade de notas", len(notas))

for n in notas:
    matricula = n[0]
    nome = n[1]
    nota = n[2]
    print("O aluno", nome, "de matricula", matricula, "tirou a nota", nota)

    if nota >= 8:
        print("O aluno", nome, "da matrícula", matricula,
              "está aprovado com uma boa nota !")
    elif nota >= 6 and nota < 8:
        print("O aluno", nome, "da matrícula", matricula, "está aprovado !")
    else:
        print("O aluno", nome, "da matrícula", matricula, "está reprovado !")
    