from datetime import datetime
import locale, os

try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except locale.Error:
    # Se falhar, tenta uma localidade comum para Windows
    locale.setlocale(locale.LC_ALL, "Portuguese_Brazil.1252")

TESTE = True

ANO_ATUAL = datetime.now().year
MES_ATUAL = datetime.now().month
MES_ANTERIOR = MES_ATUAL - 1 if MES_ATUAL > 1 else 12

NOMES_MESES = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO",
]

PASTAS_MESES = [
    "01-JANEIRO",
    "02-FEVEREIRO",
    "03-MARÇO",
    "04-ABRIL",
    "05-MAIO",
    "06-JUNHO",
    "07-JULHO",
    "08-AGOSTO",
    "09-SETEMBRO",
    "10-OUTUBRO",
    "11-NOVEMBRO",
    "12-DEZEMBRO",
]


if not TESTE:
    PASTA_MES_ATUAL = PASTAS_MESES[MES_ATUAL - 1]
    PASTA_MES_ANTERIOR = PASTAS_MESES[MES_ANTERIOR - 1]

    NOME_MES_ATUAL = NOMES_MESES[MES_ATUAL - 1]
    NOME_MES_ANTERIOR = NOMES_MESES[MES_ANTERIOR - 1]


else:
    PASTA_MES_ATUAL = "TESTES"
    PASTA_MES_ANTERIOR = "TESTES"
    NOME_MES_ATUAL = "TESTES"
    NOME_MES_ANTERIOR = "TESTES"
    NOMES_MESES = ["TESTES"] * 12
    PASTAS_MESES = ["TESTES"] * 12
