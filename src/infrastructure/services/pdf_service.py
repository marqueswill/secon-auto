import io
import os
import re
import pandas as pd
from pypdf import PdfReader, PdfWriter, PageObject
from pandas import DataFrame, isna
from datetime import datetime

from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_pdf_service import IPdfService
from src.core.interfaces.i_pathing_gateway import IPathingGateway


class PdfService(IPdfService):
    """Responsável por ler e extrair dados de arquivos PDF. Possui métodos especializados para fazer o parse de diferentes tipos de documentos (Relatórios de Folha, Notas de Empenho de Diárias, guias de INSS) utilizando expressões regulares (Regex) e exportar páginas específicas de PDFs (caso do DRISS).

    Args:
        IPdfService (_type_): _description_
    """

    def __init__(self, pathing_gw: IPathingGateway):
        self.pathing_gw = pathing_gw
        super().__init__()

    def get_raw_text(self, caminho_pdf: str) -> str:
        text = ""
        with open(caminho_pdf, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text

    def get_pdf_pages(self, caminho_pdf:str) -> list[PageObject]:
        with open(caminho_pdf, "rb") as file:
            stream_bytes = file.read()

        stream_em_memoria = io.BytesIO(stream_bytes)

        reader = PdfReader(stream_em_memoria)
        paginas = reader.pages[:-1]
        return paginas
    
    def export_pages(self, pages: list[PageObject], path: str):
        try:
            # diretorio_de_saida = os.path.dirname(path)
            # os.makedirs(diretorio_de_saida, exist_ok=True)
            writer = PdfWriter()
            for page in pages:
                writer.add_page(page)

            with open(path, "wb") as saida:
                writer.write(saida)

        except Exception as e:
            raise Exception(f"Erro ao exportar páginas: {e}")


    # TODO: Passar para o usecase
    def get_nls_baixadas(self, lista_nls: list[str]) -> list[str]:
        download_dir = self.pathing_gw.get_caminho_download_nl()
        dados_bruto_nls: list[str] = []

        for nl in lista_nls:
            caminho_pdf = os.path.join(download_dir, f"{nl}.pdf")

            # Evita que o programa quebre se o PDF não tiver sido baixado
            if not os.path.exists(caminho_pdf):
                print(f"Aviso: Arquivo não encontrado e será pulado - {caminho_pdf}")
                continue

            with open(caminho_pdf, "rb") as file:
                reader = PdfReader(file)
                texto_completo_pdf = ""

                for page in reader.pages:
                    texto_extraido = page.extract_text()
                    if texto_extraido:
                        # Usa += para juntar o texto de todas as páginas
                        texto_completo_pdf += texto_extraido + " "

                # Aplica a limpeza no texto final (é mais eficiente fazer isso fora do loop das páginas)
                texto_completo_pdf = re.sub(r"\s+", " ", texto_completo_pdf)
                texto_completo_pdf = texto_completo_pdf.strip()

                dados_bruto_nls.append(texto_completo_pdf)

        return dados_bruto_nls
