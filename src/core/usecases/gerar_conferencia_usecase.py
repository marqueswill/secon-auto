import pandas as pd
from pandas import DataFrame
from typing import cast
from src.core.entities.entities import NotaLancamento
from src.core.gateways.i_pathing_gateway import IPathingGateway
from src.core.gateways.i_conferencia_gateway import IConferenciaGateway
from src.core.usecases.pagamento_usecase import PagamentoUseCase
from src.core.gateways.i_nl_folha_gateway import INLFolhaGateway


class GerarConferenciaUseCase:

    def __init__(self, pagamento_uc: PagamentoUseCase, pathing_gw: IPathingGateway):
        self.pagamento_uc = pagamento_uc
        self.pathing_gw = pathing_gw

    def executar(self, fundo):
        conferencia_completa = self.pagamento_uc.get_dados_conferencia(fundo)
        conferencia_ferias = self.pagamento_uc.get_dados_conferencia(
            fundo, adiantamento_ferias=True
        )

        proventos = self.pagamento_uc.separar_proventos(conferencia_completa)
        descontos = self.pagamento_uc.separar_descontos(conferencia_completa)
        # dados_relatorio = self.pagamento_uc.extrair_dados_relatorio(fundo)

        saldos = self.pagamento_uc.gerar_saldos(
            conferencia_ferias, proventos, descontos
        )
        provisoes = self.pagamento_uc.get_provisoes(fundo)
        nls_fundo = self._gerar_nls_folha(fundo, saldos, provisoes)
        totais = self._calcular_totais(nls_fundo, proventos, descontos)

        # dados_510 = self._obter_valores_510(nls_fundo)
        # self.pagamento_uc.conferencia_gw.salvar_dados_510(dados_510)

        self.pagamento_uc.conferencia_gw.salvar_dados_conferencia(
            proventos, descontos, totais
        )

        # self.pagamento_uc.conferencia_gw.salvar_dados_relatorio(dados_relatorio)
        self.pagamento_uc.conferencia_gw.salvar_nls_conferencia(nls_fundo, fundo)

    def _calcular_totais(
        self,
        nls: list[NotaLancamento],
        proventos_folha: DataFrame,
        descontos_folha: DataFrame,
    ) -> DataFrame:

        total_liquidado = 0
        for dados_nl in [nl.dados for nl in nls if nl.nome != "ADIANTAMENTO_FERIAS"]:
            total_liquidado += dados_nl.loc[
                dados_nl["EVENTO"].astype(str).str.startswith("510", na=False), "VALOR"
            ].sum()

        total_proventos = (
            proventos_folha["PROVENTO"].sum() + descontos_folha["PROVENTO"].sum()
        )
        total_descontos = (
            proventos_folha["DESCONTO"].sum() + descontos_folha["DESCONTO"].sum()
        )
        total_liquido = total_proventos - total_descontos
        total_saldo = proventos_folha["SALDO"].sum()

        totais = DataFrame(
            {
                "TOTAIS": [
                    "PROVENTOS",
                    "DESCONTOS",
                    "LÍQUIDO FINANCEIRO",
                    "",
                    "TOTAL DE SALDO",
                    "TOTAL LIQUIDADO",
                ],
                "VALOR": [
                    total_proventos,
                    total_descontos,
                    total_liquido,
                    None,  # TODO: tirar essa gambiarra aqui
                    total_saldo,
                    total_liquidado,
                ],
            }
        )

        return totais

    def _gerar_nls_folha(
        self, fundo: str, saldos: dict, provisoes: dict
    ) -> list[NotaLancamento]:
        nomes_nls = self.pagamento_uc.nl_folha_gw.get_nomes_templates(fundo)
        caminho_planilha_templates = self.pathing_gw.get_caminho_template(fundo)
        nls: list[NotaLancamento] = []
        for nome_nl in nomes_nls:
            nl_gerada = self.pagamento_uc.gerar_nl_folha(
                caminho_planilha_templates, nome_nl, saldos, provisoes
            )
            nl_gerada.nome = nome_nl
            nls.append(nl_gerada)

        # nl_provisoes = self.pagamento_uc.gerar_nl_provisoes(fundo, saldos)
        # nls.append(nl_provisoes)
        return nls

    def _obter_valores_510(self, nls_fundo: list[NotaLancamento]) -> DataFrame:
        dfs_filtrados = [
            nl.dados for nl in nls_fundo if nl.nome != "ADIANTAMENTO_FERIAS"
        ]

        if not dfs_filtrados:
            return DataFrame()

        df_concat = pd.concat(dfs_filtrados, ignore_index=True)

        resultado = df_concat[df_concat["EVENTO"].astype(str).str.startswith("510")]

        return cast(DataFrame, resultado)
