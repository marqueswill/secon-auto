from pypdf import PdfReader, PdfWriter, PageObject
import re
from datetime import datetime

class DemonstrativoParser:
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