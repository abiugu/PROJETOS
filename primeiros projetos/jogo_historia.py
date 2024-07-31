import time


class JogoRPG:
    def __init__(self):
        self.inventario = []
        self.pontos = 0

    def escolher_opcao(self, opcoes):
        print("\nEscolha uma opção:")
        for i, opcao in enumerate(opcoes, start=1):
            print(f"{i}. {opcao}")

        escolha = input("Digite o número da opção escolhida: ")
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return int(escolha)
        else:
            print("Escolha inválida. Tente novamente.")
            return self.escolher_opcao(opcoes)

    def iniciar(self):
        print("Bem-vindo ao Jogo RPG!")

        print("\nVocê é um aventureiro em busca de fama e fortuna.")
        print("Sua jornada começa na pacata vila de Aventureirópolis.")

        opcoes = ["Explorar a vila", "Visitar a taverna",
                  "Aceitar uma missão na guilda"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            self.explorar_vila()
        elif escolha == 2:
            self.visitar_taverna()
        elif escolha == 3:
            self.aceitar_missao()

    def explorar_vila(self):
        print("\nVocê decide explorar a vila e conhecer os habitantes.")
        print("Encontra uma loja, uma forja e a casa do prefeito.")

        opcoes = ["Comprar itens na loja",
                  "Forjar uma nova arma", "Visitar o prefeito"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            print("\nVocê compra algumas poções e itens úteis.")
            self.inventario.extend(["Poção de Cura", "Pão de Viagem"])
            self.pontos += 20
            self.explorar_vila()
        elif escolha == 2:
            print("\nVocê forja uma nova espada afiada.")
            self.inventario.append("Espada Afiada")
            self.pontos += 30
            self.explorar_vila()
        elif escolha == 3:
            print("\nVocê visita o prefeito que lhe pede ajuda contra uma ameaça.")
            self.pontos += 40
            self.aceitar_missao()

    def visitar_taverna(self):
        print("\nVocê decide relaxar na taverna e conversar com os aventureiros locais.")
        print("Ouve rumores sobre uma caverna repleta de tesouros.")

        opcoes = ["Comprar uma bebida",
                  "Contratar um companheiro", "Investigar a caverna"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            print("\nVocê compra uma bebida e faz amizade com os frequentadores.")
            self.pontos += 10
            self.visitar_taverna()
        elif escolha == 2:
            print("\nVocê contrata um guerreiro experiente para acompanhá-lo.")
            self.inventario.append("Guerreiro Companheiro")
            self.pontos += 20
            self.visitar_taverna()
        elif escolha == 3:
            print("\nVocê decide investigar a caverna em busca de tesouros.")
            self.pontos += 30
            self.enfrentar_monstros()

    def aceitar_missao(self):
        print("\nVocê decide aceitar a missão do prefeito para eliminar uma ameaça nas proximidades.")
        print("Ele menciona uma caverna infestada de monstros.")

        opcoes = ["Preparar-se para a jornada",
                  "Recrutar aliados", "Partir imediatamente"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            print("\nVocê se prepara cuidadosamente para a jornada.")
            self.pontos += 20
            self.aceitar_missao()
        elif escolha == 2:
            print("\nVocê recruta alguns aldeões corajosos para ajudá-lo na missão.")
            self.inventario.append("Aldeões Aliados")
            self.pontos += 30
            self.aceitar_missao()
        elif escolha == 3:
            print("\nVocê parte imediatamente em direção à caverna.")
            self.pontos += 40
            self.enfrentar_monstros()

    def enfrentar_monstros(self):
        print("\nVocê chega à entrada da caverna e encontra uma horda de monstros hostis.")
        print("É hora de lutar pela sua vida!")

        opcoes = ["Atacar os monstros", "Usar magia",
                  "Tentar negociar com os monstros"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            print("\nVocê ataca ferozmente os monstros, derrotando muitos deles.")
            self.pontos += 30
            self.enfrentar_monstros()
        elif escolha == 2:
            print("\nVocê lança feitiços poderosos, enfraquecendo os monstros.")
            self.pontos += 40
            self.enfrentar_monstros()
        elif escolha == 3:
            print("\nVocê tenta negociar com os monstros, mas eles são implacáveis.")
            self.pontos -= 20
            self.enfrentar_monstros()

    def fim_jogo(self):
        print("\nParabéns! Você completou o Jogo RPG.")
        print(f"Sua pontuação final é: {self.pontos}")
        print("Obrigado por jogar!")


# ... (código anterior)


    def enfrentar_monstros(self):
        print("\nVocê chega à entrada da caverna e encontra uma horda de monstros hostis.")
        print("É hora de lutar pela sua vida!")

        opcoes = ["Atacar os monstros", "Usar magia",
                  "Tentar negociar com os monstros"]
        escolha = self.escolher_opcao(opcoes)

        if escolha == 1:
            print("\nVocê ataca ferozmente os monstros, derrotando muitos deles.")
            self.pontos += 30
            self.vitoria()
        elif escolha == 2:
            print("\nVocê lança feitiços poderosos, enfraquecendo os monstros.")
            self.pontos += 40
            self.vitoria()
        elif escolha == 3:
            print("\nVocê tenta negociar com os monstros, mas eles são implacáveis.")
            self.pontos -= 20
            self.derrota()

    def vitoria(self):
        print("\nVocê emerge vitorioso da caverna, tendo derrotado os monstros.")
        print("O povo de Aventureirópolis celebra sua coragem e heroísmo!")
        self.pontos += 50
        self.fim_jogo()

    def derrota(self):
        print("\nInfelizmente, você não conseguiu superar os monstros e sofre uma derrota.")
        print("Seu nome será lembrado, mas sua jornada chegou ao fim.")
        self.fim_jogo()

# ... (restante do código)


# Instanciar e iniciar o jogo
jogo_rpg = JogoRPG()
jogo_rpg.iniciar()
