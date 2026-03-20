import os
from pandas import DataFrame, Index
import pandas as pd

from src.core.parsers.nota_empenho_parser import NotaEmpenhoParser
from src.core.entities.entities import CabecalhoNL, DadosPreenchimento, NotaLancamento
from src.core.interfaces.i_pdf_service import IPdfService
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_preenchimento_gateway import IPreenchimentoGateway


class PagamentoDiariaUseCase:
    def __init__(
        self,
        preenchimento_gw: IPreenchimentoGateway,
        pathing_gw: IPathingGateway,
        parser_ne: NotaEmpenhoParser,
    ):
        self.preenchimento_gw = preenchimento_gw
        self.pathing_gw = pathing_gw
        self.parser_ne = parser_ne

    def executar(self, arquivos_selecionados: list[str]):
        dados_preenchimento = self.gerar_nl_diarias(arquivos_selecionados)
        self.preenchimento_gw.executar(dados_preenchimento)

    def listar_planilhas(self) -> list[str]:
        dir_path = os.path.join(
            self.pathing_gw.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            "NL_AUTOMATICA",
            "NE_DIÁRIAS",
        )
        return self.pathing_gw.listar_arquivos(dir_path)

    def gerar_nl_diarias(
        self, arquivos_selecionados: list[str]
    ) -> list[DadosPreenchimento]:
        dados_preenchimento: list[DadosPreenchimento] = []
        caminhos_pdf = self.pathing_gw.get_caminhos_nes_diaria(arquivos_selecionados)
        for i, caminho_pdf in enumerate(caminhos_pdf):
            nl = DataFrame(
                columns=pd.Index(
                    [
                        "EVENTO",
                        "INSCRIÇÃO",
                        "CLASS. CONT",
                        "CLASS. ORC",
                        "FONTE",
                        "VALOR",
                    ]
                )
            )

            dados_extraidos = self.parser_ne.parse_pdf(caminho_pdf)
            #TODO: passar lógica de dict para lógica da entidade NotaEmpenho
            processo = dados_extraidos.processo
            observacao = dados_extraidos.observacao

            cabecalho = CabecalhoNL(
                prioridade="F0",
                credor="4 - UG/Gestão",
                gestao="020101-00001",
                processo=processo,
                observacao=observacao,
            )

            for dados in dados_extraidos.dados:
                evento1 = "510379"
                evento2 = "520379"
                inscricao = dados.nune
                classcont1 = "113110105"
                classcont2 = "218910200"
                classorc = str(dados.natureza) + str(dados.subitem)
                fonte = dados.fonte
                valor = dados.valor

                linha1 = [evento1, inscricao, classcont1, classorc, fonte, valor]
                linha2 = [evento2, inscricao, classcont2, classorc, fonte, valor]

                nl.loc[len(nl)] = linha1
                nl.loc[len(nl)] = linha2

            nl = nl.sort_values(by=["INSCRIÇÃO", "EVENTO"]).reset_index(drop=True)

            lancamento = NotaLancamento(nl)
            dados = DadosPreenchimento(lancamento, cabecalho)
            dados_preenchimento.append(dados)

        return dados_preenchimento
