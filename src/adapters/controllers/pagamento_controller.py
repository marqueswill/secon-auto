import sys


from src.factories import UseCaseFactory
from src.infrastructure.services.console_service import ConsoleService
from src.config import *


def FolhaPagamentoController(test=False, run=True):
    """Função principal que atua como o Controller da aplicação."""
    app_view = ConsoleService()
    app_view.clear_console()

    while True:
        try:
            factory = UseCaseFactory()
            fundos = {
                1: "RGPS",
                2: "FINANCEIRO",
                3: "CAPITALIZADO",
            }

            app_view.display_menu(
                ["PREENCHER FOLHA", "GERAR CONFERÊNCIAS"], "Selecione uma opção:"
            )
            opcao = app_view.get_user_input(["PREENCHER FOLHA", "GERAR CONFERÊNCIAS"])

            if opcao is None:
                continue

            usecase_escolhido = opcao[0]
            if usecase_escolhido == "PREENCHER FOLHA":
                app_view.display_menu(
                    list(fundos.values()),
                    "Selecione o template:",
                    permitir_voltar=True,
                )
                tipo_folha_selecionado = app_view.get_user_input(
                    list(fundos.values()),
                    permitir_voltar=True,
                )
                if tipo_folha_selecionado is None:
                    continue

                folha = tipo_folha_selecionado[0]
                use_case = factory.create_preenchimento_folha_use_case(folha)
                nomes_templates = use_case.get_nomes_templates(folha)
                

                app_view.display_menu(
                    nomes_templates,
                    "Selecione o template:",
                    selecionar_todos=True,
                    permitir_voltar=True,
                )
                templates_selecionados = app_view.get_user_input(
                    nomes_templates,
                    selecionar_todos=True,
                    permitir_voltar=True,
                    multipla_escolha=True,
                )

                if templates_selecionados is None:
                    continue

                app_view.show_processing_message("Iniciando o processamento")
                use_case.executar(folha, templates_selecionados)
                app_view.show_message("Processamento concluído.")
                continue

            elif usecase_escolhido == "GERAR CONFERÊNCIAS":
                app_view.display_menu(
                    list(fundos.values()),
                    "Selecione o fundo para gerar a sua conferência:",
                    selecionar_todos=True,
                    permitir_voltar=True,
                )

                fundos_para_conferencia = app_view.get_user_input(
                    list(fundos.values()),
                    selecionar_todos=True,
                    permitir_voltar=True,
                )
                if fundos_para_conferencia is None:
                    continue

                for fundo_para_conferencia in fundos_para_conferencia:
                    use_case = factory.create_gerar_conferencia_use_case(
                        fundo_para_conferencia
                    )
                    use_case.executar(fundo_para_conferencia)
                app_view.show_success("Conferência gerada com sucesso.")
                continue

        except Exception as e:
            # Em caso de erro, exibe a mensagem de erro e sai
            app_view.show_message(f"Ocorreu um erro: {e}")
            continue


if __name__ == "__main__":
    try:
        FolhaPagamentoController()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
