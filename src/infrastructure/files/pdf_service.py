import io
import os
import re
import pandas as pd
from pypdf import PdfReader, PdfWriter, PageObject
from pandas import DataFrame, isna
from datetime import datetime

from src.core.gateways.i_pathing_gateway import IPathingGateway
from src.core.gateways.i_pdf_service import IPdfService
from src.core.gateways.i_pathing_gateway import IPathingGateway


class PdfService(IPdfService):
    """Responsável por ler e extrair dados de arquivos PDF. Possui métodos especializados para fazer o parse de diferentes tipos de documentos (Relatórios de Folha, Notas de Empenho de Diárias, guias de INSS) utilizando expressões regulares (Regex) e exportar páginas específicas de PDFs (caso do DRISS).

    Args:
        IPdfService (_type_): _description_
    """

    def __init__(self, pathing_gw: IPathingGateway):
        self.pathing_gw = pathing_gw
        super().__init__()

    def parse_relatorio_folha(self, fundo_escolhido: str) -> dict[str, DataFrame]:
        caminho_pdf_relatorio = str(self.pathing_gw.get_caminho_pdf_relatorio())
        with open(caminho_pdf_relatorio, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text.find("DEMOFIM - ATIVOS") != -1:
                    text += extracted_text.replace("\n", " ").replace("  ", " ")
                else:
                    break

        file.close()
        # text = self.pdf_svc.parse_relatorio()
        relatorios = {
            "RGPS": {"PROVENTOS": None, "DESCONTOS": None},
            "FINANCEIRO": {"PROVENTOS": None, "DESCONTOS": None},
            "CAPITALIZADO": {"PROVENTOS": None, "DESCONTOS": None},
        }

        dados_brutos = text.split("Total por Fundo de Previdência:")
        for fundo, relatorio in zip(relatorios.keys(), dados_brutos[:3]):
            inicio_proventos = relatorio.find("Proventos")
            inicio_descontos = relatorio.find("Descontos Elem. Despesa:")

            relatorios[fundo]["PROVENTOS"] = relatorio[
                inicio_proventos:inicio_descontos
            ]
            relatorios[fundo]["DESCONTOS"] = relatorio[inicio_descontos:]

        for nome_fundo, relatorio_fundo in relatorios.items():
            if (
                nome_fundo != fundo_escolhido
            ):  # Pulo extração se não for do fundo que escolhi
                continue

            padrao = re.compile(
                r"(\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2})\s-\s(.*?)\sRubrica.*?Total por Natureza:\s([\d\.,]+)"
            )

            dados_proventos = []
            for item in str(relatorio_fundo["PROVENTOS"]).split("Elem. Despesa:"):
                correspondencia = padrao.search(item)
                if correspondencia:
                    cod_nat = correspondencia.group(1).replace(".", "")
                    cod_nat = (
                        cod_nat[1:]
                        if cod_nat.startswith("3") and len(cod_nat) == 9
                        else cod_nat
                    )
                    nome_nat = correspondencia.group(2).strip()
                    total_natureza = float(
                        correspondencia.group(3).replace(".", "").replace(",", ".")
                    )
                    dados_proventos.append([nome_nat, cod_nat, total_natureza])

            dados_descontos = []
            for item in str(relatorio_fundo["DESCONTOS"]).split("Elem. Despesa:"):
                correspondencia = padrao.search(item)
                if correspondencia:
                    cod_nat = correspondencia.group(1).replace(".", "")
                    cod_nat = (
                        cod_nat[1:]
                        if cod_nat.startswith("3") and len(cod_nat) == 9
                        else cod_nat
                    )

                    nome_nat = correspondencia.group(2).strip()
                    total_natureza = float(
                        correspondencia.group(3).replace(".", "").replace(",", ".")
                    )
                    dados_descontos.append([nome_nat, cod_nat, total_natureza])

            colunas_p = ["NOME NAT", "COD NAT", "PROVENTO"]
            df_proventos = pd.DataFrame(dados_proventos, columns=pd.Index(colunas_p))

            colunas_d = ["NOME NAT", "COD NAT", "DESCONTO"]
            df_descontos = pd.DataFrame(dados_descontos, columns=pd.Index(colunas_d))

            return {
                "PROVENTOS": df_proventos,
                "DESCONTOS": df_descontos,
            }

    def parse_dados_diaria(self, caminho_pdf: str) -> dict:
        """Extrai dados de um PDF de diárias."""

        with open(caminho_pdf, "rb") as file:
            reader = PdfReader(file)
            text = ""
            notas_empenho = []
            for page in reader.pages:
                text = page.extract_text()
                text = re.sub(r"\s+", " ", text)
                text.strip()
                notas_empenho.append(text)

        file.close()

        dados = []

        for dados_brutos in notas_empenho:
            processo_match = re.search(r"Número do Processo\s*([\d/-]+)", dados_brutos)
            processo = processo_match.group(1)

            nune_match = re.search(r"Número do Documento\s*(\d{4}NE\d+)", dados_brutos)
            nune = nune_match.group(1) if nune_match else None
            # print(nune)

            credor_match = re.search(r"Credor\s*(\d+)", dados_brutos)
            credor = credor_match.group(1) if credor_match else None
            # credor = table.iloc[5, 0].split("-")[0].strip()  # linha 5, coluna 0

            valor_match = re.search(r"Transferência\s*Valor\s*([\d.,]+)", dados_brutos)
            valor = (
                float(valor_match.group(1).replace(".", "").replace(",", "."))
                if valor_match
                else None
            )

            fonte_match = re.search(
                r"(?s)Natureza da Despesa.*?(\d+\.\d+).*?Cronograma de Desembolso",
                dados_brutos,
            )
            fonte = fonte_match.group(1).split(".")[1]

            match_natureza = re.search(
                r"(?s)Natureza da Despesa.*?(\d+)\s*Cronograma de Desembolso",
                dados_brutos,
            )
            natureza = match_natureza.group(1)

            bloco_match = re.search(
                r"(?s)Subitens da Despesa(.*?)(?=No\. Licitação)", dados_brutos
            )
            if bloco_match:
                bloco_de_subitens = bloco_match.group(1)
                padrao_pares = r"(\d+)\s+([\d\.]+,\d{2})"
                pares = re.findall(padrao_pares, bloco_de_subitens)
                subitems = [par[0] for par in pares]

            subitem = subitems[0]

            dados.append(
                {
                    "nune": nune,
                    "credor": credor,
                    "fonte": fonte,
                    "valor": valor,
                    "natureza": natureza,
                    "subitem": subitem,
                }
            )

        # TODO: extrair observacao da NE
        observacao = ""

        return {"processo": processo, "observacao": observacao, "dados": dados}

    # TODO: adicionar tratamento do text antes de fazer os matches
    def parse_dados_inss(self, caminho_pdf: str):
        """Extrai dados de um PDF de diárias."""

        with open(caminho_pdf, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

        # Use a safe way to extract data with regex
        processo_match = re.search(r"PROCESSO Nº : ([\d/]+)", text)
        processo = processo_match.group(1) if processo_match else None

        cnpj_match1 = re.search(r"CNPJ DO PRESTADOR/FORNCEDOR:\s*([\d./-]+)", text)
        cnpj_match2 = re.search(r"CNPJ DA EMPRESA\s*([\d./-]+)", text)
        cnpj = (
            cnpj_match1.group(1)
            if cnpj_match1
            else cnpj_match2.group(1) if cnpj_match2 else None
        )

        tipo_servico_match = re.search(r"TIPO DE SERVIÇO: (.*?)[\s\n]", text)
        tipo_servico = (
            tipo_servico_match.group(1).strip() if tipo_servico_match else None
        )

        valor_nf_match = re.search(r"VALOR DA NF:\s*([\d.,]+)\s*R\$", text)
        valor_nf = (
            valor_nf_match.group(1).replace(".", "").replace(",", ".")
            if valor_nf_match
            else None
        )

        num_nf_match = re.search(r"[\s\n]+([\d.,]+) Emissão:", text)
        num_nf = (
            num_nf_match.group(1).strip().replace(".", "") if num_nf_match else None
        )

        data_emissao_match = re.search(r"Emissão: ([\d/]+)", text)
        data_emissao = data_emissao_match.group(1) if data_emissao_match else None

        serie_match = re.search(r"Série: ([\d]+)", text)
        serie = serie_match.group(1).strip() if serie_match else None

        tipo_inss_match = re.search(r"TIPO DE SERVIÇO INSS:\s*([\d]+)", text)
        tipo_inss = tipo_inss_match.group(1).strip() if tipo_inss_match else None

        base_calculo_inss_match = re.search(
            r"BASE DE CÁLCULO INSS:\s*([\d.,]+)\s*R\$", text
        )
        base_calculo_inss = (
            base_calculo_inss_match.group(1).replace(".", "").replace(",", ".")
            if base_calculo_inss_match
            else None
        )

        valor_inss_retido_match = re.search(
            r"VALOR DE INSS RETIDO:\s*([\d.,]+)\s*R\$", text
        )
        valor_inss_retido = (
            valor_inss_retido_match.group(1).replace(".", "").replace(",", ".")
            if valor_inss_retido_match
            else None
        )

        cprb_match = re.search(r"EMPRESA É CONTRIBUINTE DA CPRB\?\s*([\w])", text)
        cprb = cprb_match.group(1) if cprb_match else None

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
            "TIPO_SERVICO": tipo_servico,
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

        if cnpj:  # ignora pessoas físicas
            return dados_pdf
        else:
            return None

    def parse_pdf_driss(self, caminho_pdf: str) -> dict[str, list[PageObject]]:
        with open(caminho_pdf, "rb") as file:
            stream_bytes = file.read()

        stream_em_memoria = io.BytesIO(stream_bytes)

        paginas_por_empresa = {}
        reader = PdfReader(stream_em_memoria)
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

    def parse_dados_provisoes(self, fundo: str) -> dict:
        def to_number(s):
            clean_s = s.replace(".", "").replace(",", ".")
            f = float(clean_s)
            return f

        def is_number(s):
            try:
                to_number(s)
                return True
            except ValueError:
                return False

        caminho_pdf_relatorio = str(self.pathing_gw.get_caminho_pdf_relatorio())
        with open(caminho_pdf_relatorio, "rb") as file:
            text = ""
            reader = PdfReader(file)
            page = reader.pages[-1]
            extracted_text = page.extract_text()
            if extracted_text.find("Provisionamento de Férias") != -1:
                text += extracted_text.replace("\n", " ").replace("  ", " ")

        file.close()

        categorias = ["RGPS", "FINANCEIRO", "CAPITALIZADO"]
        beneficios = [
            "ADICIONAL DE FÉRIAS",
            "ABONO PECUNIÁRIO",
            "13o SALÁRIO",
            "LICENÇA PRÊMIO",
        ]
        campos = ["PROVISIONADO", "REALIZADO", "BAIXA"]
        dados = {
            cat: {ben: {campo: 0.0 for campo in campos} for ben in beneficios}
            for cat in categorias
        }

        idx_rgps = text.find("RGPS")
        idx_financeiro = text.find("FINANCEIRO")
        idx_capitalizado = text.find("CAPITALIZADO")
        idx_totais = text.find("Total:")

        dados_rgps = [
            to_number(t)
            for t in text[idx_rgps:idx_financeiro].split(" ")
            if is_number(t)
        ][1:]
        dados_financeiro = [
            to_number(t)
            for t in text[idx_financeiro:idx_capitalizado].split(" ")
            if is_number(t)
        ][1:]
        dados_capitalizado = [
            to_number(t)
            for t in text[idx_capitalizado:idx_totais].split(" ")
            if is_number(t)
        ][1:]

        todos_dados = {
            "RGPS": dados_rgps,
            "FINANCEIRO": dados_financeiro,
            "CAPITALIZADO": dados_capitalizado,
        }
        for c in categorias:
            dados_fundo = todos_dados[c]
            remuneracao = dados_fundo.pop(0)
            # dados[c]["Remuneração"] = remuneracao
            for j, b in enumerate(beneficios):
                provi = dados_fundo[j * 3]
                realiz = dados_fundo[j * 3 + 1]
                baixa = dados_fundo[j * 3 + 2]

                dados[c][b]["PROVISIONADO"] = provi
                dados[c][b]["REALIZADO"] = realiz
                dados[c][b]["BAIXA"] = baixa

        resultado = dados[fundo]

        return resultado

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
