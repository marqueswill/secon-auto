from typing import Any, List, Optional
import pandas as pd
import os
import win32com.client as win32
from win32com.client import CDispatch

from pandas import DataFrame

from src.core.interfaces.i_excel_service import IExcelService


# Assumindo que esta é a nova estrutura para usar o win32com
class ExcelServiceWin32(IExcelService):
    """_summary_ Classe para manipulação de arquivos Excel utilizando a biblioteca win32com. Suas funções incluem criar/carregar workbooks, ler abas como DataFrames, exportar dados com formatação (bordas, cores, cabeçalhos), deletar linhas/abas e ajustar largura de colunas.
    É útil para cenários onde é necessário interagir diretamente com a instância do Excel aberta ou preservar conexões de dados complexas que o openpyxl pode não suportar.
    Args:
        IExcelService (_type_): _description_
    """

    # excel: Optional[CDispatch] = None
    # workbook: Optional[CDispatch] = None

    def __init__(self, caminho_arquivo: str | None = None):
        if caminho_arquivo is not None:
            self.caminho_arquivo = caminho_arquivo
            self.__enter__()

    def __enter__(self):
        """Inicializa e abre o Excel e o Workbook."""
        try:
            # if self.excel:
            #     return

            # 1. Abre a Aplicação Excel (invisível para o usuário)
            self.excel = win32.Dispatch("Excel.Application")
            self.excel.Visible = False  # Defina como True para ver a mágica
            self.excel.DisplayAlerts = False  # Não exibe pop-ups de alerta

            # 2. Abre o Workbook
            if not os.path.exists(self.caminho_arquivo):
                # Cria um novo se não existir (se o excel.Application estiver aberto)
                self.workbook = self.excel.Workbooks.Add()
                self.workbook.SaveAs(self.caminho_arquivo)
            else:
                self.workbook = self.excel.Workbooks.Open(self.caminho_arquivo)

            return self
        except Exception as e:
            if self.excel:
                try:
                    self.excel.Quit()
                except:
                    pass
            raise Exception(f"Erro ao inicializar Excel via win32com: {e}")

    def __exit__(self):
        """Salva e fecha o Workbook e a Aplicação Excel."""
        if self.workbook:
            try:
                # O save preserva conexões e outros objetos complexos
                self.workbook.Save()
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")
            finally:
                self.workbook.Close(SaveChanges=True)
        if self.excel:
            self.excel.Quit()

    def exportar_para_planilha(
        self,
        table: DataFrame,
        sheet_name: str,
        start_column="A",
        start_line="1",
        title: str = "",
        clear=False,
        sum_numeric=False,
        fit_columns=True,
        write_headers=True,
    ):
        """
        Exporta o DataFrame para uma planilha usando win32com, preservando conexões.
        """

        try:
            sheet = self.workbook.Sheets(sheet_name)
        except:
            raise ValueError(
                f"A aba '{sheet_name}' não foi encontrada no arquivo Excel."
            )

        current_row = int(start_line)

        print(title)
        if title != "":
            title_cell = sheet.Range(f"{start_column}{current_row}")
            title_cell.Value = title
            title_cell.Font.Bold = True
            title_cell.Font.Size = 14
            current_row += 1

        if write_headers:
            data_to_write = [table.columns.tolist()] + table.values.tolist()
        else:
            data_to_write = table.values.tolist()

        if not data_to_write:
            if write_headers and not table.columns.empty:
                data_to_write = [table.columns.tolist()]
            else:
                print(f"DataFrame vazio. Nada exportado para a aba '{sheet_name}'.")
                return

        # 3. Define o intervalo de destino no Excel
        n_rows = len(data_to_write)
        n_cols = len(data_to_write[0])
        start_cell = f"{start_column}{start_line}"
        end_column_index = sheet.Range(start_column + "1").Column + n_cols - 1
        end_column = self.get_column_letter(end_column_index)
        end_row = current_row + n_rows - 1
        end_cell = f"{end_column}{end_row}"
        target_range = sheet.Range(f"{start_cell}:{end_cell}")

        if clear:
            sheet.Range("A1", sheet.UsedRange.SpecialCells(11)).ClearContents()

        target_range.Value = data_to_write

        if fit_columns:
            target_range.EntireColumn.AutoFit()

    def exportar_para_celula(
        self,
        sheet_name: str,
        value,
        column: str = "A",
        line: str = "1",
    ):
        """
        Escreve um valor único em uma célula específica.
        Ex: exportar_para_celula("R$ 500", "C", "10", "Resumo")
        """

        sheet = self.workbook.Sheets(sheet_name)
        cell_address = f"{column}{line}"
        sheet.Range(cell_address).Value = value
        print(f"titulo: {value}")

    def get_column_letter(self, index):
        result = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def get_sheet(
        self, sheet_name: str, as_dataframe=False, header_row=1, columns=None
    ) -> CDispatch | DataFrame:
        """
        Retorna uma aba específica do arquivo Excel.
        Se as_dataframe=True, retorna como pandas DataFrame.
        """
        if self.workbook is None:
            raise RuntimeError(
                "O workbook não foi inicializado. Carregue o arquivo antes de prosseguir."
            )

        try:
            sheet = self.workbook.Sheets(sheet_name)
        except Exception:
            raise ValueError(f"Aba '{sheet_name}' não encontrada.")

        if not as_dataframe:
            return sheet

        data_range = sheet.UsedRange
        data_values = data_range.Value

        if not data_values:
            return pd.DataFrame()

        data_list = [list(row) for row in data_values]
        try:
            headers = data_list[header_row - 1]
            rows = data_list[header_row:]
        except IndexError:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=pd.Index(headers))

        return df

    # TODO: testar pra ver se funfa
    @staticmethod
    def read_table(
        file_path: str, sheet_name: str, header_row=1, columns=None
    ) -> DataFrame:
        """
        Lê uma aba do Excel e retorna um DataFrame.
        Abre e fecha a instância do Excel automaticamente de forma segura.
        """
        with ExcelServiceWin32(file_path) as excel_svc:
            df = excel_svc.get_sheet(
                sheet_name=sheet_name,
                as_dataframe=True,
                header_row=header_row,
                columns=columns,
            )
            return df

    @staticmethod
    def export_table(table: DataFrame, sheet_name: str):
        with ExcelServiceWin32(file_path) as excel_svc:
            excel_svc.exportar_para_planilha(table, sheet_name, clear=True)

    @staticmethod
    def read_csv(caminho_csv) -> DataFrame:
        return pd.read_csv(caminho_csv)

    def delete_sheet(self, sheet_name: str) -> None:
        """
        Deleta uma aba (Worksheet) específica do Workbook pelo nome.
        """
        if not self.workbook:
            raise Exception("Workbook não está aberto.")

        # Desabilita o DisplayAlerts para suprimir o pop-up de confirmação de exclusão
        self.excel.DisplayAlerts = False
        try:
            # 1. Acessa a planilha pelo nome
            sheet = self.workbook.Sheets(sheet_name)
            # 2. Chama o método Delete()
            sheet.Delete()
            print(f"Aba '{sheet_name}' deletada com sucesso.")
        except Exception as e:
            print(f"Erro ao tentar deletar a aba '{sheet_name}': {e}")
            # Não lança o erro, apenas o imprime, pois a sheet pode não existir
        finally:
            # Restaura o DisplayAlerts
            self.excel.DisplayAlerts = True

    def delete_rows(
        self, sheet_name: str, start_row: int = 1, end_row: Optional[int] = None
    ):
        """
        Deleta linhas a partir de uma linha de início em uma planilha específica.
        Se end_row não for fornecido, deleta apenas a linha de início.
        """
        if not self.workbook:
            raise Exception("Workbook não está aberto.")

        try:
            sheet = self.workbook.Sheets(sheet_name)
        except Exception:
            print(f"Aba '{sheet_name}' não encontrada. Nenhuma linha deletada.")
            return

        # 1. Define o intervalo de linhas a ser deletado
        if end_row is None:
            # Deleta apenas a linha de início
            range_to_delete = sheet.Rows(start_row)
            msg = f"Linha {start_row}"
        else:
            # Deleta um intervalo de linhas (ex: 5:10)
            range_to_delete = sheet.Range(f"{start_row}:{end_row}")
            msg = f"Linhas {start_row} até {end_row}"

        # 2. Chama o método Delete (o valor padrão 'Shift' é xlShiftUp)
        try:
            range_to_delete.Delete()
            print(f"{msg} deletadas da aba '{sheet_name}'.")
        except Exception as e:
            print(f"Erro ao deletar {msg} da aba '{sheet_name}': {e}")

    def move_to_first(self, sheet_name: str) -> None:
        """
        Move a aba especificada para a primeira posição no Workbook.
        """
        if not self.workbook:
            raise Exception("Workbook não está aberto.")

        try:
            # 1. Acessa a aba que será movida
            sheet_to_move = self.workbook.Sheets(sheet_name)
            # 2. Acessa a primeira aba, que será o destino (Before)
            first_sheet = self.workbook.Sheets(1)

            # 3. Chama o método Move, especificando o destino (Before)
            sheet_to_move.Move(Before=first_sheet)
            print(f"Aba '{sheet_name}' movida para a primeira posição.")
        except Exception:
            raise ValueError(f"Aba '{sheet_name}' não encontrada ou erro ao mover.")

    def _hex_to_excel_color(self, hex_color: str) -> int | None:
        """
        Converte uma cor Hex (#RRGGBB) para o formato inteiro RGB aceito pelo Excel via COM.
        O Excel usa a ordem BGR (Blue-Green-Red) na construção do inteiro.
        """
        if not hex_color:
            return None

        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return 0  # Retorna preto ou padrão em caso de erro

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Fórmula para converter RGB para o Long do Excel: R + (G * 256) + (B * 65536)
        return r + (g * 256) + (b * 65536)

    def apply_conditional_formatting(
        self,
        formula: str,
        target_range: str,  # 1. Renomeado para evitar conflito com range()
        sheet_name: str,
        color: Optional[str] = None,
        filling: Optional[str] = None,
        bold: bool = False,
        underline: bool = False,
        clear_existing: bool = True,  # 2. Opção para limpar regras anteriores
    ):
        """
        Aplica formatação condicional baseada em fórmula.

        Args:
            formula (str): A fórmula em INGLÊS (Ex: '=AND($A1>0, $B1<5)').
                        Use vírgula ',' como separador de argumentos.
            target_range (str): O intervalo de células (Ex: 'A1:C10').
            sheet_name (str): Nome da aba.
            color (str, optional): Cor da fonte em Hex. Defaults to None.
            filling (str, optional): Cor de fundo em Hex. Defaults to None.
            bold (bool, optional): Negrito. Defaults to False.
            underline (bool, optional): Sublinhado. Defaults to False.
            clear_existing (bool, optional): Se True, remove formatações condicionais
                                            anteriores no range. Defaults to True.
        """
        if not self.workbook:
            raise Exception("Workbook não está aberto.")

        try:
            sheet = self.workbook.Sheets(sheet_name)
        except Exception:
            raise ValueError(f"Aba '{sheet_name}' não encontrada.")

        clean_range = target_range.lstrip("=")

        try:
            excel_range = sheet.Range(clean_range)
        except Exception as e:
            print(f"Erro ao selecionar o range '{clean_range}': {e}")
            return

        # Constante xlExpression = 2
        xlExpression = 2

        try:
            # 3. Limpeza preventiva de regras anteriores nesse range específico
            if clear_existing:
                excel_range.FormatConditions.Delete()

            # Adiciona a regra
            fc = excel_range.FormatConditions.Add(Type=xlExpression, Formula1=formula)

            # --- Aplicação de Estilos ---

            # Cor de Fundo (Interior)
            if filling:
                fc.Interior.Color = self._hex_to_excel_color(filling)

            # Cor da Fonte
            if color:
                fc.Font.Color = self._hex_to_excel_color(color)

            # Negrito
            if bold:
                fc.Font.Bold = True

            # Sublinhado (2 = xlUnderlineStyleSingle)
            if underline:
                fc.Font.Underline = 2

            # Opcional: Definir 'Parar se Verdadeiro' para evitar conflitos com outras regras fora deste range
            # fc.StopIfTrue = False

        except Exception as e:
            print(f"Erro ao aplicar formatação condicional no range {clean_range}: {e}")
            # Dica de debug para fórmulas
            print(
                f"Verifique se a fórmula '{formula}' está em Inglês e usa vírgulas como separador."
            )
