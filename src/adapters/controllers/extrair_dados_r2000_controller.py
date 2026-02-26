from src.factories import UseCaseFactory
from src.infrastructure.cli.console_service import ConsoleService
from src.config import *


def ExtrairDadosR2000Controller():
    app_view = ConsoleService()
    factory = UseCaseFactory()

    while True:
        app_view.display_menu(
            NOMES_MESES,
            "Selecione o mês:",
            selecionar_todos=False,
        )

        mes_escolhido = app_view.get_user_input(
            PASTAS_MESES,
            multipla_escolha=False,
        )

        if mes_escolhido:
            use_case = factory.create_extrair_dados_r2000_usecase(mes_escolhido[0])
            use_case.executar(mes_escolhido)
            break


if __name__ == "__main__":
    try:
        ExtrairDadosR2000Controller()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
