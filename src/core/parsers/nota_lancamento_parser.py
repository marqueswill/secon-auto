from src.core.entities.entities import NotaLancamento
from src.core.interfaces.i_siggo_service import ISiggoService
from src.core.interfaces.i_excel_service import IExcelService
from src.config import ANO_ATUAL


class NotaLancamentoParser:

    def __init__(self, siggo_svc: ISiggoService, excel_svc: IExcelService) -> None:
        self.siggo_svc = siggo_svc
        self.excel_svc = excel_svc

    # O executar recebe uma lista com as NLs para realizar o parse
    def executar(self):
        lista_nls = self.get_lista_nls()
        todos_dados_nl = []
        for num_nl in lista_nls:
            dados = self.parse_pagina_nl(num_nl)
            todos_dados_nl.append(dados)

        for tabela in todos_dados_nl:
            self.excel_svc.exportar_para_planilha(tabela, tabela.nome)

    def get_lista_nls(self) -> list[str]:
        df = self.excel_svc.get_sheet("lista_nls")
        return df["NUM_NL"].astype(str).tolist()

    def parse_pagina_nl(self, num_nl):
        # Acessar a página de cada NL
        url = f"https://siggo.fazenda.df.gov.br/{ANO_ATUAL}/afc/lista-nota-lancamento/detalhar/20101/1/{num_nl}"
        self.siggo_svc.acessar_link(url)

        xpath_tabela_nl = "/html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table"
        tabela_extraida = self.siggo_svc.get_table_by_xpath(xpath_tabela_nl)

        if tabela_extraida is not None:
            return NotaLancamento(tabela_extraida, num_nl)
        else:
            raise Exception("Tabela da NL foi não encontrada na página.")

        # Fazer parse dos dados diretamente da página para não ter que baixar o PDF
        # Encapsular os dados en entidades (expandir entidades atuais)
        # Exportar tudo para um excel (cada NL fica em uma aba)

        # INFORMAÇÕES PARA EXTRAIR:
        # Data de Emissão: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[1]/div/div[1]/input
        # Data de Lançamento:
        # Lançado em:
        # Nº Documento:
        # Prioridade de Pagamento: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[1]/div/div[5]/input
        # Unidade Gestora:
        # Gestão:
        # Credor:
        # Contrato:
        # Fatura/NF:
        # Processo:
        # Histórico:
        # Observação:
        #
