from pandas import DataFrame
import pandas as pd

from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_excel_service import IExcelService
from src.core.interfaces.i_pdf_service import IPdfService
from src.config import *


class ExtrairDadosR2000UseCase:

    def __init__(
        self,
        excel_svc: IExcelService,
        pdf_svc: IPdfService,
        pathing_gw: IPathingGateway,
    ):
        self.pathing_gw = pathing_gw
        self.excel_svc = excel_svc
        self.pdf_svc = pdf_svc

    def executar(self, meses_escolhidos: list[str]):
        for pasta_mes in meses_escolhidos:
            try:
                dados_inss = self.extrair_dados_inss(pasta_mes)
                df_r2010_1, df_r2010_2 = self.gerar_dataframes_reinf(dados_inss)
                self.exportar_planilhas_r2000(df_r2010_1, df_r2010_2)
            except Exception as e:
                print(e)
            finally:
                self.excel_svc.__exit__()

    def exportar_valores_pagos(self, meses_escolhidos: list[str]):
        for pasta_mes in meses_escolhidos:
            try:
                dados_inss = self.extrair_dados_inss(pasta_mes)
                valores_pagos = self.gerar_dataframe_valores_pagos(dados_inss)
                nome_mes = pasta_mes.split("-")[1].strip() if not TESTE else "TESTES"
                self.excel_svc.exportar_para_planilha(
                    valores_pagos, sheet_name=nome_mes, clear=True
                )
            except Exception as e:
                print(e)

    def extrair_dados_inss(self, pasta_mes: str):
        caminhos_pdf = self.pathing_gw.get_caminhos_demonstrativos(pasta_mes)
        lista_de_dados_completa = []
        for caminho_pdf in caminhos_pdf:
            dados_extraidos = self.pdf_svc.parse_dados_inss(caminho_pdf)

            if dados_extraidos is not None:
                lista_de_dados_completa.append(dados_extraidos)

        if lista_de_dados_completa:
            df = DataFrame(lista_de_dados_completa)
            df = df.sort_values(by=["CNPJ", "NUM_NF"]).reset_index(drop=True)

        df = df.sort_values(by=["CNPJ", "NUM_NF"])

        return df

    def gerar_dataframe_valores_pagos(self, df_principal):

        df_valores_pagos = DataFrame(
            columns=[
                "CHAVE",
                "PROCESSO",
                "CNPJ",
                "NUM NF",
                "VALOR BRUTO",
            ]
        )

        # Acumula as linhas em listas
        linhas_df = []

        for _, dados in df_principal.iterrows():
            # Preenche a linha para df_r2010_1
            nova_linha = {
                "CHAVE": dados["CHAVE"],
                "PROCESSO": dados["PROCESSO"],
                "CNPJ": dados["CNPJ"],
                "NUM NF": dados["NUM_NF"],
                "VALOR BRUTO": dados["VALOR_NF"],
            }
            linhas_df.append(nova_linha)

        df_valores_pagos = DataFrame(
            linhas_df,
            columns=[
                "CHAVE",
                "PROCESSO",
                "CNPJ",
                "NUM NF",
                "VALOR BRUTO",
            ],
        )
        return df_valores_pagos

    def gerar_dataframes_reinf(
        self, dados_inss: DataFrame
    ) -> tuple[DataFrame, DataFrame]:

        if dados_inss.empty:
            print("O DataFrame principal está vazio, não há dados para preencher.")
            return None, None

        dados_inss_retencao = dados_inss[
            dados_inss["VALOR_INSS_RETIDO"] > 0
        ].reset_index(drop=True)

        cnpj_tomador = "00534560000126"

        linhas_r2010_1 = []
        linhas_r2010_2 = []
        for i, dados in dados_inss_retencao.iterrows():
            nova_linha_r2010_1 = {
                "LINHA": i + 1,
                "REGISTRO": "R-2010-1",
                "NRINSCESTABTOM": cnpj_tomador,
                "CNPJPRESTADOR": dados["CNPJ"],
                "INDOBRA": 0,
                "INDCPRB": dados["CPRB"],
                "NUMDOCTO": dados["NUM_NF"],
                "SERIE": dados["SERIE"],
                "DTEMISSAONF": (
                    dados["DATA_EMISSAO"].strftime("%Y-%m-%d")
                    if pd.notnull(dados["DATA_EMISSAO"])
                    else None
                ),
                "VLRBRUTO": dados["VALOR_NF"],
                "OBS": dados["PROCESSO"],
                "MÊS": (
                    int(dados["DATA_EMISSAO"].month)
                    if pd.notnull(dados["DATA_EMISSAO"])
                    else None
                ),
            }
            linhas_r2010_1.append(nova_linha_r2010_1)

            nova_linha_r2010_2 = {
                "LINHA": i + 1,
                "REGISTRO": "R-2010-2",
                "TPSERVICO": dados["TIPO_INSS"],
                "VLRBASERET": dados["BASE_CALCULO_INSS"],
                "VLRRETENCAO": dados["VALOR_INSS_RETIDO"],
                "VLRRETSUB": 0,
                "VLRNRETPRINC": 0,
                "VLRSERVICOS15": 0,
                "VLRSERVICOS20": 0,
                "VLRSERVICOS25": 0,
                "VLRADICIONAL": 0,
                "VLRNRETADIC": 0,
            }
            linhas_r2010_2.append(nova_linha_r2010_2)

        df_r2010_1 = DataFrame(
            linhas_r2010_1,
            columns=[
                "LINHA",
                "REGISTRO",
                "NRINSCESTABTOM",
                "CNPJPRESTADOR",
                "INDOBRA",
                "INDCPRB",
                "NUMDOCTO",
                "SERIE",
                "DTEMISSAONF",
                "VLRBRUTO",
                "OBS",
                "MÊS",
            ],
        )
        df_r2010_2 = DataFrame(
            linhas_r2010_2,
            columns=[
                "LINHA",
                "REGISTRO",
                "TPSERVICO",
                "VLRBASERET",
                "VLRRETENCAO",
                "VLRRETSUB",
                "VLRNRETPRINC",
                "VLRSERVICOS15",
                "VLRSERVICOS20",
                "VLRSERVICOS25",
                "VLRADICIONAL",
                "VLRNRETADIC",
            ],
        )

        planilha_validacao = (
            self.excel_svc.get_sheet("VALIDAÇÃO_BD", as_dataframe=True)
            .iloc[:, :6]
            .dropna(subset=["CNPJ/CPF"])
        )

        planilha_validacao["CHAVE_BUSCA"] = (
            planilha_validacao["CNPJ/CPF"].astype(str)
            + "."
            + planilha_validacao["NUMERO DA NF"].astype(str)
        )

        df_r2010_1["IDENTIFICADOR CNPJ-NF"] = (
            df_r2010_1["CNPJPRESTADOR"].astype(str)
            + "."
            + df_r2010_1["NUMDOCTO"].astype(str)
        )

        return df_r2010_1, df_r2010_2

    def exportar_planilhas_r2000(self, df_r2010_1: DataFrame, df_r2010_2: DataFrame):
        #TODO: reset das formatações condicionais
        
        self.excel_svc.delete_rows("R-2010-1", 4, 100)
        self.excel_svc.exportar_para_planilha(
            df_r2010_1,
            sheet_name="R-2010-1",
            write_headers=False,
            start_line=4,
            fit_columns=False,
        )

        self.excel_svc.delete_rows("R-2010-2", 4, 100)
        self.excel_svc.exportar_para_planilha(
            df_r2010_2,
            sheet_name="R-2010-2",
            write_headers=False,
            start_line=4,
            fit_columns=False,
        )


