import pandas as pd

from pandas import DataFrame

from src.core.entities.entities import NotaLancamento
from src.config import *

from src.core.interfaces.i_conferencia_gateway import IConferenciaGateway
from src.core.interfaces.i_excel_service import IExcelService
from src.core.interfaces.i_pathing_gateway import IPathingGateway


class ConferenciaGateway(IConferenciaGateway):
    """_summary_ Atua como uma ponte para consolidar os dados da conferência financeira. Ele lê a tabela "Demofin", e utiliza o ExcelService para exportar os resultados processados (proventos, descontos, totais e relatórios) para as planilhas de conferência finais.

    Args:
        IConferenciaGateway (_type_): _description_
    """

    def __init__(
        self,
        pathing_gw: IPathingGateway,  # Configuração do pathing
        excel_svc: IExcelService,  # Exportação e importação
    ):
        self.pathing_gw = pathing_gw
        self.excel_svc = excel_svc
        super().__init__()

    def get_tabela_demofin(self):
        caminho_completo = self.pathing_gw.get_caminho_tabela_demofin()
        tabela_demofin = pd.read_excel(
            caminho_completo, sheet_name="DEMOFIN - T", header=1
        )
        return tabela_demofin

    def salvar_nls_conferencia(self, nls: list[NotaLancamento], fundo: str):
        for nl in nls:
            if nl.esta_vazia():
                print(f"A NL {nl.nome} não tem valor para liquidação.")
                continue

            
            self.excel_svc.exportar_para_planilha(
                table=nl.dados,
                sheet_name=nl.nome,
                # start_line=str(linha_atual),
                # title=titulo,
            )


    def salvar_dados_conferencia(
        self, proventos_folha: DataFrame, descontos_folha: DataFrame, totais: DataFrame
    ):
        # Exporta proventos na coluna A
        self.excel_svc.exportar_para_planilha(
            table=proventos_folha,
            sheet_name="CONFERÊNCIA",
            start_column="A",
            clear=True,
        )

        # Exporta descontos na coluna H
        self.excel_svc.exportar_para_planilha(
            table=descontos_folha,
            sheet_name="CONFERÊNCIA",
            start_column="H",
            clear=False,
        )

        self.excel_svc.apply_conditional_formatting(
            formula="=AND($A1<>" ";IFERROR($F1<0;FALSE))",
            target_range="=$A:$F",
            filling="#FFD966",
            sheet_name="CONFERÊNCIA",
        )
        self.excel_svc.apply_conditional_formatting(
            formula="=AND($H1<>" ";IFERROR($M1<0;FALSE))",
            target_range="=$H:$M",
            filling="#FFD966",
            sheet_name="CONFERÊNCIA",
        )

        # self.excel_svc.apply_conditional_formatting(
        #     formula="=AND($A1<>"";IFERROR($F1<0;FALSE))",
        #     target_range="=$F:$F",
        #     filling="#FF7979",
        #     sheet_name="CONFERÊNCIA",
        # )
        # self.excel_svc.apply_conditional_formatting(
        #     formula="=AND($H1<>"";IFERROR($M1<0;FALSE))",
        #     target_range="=$M:$M",
        #     filling="#FF7979",
        #     sheet_name="CONFERÊNCIA",
        # )

        # Exporta os totais para coluna H, abaixo dos descontos
        ultima_linha = str(len(descontos_folha) + 3)
        self.excel_svc.exportar_para_planilha(
            table=totais,
            sheet_name="CONFERÊNCIA",
            start_column="H",
            start_line=ultima_linha,
            clear=False,
        )

        self.excel_svc.delete_sheet("Sheet")
        self.excel_svc.move_to_first("CONFERÊNCIA")

    def salvar_dados_relatorio(self, dados_relatorio: dict[str, DataFrame]):
        self.excel_svc.exportar_para_planilha(
            dados_relatorio["PROVENTOS"],
            sheet_name="RELATÓRIO",
            start_column="A",
            clear=True,
        )

        self.excel_svc.exportar_para_planilha(
            dados_relatorio["DESCONTOS"],
            sheet_name="RELATÓRIO",
            start_column="E",
            clear=False,
        )

        self.excel_svc.move_to_first("RELATÓRIO")

    def salvar_dados_510(self, dados_510: DataFrame):
        self.excel_svc.exportar_para_planilha(
            dados_510,
            sheet_name="DADOS_510",
            start_column="A",
            clear=True,
        )
        self.excel_svc.move_to_first("DADOS_510")
