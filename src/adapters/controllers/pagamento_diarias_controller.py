from src.infrastructure.services.console_service import ConsoleService
from src.factories import UseCaseFactory


def PagamentoDiariaController(run=True):
    app_view = ConsoleService()
    app_view.clear_console()

    factory = UseCaseFactory()
    pagamento_diaria_uc = factory.create_pagamento_diaria_uc()
    nomes_planilhas = pagamento_diaria_uc.listar_planilhas()

    while True:
        app_view.display_menu(
            nomes_planilhas,
            "Selecione a planilha:",
            selecionar_todos=True,
            # permitir_voltar=True,
        )
        planilhas_selecionadas = app_view.get_user_input(
            nomes_planilhas,
            selecionar_todos=True,
            permitir_voltar=True,
            multipla_escolha=True,
        )

        if planilhas_selecionadas is None:
            continue

        if run:
            pagamento_diaria_uc.executar(planilhas_selecionadas)

        app_view.show_message("Processamento concluído.")
        break

if __name__ == "__main__":
    try:
        PagamentoDiariaController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
