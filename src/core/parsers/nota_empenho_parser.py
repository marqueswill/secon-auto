from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.entities.entities import NotaEmpenho
from pypdf import PdfReader, PdfWriter, PageObject
import re 

class NotaEmpenhoParser:
    def __init__(self, pathing_gw:IPathingGateway) -> None:
        self.pathing_gw = pathing_gw

    #TODO: fazer uma versão genérica que extrai mais dados da NE
    def executar(self, caminho_pdf:str) -> NotaEmpenho:
        """Extrai dados de uma NE."""

        ...

    def parser_diarias(self, caminho_pdf: str) -> dict:
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

        for i, dados_brutos in enumerate(notas_empenho):
            processo_match = re.search(r"N[úu\ufffd]mero do Processo\s*([\d/-]+)", dados_brutos, re.IGNORECASE)
            if not processo_match:
                raise ValueError(
                    f"Campo 'Número do Processo' não encontrado na página {i + 1}. "
                    f"Verifique se o PDF está no formato esperado.\n"
                    f"Trecho do texto: {dados_brutos[:300]}"
                )
            processo = processo_match.group(1)

            nune_match = re.search(r"N[úu\ufffd]mero do Documento\s*(\d{4}NE\d+)", dados_brutos, re.IGNORECASE)
            nune = nune_match.group(1) if nune_match else None

            credor_match = re.search(r"Credor\s*(\d+)", dados_brutos)
            credor = credor_match.group(1) if credor_match else None

            valor_match = re.search(r"Transfer[êe\ufffd]ncia\s*Valor\s*([\d.,]+)", dados_brutos, re.IGNORECASE)
            valor = (
                float(valor_match.group(1).replace(".", "").replace(",", "."))
                if valor_match
                else None
            )

            # Tenta encontrar no novo formato: "Natureza da Despesa 02101 01122823185170019 1500.100000000 99999 339014"
            match_class = re.search(r"Natureza da Despesa\s+\d+\s+\d+\s+([\d\.]+)\s+\d+\s+(\d+)", dados_brutos)
            if match_class:
                fonte_raw = match_class.group(1)
                fonte = fonte_raw.split(".")[1] if "." in fonte_raw else fonte_raw
                natureza = match_class.group(2)
            else:
                fonte_match = re.search(
                    r"(?s)Natureza da Despesa.*?(\d+\.\d+).*?Cronograma de Desembolso",
                    dados_brutos,
                )
                if not fonte_match:
                    raise ValueError(
                        f"Campo 'Fonte' (Natureza da Despesa → Cronograma de Desembolso) "
                        f"não encontrado na página {i + 1}.\n"
                        f"Trecho do texto: {dados_brutos[:300]}"
                    )
                fonte = fonte_match.group(1).split(".")[1]

                match_natureza = re.search(
                    r"(?s)Natureza da Despesa.*?(\d+)\s*Cronograma de Desembolso",
                    dados_brutos,
                )
                if not match_natureza:
                    raise ValueError(
                        f"Campo 'Natureza da Despesa' não encontrado na página {i + 1}.\n"
                        f"Trecho do texto: {dados_brutos[:300]}"
                    )
                natureza = match_natureza.group(1)

            bloco_match = re.search(
                r"(?s)Subitens da Despesa(.*?)(?=No\.\s*Licita|Descri[çc\ufffd]ão)", dados_brutos, re.IGNORECASE
            )
            subitems = []
            if bloco_match:
                bloco_de_subitens = bloco_match.group(1)
                padrao_pares = r"(\d+)\s+([\d\.]+,\d{2})"
                pares = re.findall(padrao_pares, bloco_de_subitens)
                subitems = [par[0] for par in pares]

            subitem = subitems[0] if subitems else None

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
