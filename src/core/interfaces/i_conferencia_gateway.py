from abc import ABC, abstractmethod
from src.core.entities.entities import NotaLancamento
from pandas import DataFrame


class IConferenciaGateway(ABC):
    """_summary_ Extração e transformação dos dados para gerar a conferência da folha de pagamentos.
    Inclui os dados de proventos e descontos do Demofin, os dados do relatório e as NLs geradas.
    """

    @abstractmethod
    def get_tabela_demofin(self) -> DataFrame: ...

    @abstractmethod
    def salvar_nls_conferencia(self, nls: list[NotaLancamento], fundo:str): ...

    @abstractmethod
    def salvar_dados_conferencia(
        self, proventos_folha: DataFrame, descontos_folha: DataFrame, totais: DataFrame
    ): ...

    @abstractmethod
    def salvar_dados_relatorio(self, dados_relatorio: dict[str, DataFrame]): ...

    @abstractmethod
    def salvar_dados_510(self, dados_510: DataFrame): ...
