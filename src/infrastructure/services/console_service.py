import os
import sys
import time

from src.core.interfaces.i_view import IView


class ConsoleService(IView):
    """_summary_ Gerencia toda a interação com o usuário através do terminal. É responsável por limpar a tela, exibir menus de opções, capturar e validar a entrada do usuário (seleção única ou múltipla) e exibir mensagens de processamento ou erro com formatação de cores.

    Args:
        IView (_type_): _description_
    """

    def display_menu(
        self,
        opcoes: list[str],
        mensagem="Selecione uma opção:",
        selecionar_todos=False,
        permitir_voltar=False,
    ):
        """Exibe um menu de opções no console."""
        self.clear_console()
        print(mensagem)
        if selecionar_todos:
            print("0. TODOS")
        for i, opcao in enumerate(opcoes, start=1):
            print(f"{i}. {opcao}")

        print()
        if permitir_voltar:
            print("V. VOLTAR")
        print("X. SAIR\n")

    def get_user_input(
        self,
        opcoes: list[str],
        selecionar_todos=False,
        permitir_voltar=False,
        multipla_escolha=False,
    ) -> list[str] | None:
        """Obtém e valida a entrada do usuário a partir do menu exibido."""
        if not multipla_escolha:
            while True:
                escolha = input("Digite o número correspondente: ").strip().upper()

                if escolha == "X":
                    sys.exit()
                elif permitir_voltar and escolha == "V":
                    return None
                elif selecionar_todos and escolha == "0":
                    return opcoes
                elif escolha.isdigit() and int(escolha) in range(1, len(opcoes) + 1):
                    return [opcoes[int(escolha) - 1]]
                else:
                    input("Opção inválida. Pressione ENTER para tentar novamente.")
                    self.clear_console()
                    self.display_menu(
                        opcoes,
                        selecionar_todos=selecionar_todos,
                        permitir_voltar=permitir_voltar,
                    )
        else:
            while True:
                escolha_bruta = (
                    input("Digite os números das opções separados: ")
                    .strip()
                    .upper()
                    .replace("  ", " ")
                    .replace("  ", " ")
                )

                if escolha_bruta == "X":
                    sys.exit()
                elif permitir_voltar and escolha_bruta == "V":
                    return None
                elif selecionar_todos and escolha_bruta == "0":
                    return opcoes

                # Divide a string em uma lista de strings
                escolhas_separadas = [e.strip() for e in escolha_bruta.split(" ")]

                opcoes_validas: list[str] = []
                input_invalido = False

                # Valida cada escolha individualmente
                for escolha in escolhas_separadas:
                    if not escolha.isdigit():
                        input_invalido = True
                        break

                    num_escolhido = int(escolha)

                    if num_escolhido in range(1, len(opcoes) + 1):
                        opcoes_validas.append(opcoes[num_escolhido - 1])
                    else:
                        input_invalido = True
                        break

                if not input_invalido and opcoes_validas:
                    # Retorna uma lista de strings (os itens da lista de opções)
                    return opcoes_validas
                else:
                    input("Opção inválida. Pressione ENTER para tentar novamente.")
                    self.clear_console()
                    self.display_menu(
                        opcoes,
                        selecionar_todos=selecionar_todos,
                        permitir_voltar=permitir_voltar,
                    )

    def show_processing_message(self, message: str):
        """Exibe uma mensagem de processamento com uma animação de pontinhos."""
        print(f"\n{message}", end="", flush=True)
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.5)
        print()

    def clear_console(self):
        """Limpa a tela do console."""
        if os.name == "nt":
            _ = os.system("cls")
        else:
            _ = os.system("clear")

    def show_message(self, message: str):
        """Exibe uma mensagem e espera que o usuário pressione ENTER."""
        input(f"\n{message}\nPressione ENTER para sair.")

    def show_error(self, msg):
        self.color_print(f"\n{msg}\n", color="red", style="bold")
        input(f"\nPressione ENTER para sair.")

    def show_success(self, msg):
        self.color_print(f"\n{msg}\n", color="green", style="bold")
        input(f"\nPressione ENTER para sair.")

    @staticmethod
    def color_text(text, color=None, style=None, background=None):
        # ANSI color codes
        colors = {
            "black": 30,
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "magenta": 35,
            "cyan": 36,
            "white": 37,
        }
        styles = {"normal": 0, "bold": 1, "underline": 4}
        backgrounds = {
            "black": 40,
            "red": 41,
            "green": 42,
            "yellow": 43,
            "blue": 44,
            "magenta": 45,
            "cyan": 46,
            "white": 47,
        }

        codes = []

        if style in styles:
            codes.append(str(styles[style]))
        if color in colors:
            codes.append(str(colors[color]))
        if background in backgrounds:
            codes.append(str(backgrounds[background]))

        prefix = f"\033[{';'.join(codes)}m" if codes else ""
        suffix = "\033[0m" if codes else ""

        return f"{prefix}{text}{suffix}"

    @staticmethod
    def color_print(*args, color=None, style=None, background=None, sep=" ", end="\n"):
        colored_args = [
            ConsoleService.color_text(
                str(arg), color=color, style=style, background=background
            )
            for arg in args
        ]
        print(*colored_args, sep=sep, end=end)
