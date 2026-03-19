from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService
from src.config import *


def NLAutomaticaController(run=True):
    app_view = ConsoleService()
    app_view.clear_console()

    factory = UseCaseFactory()
    preenchimento_uc = factory.create_preenchimento_nl_use_case()

    nomes_planilhas = preenchimento_uc.listar_planilhas()

    while True:
        app_view.display_menu(
            nomes_planilhas,
            "Selecione a planilha:",
            selecionar_todos=True,
            permitir_voltar=True,
        )
        planilhas_selecionadas = app_view.get_user_input(
            nomes_planilhas,
            selecionar_todos=True,
            permitir_voltar=True,
            multipla_escolha=True,
        )

        if planilhas_selecionadas is None:
            continue

        # nls_carregadas = []
        templates_selecionados = {}
        for planilha in planilhas_selecionadas:
            while True:
                try:

                    nomes_templates = preenchimento_uc.listar_templates(planilha)

                    app_view.display_menu(
                        nomes_templates,
                        f"Selecione as NLs da planilha {planilha.split(".")[0]} para serem preenchidas:",
                        selecionar_todos=True,
                        # permitir_voltar=True,
                    )
                    escolhas_planilha = app_view.get_user_input(
                        nomes_templates,
                        selecionar_todos=True,
                        # permitir_voltar=True,
                        multipla_escolha=True,
                    )

                    if escolhas_planilha is not None:
                        templates_selecionados[planilha] = escolhas_planilha
                        break

                except Exception as e:
                    print(f"Erro ao processar {planilha}: {e}")

        break

    if run:
        preenchimento_uc.executar(templates_selecionados)


if __name__ == "__main__":
    try:
        NLAutomaticaController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
