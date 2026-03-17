from pandas import DataFrame
from src.core.entities.entities import DadosPreenchimento
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_nl_folha_gateway import ITemplateFolhaGateway
from src.core.interfaces.i_preenchimento_gateway import IPreenchimentoGateway


class PreenchimentoNLUseCase:
    def __init__(
        self,
        nl_folha_gw: ITemplateFolhaGateway,
        preenchedor_gw: IPreenchimentoGateway,
        pathing_gw: IPathingGateway,
    ):
        self.nl_folha_gw = nl_folha_gw
        self.preenchedor_gw = preenchedor_gw
        self.pathing_gw = pathing_gw

    def executar(self, nls_selecionadas: dict[str, list[str]]):
        nls_carregadas: list[DadosPreenchimento] = []
        for planilha, abas in nls_selecionadas.items():
            caminho_planilha = self.pathing_gw.get_current_file_path() + "\\" + planilha
            nls: list[DadosPreenchimento] = []
            for aba in abas:
                lancamento = self.nl_folha_gw.carregar_template_nl(
                    caminho_planilha, template=aba, incluir_calculos=False
                )
                cabecalho = self.nl_folha_gw.carregar_cabecalho(
                    caminho_planilha, template=aba
                )

                dado = DadosPreenchimento(lancamento, cabecalho)
                nls.append(dado)

            nls_carregadas.extend(nls)

        self.preenchedor_gw.executar(nls_carregadas)

    def listar_planilhas(self) -> list[str]:
        caminho_atual = self.pathing_gw.get_current_file_path()
        arquivos = self.pathing_gw.listar_arquivos(caminho_atual)
        nomes_planilhas = [
            nome
            for nome in arquivos
            if nome.endswith((".xlsx", ".xls")) and not nome.startswith("~$")
        ]
        return nomes_planilhas

    def listar_templates(self, nome_planilha: str) -> list[str]:
        caminho_atual = self.pathing_gw.get_current_file_path()
        caminho_arquivo = caminho_atual + "\\" + nome_planilha
        nomes_templates = self.nl_folha_gw.listar_abas(caminho_arquivo)
        return nomes_templates
