from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService

def CancelamentoRPController(run=True, test=False):
    app_view = ConsoleService()
    factory = UseCaseFactory()
    use_case = factory.create_cancelamento_rp_uc()
    use_case.executar()
    app_view.show_message("Processamento concluído.")

if __name__ == "__main__":
    try:
        CancelamentoRPController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
