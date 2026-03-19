import re
import pandas as pd
from pandas import DataFrame
from pypdf import PdfReader, PdfWriter, PageObject
from src.core.interfaces.i_pathing_gateway import IPathingGateway


class FolhaPagamentoParser:
    def __init__(self, pathing_gw: IPathingGateway) -> None:
        self.pathing_gw = pathing_gw

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

        relatorios: dict[str, dict[str, str | None]] = {
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
            df_proventos = DataFrame(dados_proventos, columns=pd.Index(colunas_p))

            colunas_d = ["NOME NAT", "COD NAT", "DESCONTO"]
            df_descontos = DataFrame(dados_descontos, columns=pd.Index(colunas_d))

            return {
                "PROVENTOS": df_proventos,
                "DESCONTOS": df_descontos,
            }

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
