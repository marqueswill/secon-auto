from abc import ABC, abstractmethod
from typing import Dict
from pandas import DataFrame

from src.core.entities.entities import (
    CabecalhoNL,
    DadosPreenchimento,
    TemplateNL,
    NotaLancamento,
)


class IPreenchimentoGateway(ABC):
    """_summary_ Preenche os dados de NLs no siggo."""

    @abstractmethod
    def executar(self, dados: list[DadosPreenchimento], divisao_par=True): ...

    @abstractmethod
    def separar_por_pagina(
        self, dataframe: DataFrame, tamanho_pagina=24
    ) -> list[NotaLancamento]: ...

    @abstractmethod
    def preparar_preechimento_cabecalho(self, cabecalho: CabecalhoNL) -> dict: ...

    @abstractmethod
    def preparar_preenchimento_nl(self, dados) -> dict: ...

    def extrair_dados_preenchidos(self) -> list[DadosPreenchimento]: ...
