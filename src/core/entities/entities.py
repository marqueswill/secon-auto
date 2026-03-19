from pandas import DataFrame
from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class NotaLancamento:
    dados: DataFrame
    nome: str = ""

    def __post_init__(self):
        self._checar_formato()

    def _checar_formato(self):
        colunas_obrigatorias = {
            "EVENTO",
            "INSCRIÇÃO",
            "CLASS. CONT",
            "CLASS. ORC",
            "FONTE",
            "VALOR",
        }

        if not colunas_obrigatorias.issubset(self.dados.columns):
            faltantes = colunas_obrigatorias - set(self.dados.columns)
            raise ValueError(
                f"NL-{self.nome}: O DataFrame não possui as colunas obrigatórias. Faltando: {faltantes}"
            )

        evento = self.dados["EVENTO"].astype(str).str.strip()
        if not evento.str.match(r"(^\d{6}$|^\.$)").all():
            raise ValueError(f"NL-{self.nome}: O evento deve conter 6 dígitos.")

        class_cont = self.dados["CLASS. CONT"].astype(str).str.strip()
        if not class_cont.str.match(r"(^\d{9}$|^\.$|^$|^nan$)").all():
            raise ValueError(
                f"NL-{self.nome}: A classificação contábil, caso existir, deve conter 9 dígitos."
            )

        class_orc = self.dados["CLASS. ORC"].astype(str).str.strip()
        if not class_orc.str.match(r"(^\d{8}$|^\.$|^$|^nan$)").all():
            raise ValueError(
                f"NL-{self.nome}: A classificação orçamentária, caso existir, deve conter 8 dígitos."
            )

    @property
    def cabecalhos(self):
        return self.dados.columns

    def esta_vazia(self) -> bool:
        return self.dados.empty


@dataclass
class TemplateNL(NotaLancamento):
    def _checar_formato(self):
        colunas_obrigatorias = {
            "EVENTO",
            "INSCRIÇÃO",
            "CLASS. CONT",
            "CLASS. ORC",
            "FONTE",
            "VALOR",
            "SOMAR",
            "SUBTRAIR",
            "TIPO",
        }

        if not colunas_obrigatorias.issubset(self.dados.columns):
            faltantes = colunas_obrigatorias - set(self.dados.columns)
            raise ValueError(
                f"NL-{self.nome}: O DataFrame não possui as colunas obrigatórias. Faltando: {faltantes}"
            )

        return super()._checar_formato()


@dataclass
class CabecalhoNL:
    prioridade: str = ""
    credor: str = ""
    gestao: str = ""
    processo: str = ""
    observacao: str = ""
    contrato: str = ""

    def get_all(self) -> dict:
        return asdict(self)


@dataclass
class DadosPreenchimento:
    lancamento: NotaLancamento
    cabecalho: CabecalhoNL

@dataclass
class ItemEmpenho:
    """Representa uma linha individual de dados dentro de uma Nota de Empenho."""
    nune: str
    credor: str
    fonte: str
    valor: float
    natureza: str
    subitem: str

@dataclass
class NotaEmpenho:
    """Entidade que agrupa os dados de um processo de empenho (ex: Diárias)."""
    processo: str
    dados: List[ItemEmpenho] = field(default_factory=list)
    observacao: str = ""

    def para_dataframe(self) -> DataFrame:
        """Converte os itens de empenho em um DataFrame para processamento ou exibição."""
        import pandas as pd
        if not self.dados:
            return pd.DataFrame()
        
        # Converte a lista de objetos ItemEmpenho em uma lista de dicionários
        dados_dict = [item.__dict__ for item in self.dados]
        return pd.DataFrame(dados_dict)

    def calcular_valor_total(self) -> float:
        """Soma o valor de todos os itens da NE."""
        return sum(item.valor for item in self.dados if item.valor)

    def esta_vazia(self) -> bool:
        """Verifica se existem dados de empenho."""
        return len(self.dados) == 0