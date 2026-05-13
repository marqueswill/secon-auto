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

    # mover para DrissUsecase, retornar apenas as páginas
    def get_pdfs_driss(self, caminho_pdf: str) -> list[PageObject]:
        with open(caminho_pdf, "rb") as file:
            stream_bytes = file.read()

        stream_em_memoria = io.BytesIO(stream_bytes)

        reader = PdfReader(stream_em_memoria)
        paginas = reader.pages[:-1]
        return paginas
        paginas_por_empresa = {}
        # Identifica a empresa em cada página e agrupa as páginas por empresa
        for page in reader.pages[:-1]:
            text = page.extract_text().replace("\n", " ").replace("  ", " ").strip()
            # nome da empresa sempre vem nesse padrão: relativo ao ISS proveniente dos serviços prestados por WINDOC GESTÃO DE DOCUMENTOS LTDA, com endereço:
            padrao = r"relativo ao ISS proveniente dos serviços prestados por (.*?), com endereço:"
            nome_empresa_match = re.search(padrao, text)
            if nome_empresa_match:
                nome_empresa = nome_empresa_match.group(1).strip()
                paginas_por_empresa[nome_empresa] = paginas_por_empresa.get(
                    nome_empresa, []
                ) + [page]

        return paginas_por_empresa

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

    def parse_dados_inss(self, caminho_pdf: str):
        """Extrai dados de um PDF de demonstrativo de INSS."""

        try:
            with open(caminho_pdf, "rb") as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            # Normaliza o texto: remove quebras de linha e espaços extras
            text = re.sub(r"\s+", " ", text)

            # --- Extração com Regex Flexíveis ---
            
            # Processo
            processo_match = re.search(r"PROCESSO\s*Nº\s*:?\s*([\d/]+)", text, re.IGNORECASE)
            processo = processo_match.group(1) if processo_match else None

            # CNPJ
            cnpj_match = re.search(r"(?:CNPJ.*?PRESTADOR.*?|CNPJ.*?EMPRESA.*?)\s*([\d./-]+)", text, re.IGNORECASE)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            # Valor da NF
            valor_nf_match = re.search(r"VALOR\s*DA\s*NF\s*:?.*?(?:R\$)?\s*([\d.,]+)", text, re.IGNORECASE)
            valor_nf = valor_nf_match.group(1).replace(".", "").replace(",", ".") if valor_nf_match else None

            # Número da NF
            num_nf_match = re.search(r"([\d.,]+)\s*Emissão:", text, re.IGNORECASE)
            num_nf = num_nf_match.group(1).strip().replace(".", "") if num_nf_match else None

            # Data de Emissão
            data_emissao_match = re.search(r"Emissão:\s*([\d/]+)", text, re.IGNORECASE)
            data_emissao = data_emissao_match.group(1) if data_emissao_match else None

            # Série
            serie_match = re.search(r"Série:\s*([\d]+)", text, re.IGNORECASE)
            serie = serie_match.group(1).strip() if serie_match else None

            # Tipo INSS
            tipo_inss_match = re.search(r"TIPO\s*DE\s*SERVIÇO\s*INSS\s*:?\s*([\d]+)", text, re.IGNORECASE)
            tipo_inss = tipo_inss_match.group(1).strip() if tipo_inss_match else None

            # Base de Cálculo INSS
            base_calculo_inss_match = re.search(r"BASE\s*DE\s*CÁLCULO\s*INSS\s*:?.*?(?:R\$)?\s*([\d.,]+)", text, re.IGNORECASE)
            base_calculo_inss = base_calculo_inss_match.group(1).replace(".", "").replace(",", ".") if base_calculo_inss_match else None

            # Valor INSS Retido
            valor_inss_retido_match = re.search(r"VALOR\s*DE\s*INSS\s*RETIDO\s*:?.*?(?:R\$)?\s*([\d.,]+)", text, re.IGNORECASE)
            valor_inss_retido = valor_inss_retido_match.group(1).replace(".", "").replace(",", ".") if valor_inss_retido_match else None

            # CPRB
            cprb_match = re.search(r"CONTRIBUINTE\s*DA\s*CPRB\s*\?\s*([\w])", text, re.IGNORECASE)
            cprb = cprb_match.group(1) if cprb_match else None

            # --- Debug no Terminal ---
            nome_arquivo = os.path.basename(caminho_pdf)
            if not valor_nf or not num_nf:
                print(f"  [AVISO] Dados incompletos em: {nome_arquivo} (NF: {num_nf}, Valor: {valor_nf})")
            else:
                print(f"  [OK] Lido: {nome_arquivo} - NF {num_nf}")

            dados_pdf = {
                "CHAVE": (
                    "0" * (15 - len(processo)) + processo + "," + num_nf
                    if processo and num_nf
                    else None
                ),
                "PROCESSO": processo,
                "CNPJ": (
                    str(cnpj.replace(".", "").replace("/", "").replace("-", ""))
                    if cnpj
                    else None
                ),
                "TIPO_SERVICO": "", # Pode ser preenchido se necessário
                "VALOR_NF": float(valor_nf) if valor_nf else None,
                "NUM_NF": num_nf if num_nf else None,
                "DATA_EMISSAO": (
                    datetime.strptime(data_emissao, "%d/%m/%Y").date()
                    if data_emissao
                    else None
                ),
                "SERIE": serie,
                "TIPO_INSS": tipo_inss,
                "BASE_CALCULO_INSS": (
                    float(base_calculo_inss) if base_calculo_inss else None
                ),
                "VALOR_INSS_RETIDO": (
                    float(valor_inss_retido) if valor_inss_retido else None
                ),
                "CPRB": 0 if cprb == "N" else 1,
            }

            return dados_pdf if cnpj else None

        except Exception as e:
            print(f"  [ERRO] Falha ao processar {os.path.basename(caminho_pdf)}: {e}")
            return None
