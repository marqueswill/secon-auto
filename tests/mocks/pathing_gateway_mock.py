from src.config import *
from src.core.interfaces.i_pathing_gateway import IPathingGateway


class PathingGatewayMock(IPathingGateway):

    def get_caminho_raiz_secon(self) -> str:
        mocks_file_dir = os.path.dirname(os.path.abspath(__file__))
        tests_root_dir = os.path.abspath(os.path.join(mocks_file_dir, "..", ".."))
        fixtures_path = os.path.join(tests_root_dir, "tests", "fixtures")

        return fixtures_path

    def get_caminho_template(self, fundo: str) -> str:
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "TEMPLATES",
            f"TEMPLATES_NL_{fundo.upper()}.xlsx",
        )

    def get_caminho_conferencia(self, fundo: str):
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "CONFERÊNCIAS",
            f"CONFERÊNCIA_{fundo.upper()}_TEST.xlsx",
        )

    def get_caminho_pasta_folha(self):
        pass

    def get_caminho_tabela_demofin(self):
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "DEMOFIN_TABELA.xlsx",
        )

    def get_caminho_pdf_relatorio(self):
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "RELATÓRIOS - ATIVOS.pdf",
        )

    def get_caminho_conferencia_esperada(self, fundo: str) -> str:
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "expected",
            f"CONFERÊNCIA_{fundo.upper()}.xlsx",
        )

    def get_current_file_path(self) -> str:
        return os.path.join(
            self.get_caminho_raiz_secon(),
            "TEMPLATES",
        )

    def listar_arquivos(self, caminho: str) -> list[str]:
        return os.listdir(caminho)