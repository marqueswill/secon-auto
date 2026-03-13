from src.factories import UseCaseFactory
from src.infrastructure.cli.console_service import ConsoleService

def DownloadNlsController(run=True, test=False):
    app_view = ConsoleService()
    factory = UseCaseFactory()
    use_case = factory.create_download_nls_usecase()
    lista_nls = ["2026NL00341", "2026NL00100","2026NL00251"]
    use_case.executar(lista_nls)
    app_view.show_message("Processamento concluído.")

if __name__ == "__main__":
    try:
        DownloadNlsController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
