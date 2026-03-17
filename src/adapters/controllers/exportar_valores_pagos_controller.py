from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService
from src.config import *


def ExportarValoresPagosController():
    app_view = ConsoleService()
    factory = UseCaseFactory()
    use_case = factory.create_exportar_valores_pagos_uc()

    # selecão mês de interesse
    while True:
        app_view.display_menu(
            NOMES_MESES,
            "Selecione o mês:",
            selecionar_todos=False,
        )

        mes_escolhido = app_view.get_user_input(
            PASTAS_MESES,
            multipla_escolha=True,
        )

        if mes_escolhido:
            use_case.exportar_valores_pagos(mes_escolhido)
            app_view.show_success("Valores pagos exportados com sucesso!")
            break


if __name__ == "__main__":
    try:
        ExportarValoresPagosController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
