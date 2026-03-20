from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.entities.entities import NotaEmpenho
from pypdf import PdfReader, PdfWriter, PageObject
import re
from src.core.entities.entities import NotaEmpenho, ItemEmpenho


class NotaEmpenhoParser:
    def __init__(self, pathing_gw: IPathingGateway) -> None:
        self.pathing_gw = pathing_gw

    # TODO: implementar tipo o das NLs, só que na aba "listar nota de empenho"
    # tem duas opções: fazer o parse para cada NE de um processo desejado
    def parse_siggo(self,  processo="") -> NotaEmpenho:
        """Extrai dados de uma NE do siggo."""
        ...

    def parse_pdf(self, caminho_pdf: str) -> NotaEmpenho:
        """Extrai dados de uma NE de diárias."""

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
                ItemEmpenho(
                    credor=credor,
                    fonte=fonte,
                    natureza=natureza,
                    nune=nune,
                    subitem=subitem,
                    valor=valor,
                )
            )

        # TODO: extrair observacao da NE
        ne = NotaEmpenho(
            processo=processo,
            observacao="",
            dados=dados,
        )
        print(ne)
        return ne