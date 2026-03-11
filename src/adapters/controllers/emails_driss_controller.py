from src.infrastructure.cli.console_service import ConsoleService
from src.factories import UseCaseFactory


def EmailsDrissController(run=True, test=False):
    app_view = ConsoleService()

    factory = UseCaseFactory()
    use_case = factory.create_emails_driss_usecase()
    use_case.executar()

    app_view.show_message("Processamento concluído.")


if __name__ == "__main__":
    try:
        EmailsDrissController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
