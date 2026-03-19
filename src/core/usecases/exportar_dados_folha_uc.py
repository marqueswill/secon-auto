from src.core.parsers.nota_lancamento_parser import NotaLancamentoParser
from src.core.interfaces.i_excel_service import IExcelService


class ExportarDadosFolhaUseCase:
    def __init__(self, parser: NotaLancamentoParser, excel_svc: IExcelService):
        self.parser = parser
        self.excel_svc = excel_svc

    # O executar recebe uma lista com as NLs para realizar o parse
    def executar(self, lista_nls: list[str]):
        todos_dados_nl = self.parser.parse(lista_nls)
        # for tabela in todos_dados_nl:
        #     self.excel_svc.export_table(tabela, tabela.nome)

    def get_lista_nls(self) -> list[str]:
        df = self.excel_svc.get_sheet("lista_nls")
        return df["NUM_NL"].astype(str).tolist()

    def listar_planilhas(self) -> list[str]:
        caminho_atual = self.pathing_gw.get_current_file_path()
        arquivos = self.pathing_gw.listar_arquivos(caminho_atual)
        nomes_planilhas = [
            nome
            for nome in arquivos
            if nome.endswith((".xlsx")) and not nome.startswith("~$")
        ]
        return nomes_planilhas
