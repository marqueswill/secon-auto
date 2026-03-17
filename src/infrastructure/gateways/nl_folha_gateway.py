from typing import List
from pandas import DataFrame  # type: ignore
import pandas as pd

from src.config import *
from src.core.interfaces.i_nl_folha_gateway import INLFolhaGateway
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.entities.entities import CabecalhoNL, NotaLancamento, TemplateNL


class NLFolhaGateway(INLFolhaGateway):
    """_summary_ Responsável por interagir com os arquivos de Templates das Notas de Lançamento (NL). Ele lista as abas disponíveis (templates), carrega os dados do cabeçalho da NL e os dados das linhas de lançamento para serem usados no preenchimento.

    Args:
        INLFolhaGateway (_type_): _description_
    """

    def __init__(self, pathing_gw: IPathingGateway):
        self.pathing_gw = pathing_gw
        super().__init__()

    def get_nomes_templates(self, fundo: str) -> List[str]:
        caminho_template = self.pathing_gw.get_caminho_template(fundo)
        template_excel = pd.ExcelFile(caminho_template)
        nomes_nls = template_excel.sheet_names

        return nomes_nls

    # TODO: verificação formato template
    def carregar_template_nl(
        self, caminho_completo: str, template: str, incluir_calculos=True
    ) -> TemplateNL | NotaLancamento | None:
        try:

            df = pd.read_excel(
                caminho_completo,
                header=6,
                sheet_name=template,
                usecols="A:I" if incluir_calculos else "A:F",
                dtype=str,
            ).astype(str)

            df.replace(["nan", "", "-"], ".", inplace=True)

            if "CLASS. ORC" in df.columns:
                df["CLASS. ORC"] = (
                    df["CLASS. ORC"]
                    .apply(lambda x: str(x)[1:] if len(str(x)) == 9 else str(x))
                    .astype(str)
                )

            if incluir_calculos:
                return TemplateNL(df, template)
            else:
                return NotaLancamento(df, template)
        except PermissionError as e:
            print("Feche todas planilhas de template e tente novamente.", e)
        except Exception as e:
            raise Exception(e)

    # TODO: verificação formato cabeçalho
    def carregar_cabecalho(self, caminho_completo: str, template: str) -> CabecalhoNL:
        cabecalho_dict = {}

        try:
            df = pd.read_excel(
                caminho_completo, sheet_name=template, header=None, dtype=str
            )

            for index, row in df.iterrows():
                chave = str(row[0]).strip()
                if chave == "EVENTO":
                    break

                if chave and chave.lower() != "nan":
                    chave_limpa = chave.replace(":", "").strip().lower()
                    valor = str(row[1]).strip() if bool(pd.notna(row[1])) else ""
                    cabecalho_dict[chave_limpa] = valor

            cabecalho = CabecalhoNL(
                prioridade=cabecalho_dict.get("prioridade de pagamento", ""),
                credor=cabecalho_dict.get("credor", ""),
                gestao=cabecalho_dict.get("ug/gestão", ""),
                processo=cabecalho_dict.get("processo", ""),
                observacao=cabecalho_dict.get("observação", ""),
                contrato=cabecalho_dict.get("contrato", ""),
            )

            return cabecalho

        except Exception as e:
            print(f"Erro ao processar o cabeçalho da planilha '{template}': {e}")
            return CabecalhoNL()

    def listar_abas(self, caminho_arquivo: str) -> List[str]:
        xls = pd.ExcelFile(caminho_arquivo)
        return xls.sheet_names
