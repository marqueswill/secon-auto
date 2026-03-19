from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService


def ExportarDadosFolhaController(run=True, test=False):
    app_view = ConsoleService()
    factory = UseCaseFactory()
    use_case = factory.exportar_dados_folha_uc()
    # nomes_planilhas = use_case.listar_planilhas()

    while True:
        # app_view.display_menu(
        #     NOMES_MESES,
        #     "Selecione o mês:",
        #     selecionar_todos=False,
        # )

        # mes_referencia = app_view.get_user_input(
        #     NOMES_MESES, multipla_escolha=False, selecionar_todos=False
        # )

        # app_view.display_menu(
        #     nomes_planilhas,
        #     "Selecione a planilha:",
        #     selecionar_todos=False,
        #     permitir_voltar=True,
        # )

        # planilhas_selecionadas = app_view.get_user_input(
        #     nomes_planilhas,
        #     selecionar_todos=False,
        #     permitir_voltar=True,
        #     multipla_escolha=False,
        # )

        # if planilhas_selecionadas is None:
        #     continue
        
        nls_folha = ["2026NL00724", "2026NL00730"]
        use_case.executar(nls_folha)
        app_view.show_message("Processamento concluído.")
        break


if __name__ == "__main__":
    try:
        ExportarDadosFolhaController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
