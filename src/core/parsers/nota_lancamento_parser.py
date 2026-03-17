class NotaLancamentoParser:

    def __init__(self) -> None:
        pass

    
# O executar recebe uma lista com as NLs para realizar o parse
# Acessar a página de cada NL
# Fazer parse dos dados diretamente da página para não ter que baixar o PDF
# Encapsular os dados en entidades (expandir entidades atuais)
# Exportar tudo para um excel (cada NL fica em uma aba)


# INFORMAÇÕES PARA EXTRAIR:
# Data de Emissão:
# Data de Lançamento:
# Lançado em:
# Nº Documento:
# Prioridade de Pagamento:
# Unidade Gestora:
# Gestão:
# Credor:
# Contrato:
# Fatura/NF:
# Processo:
# Histórico:
# Observação:
# 

# Tabela lançamento: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table
# Caso não consiga extrair a tabela de uma vez, fazer célular a célular conforme o seguinte:
# Linha 1 Coluna 1: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table/tbody/tr[1]/td[1]
# Linha 1 Coluna 2: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table/tbody/tr[1]/td[2]
# Linha 2 Coluna 1: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table/tbody/tr[2]/td[1]
# Linha 2 Coluna 2: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table/tbody/tr[2]/td[2]
