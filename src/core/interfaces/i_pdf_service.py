from abc import ABC, abstractmethod
from pypdf import PageObject
from pandas import DataFrame


class IPdfService(ABC):

    @abstractmethod
    def get_raw_text(self, caminho_pdf: str) -> str: ...

    @abstractmethod
    def export_pages(self, pages: list[PageObject], path: str): ...

    @abstractmethod
    def get_pdfs_driss(self, caminho_pdf: str) -> list[PageObject]: ...

    @abstractmethod
    def get_nls_baixadas(self, lista_nls: list[str]) -> list[str]: ...

    # @abstractmethod
    # def parse_dados_diaria(self, caminho_pdf: str) -> dict: ...

    # @abstractmethod
    # def parse_relatorio_folha(self, fundo_escolhido: str)->dict[str, DataFrame]: ...

    # @abstractmethod
    # def parse_dados_inss(self): ...

    # @abstractmethod
    # def parse_dados_provisoes(self, fundo:str) -> dict: ...
