from abc import ABC, abstractmethod
from pypdf import PageObject
from pandas import DataFrame

class IPdfService(ABC):

    @abstractmethod
    def parse_dados_diaria(self, caminho_pdf: str) -> dict: ...

    @abstractmethod
    def parse_relatorio_folha(self, fundo_escolhido: str)->dict[str, DataFrame]: ...

    @abstractmethod
    def parse_dados_inss(self): ...

    @abstractmethod
    def parse_pdf_driss(self, file) -> dict[str, list[PageObject]]: ...

    @abstractmethod
    def parse_dados_provisoes(self, fundo:str) -> dict: ...
    
    @abstractmethod
    def export_pages(self, pages: list[PageObject], path: str): ...
