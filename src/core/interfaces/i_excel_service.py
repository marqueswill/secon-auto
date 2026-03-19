# /src/core/gateways/i_excel_service.py

from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pandas import DataFrame


# TODO: refatorar para que o usecase inicialize a planilha desejada, e não a factory
class IExcelService(ABC):
    """
    Define a interface (contrato) para um serviço que
    manipula arquivos de planilha (Excel).
    """

    @abstractmethod
    def get_sheet(
        self,
        sheet_name: str,
        as_dataframe: bool = False,
        header_row: int = 1,
        columns: Optional[List[str]] = None,
    ) -> DataFrame | Any: ...

    @abstractmethod
    def delete_sheet(self, sheet_name: str) -> None: ...

    @abstractmethod
    def move_to_first(self, sheet_name: str) -> None: ...

    @abstractmethod
    def exportar_para_planilha(
        self,
        table: DataFrame,
        sheet_name: str,
        start_column="A",
        start_line="1",
        title = "",
        clear=False,
        sum_numeric=False,
        fit_columns=True,
        write_headers=True,
    ) -> None: ...

    @abstractmethod
    def delete_rows(self, sheet_name: str, start_row: int = 1): ...

    @abstractmethod
    def apply_conditional_formatting(
        self,
        formula: str,
        target_range: str,
        sheet_name: str,
        color: str | None = None,
        filling: str | None = None,
        bold: bool = False,
        underline: bool = False,
    ): ...

    @abstractmethod
    def exportar_para_celula(
        self,
        sheet_name: str,
        value,
        column: str = "A",
        line: str = "1",
    ): ...
