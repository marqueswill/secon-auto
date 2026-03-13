from abc import ABC, abstractmethod


class IPathingGateway(ABC):
    """_summary_ Gateway usado para unificar a personalização de caminhos"""

    @abstractmethod
    def get_current_file_path(self) -> str: ...

    @abstractmethod
    def get_caminho_raiz_secon(self) -> str: ...

    @abstractmethod
    def get_caminho_template(self, tipo_folha: str) -> str: ...

    @abstractmethod
    def get_caminho_conferencia(self, fundo: str) -> str: ...

    @abstractmethod
    def get_caminho_tabela_demofin(self) -> str: ...

    @abstractmethod
    def get_caminho_pdf_relatorio(self) -> str | None: ...

    @abstractmethod
    def listar_arquivos(self, caminho: str) -> list[str]: ...

    @abstractmethod
    def get_caminhos_nes_diaria(
        self, arquivos_selecionados: list[str]
    ) -> list[str]: ...

    @abstractmethod
    def get_caminhos_demonstrativos(self, pasta_mes: str) -> list[str]: ...

    @abstractmethod
    def get_caminho_reinf(self, pasta_mes: str | None) -> str: ...

    @abstractmethod
    def get_caminho_pdf_driss(self) -> str: ...

    @abstractmethod
    def get_caminhos_pdfs_envio_driss(self) -> list[str]: ...

    @abstractmethod
    def get_caminho_download_nl(self)->str: ...