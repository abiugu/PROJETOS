salario = float(input("Quanto voce ganha?:"))

if salario < 3000:
    print("ta começando")

elif salario >= 3000 and salario < 5000:
    print("melhorou, já pode jogar na cara")

elif salario >= 5000 and salario < 10000:
    print("ta seboso, melhor que isso vira um SEMIDEUS")

elif salario >= 10000 and salario < 15000:
    print("VOCE PROVOU QUE É UM ABSURDO, NÃO DEPENDE DE NINGUÉM")

else:
    print("Merecedor demais de tudo isso, parabéns !!")
