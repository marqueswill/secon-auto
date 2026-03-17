from abc import ABC, abstractmethod
from typing import List
from pandas import DataFrame

from src.core.entities.entities import CabecalhoNL, TemplateNL, NotaLancamento


class INLFolhaGateway(ABC):
    """_summary_ Gera uma NL para folha de pagamento a partir de um fundo e um template fornecido.
    Também interage com as planilhas de template das NLs de folha de pagamento.
    """

    # TODO: renomear pra um nome menos confuso
    @abstractmethod
    def carregar_template_nl(
        self, caminho_completo: str, template: str, incluir_calculos=True
    ) -> TemplateNL | NotaLancamento | None: ...

    @abstractmethod
    def carregar_cabecalho(
        self, caminho_completo: str, template: str
    ) -> CabecalhoNL: ...

    @abstractmethod
    def get_nomes_templates(self, fundo: str) -> List[str]: ...

    @abstractmethod
    def listar_abas(self, caminho_arquivo: str) -> List[str]: ...
