from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService


def BaixaDiariasController(run=True, test=False):
    app_view = ConsoleService()
    factory = UseCaseFactory()
    use_case = factory.create_baixa_diarias_uc()

    nomes_planilhas = use_case.listar_planilhas()

    while True:
        app_view.display_menu(
            nomes_planilhas,
            "Selecione o mês:",
            selecionar_todos=True,
        )

        arquivos_escolhidos = app_view.get_user_input(
            nomes_planilhas, multipla_escolha=True, selecionar_todos=True
        )

        if not arquivos_escolhidos:
            continue

        use_case.executar(arquivos_escolhidos)
        app_view.show_message("Processamento concluído.")
        break


if __name__ == "__main__":
    try:
        BaixaDiariasController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
