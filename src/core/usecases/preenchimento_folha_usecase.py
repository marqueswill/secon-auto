from typing import Dict, List
from pandas import DataFrame

from src.core.entities.entities import DadosPreenchimento
from src.core.usecases.pagamento_usecase import PagamentoUseCase
from src.core.gateways.i_preenchimento_gateway import IPreenchimentoGateway
from src.core.gateways.i_pathing_gateway import IPathingGateway


class PreenchimentoFolhaUseCase:

    def __init__(
        self,
        pagamento_uc: PagamentoUseCase,
        preenchedor_gw: IPreenchimentoGateway,
        pathing_gw: IPathingGateway,
    ):
        self.pagamento_uc = pagamento_uc
        self.preenchedor_gw = preenchedor_gw
        self.pathing_gw = pathing_gw

    def get_nomes_templates(self, fundo: str):
        return self.pagamento_uc.nl_folha_gw.get_nomes_templates(fundo)

    def get_dados_preenchidos(self) -> list[DadosPreenchimento]:
        return self.preenchedor_gw.extrair_dados_preenchidos()

    def executar(self, fundo: str, templates: list[str]) -> list[DadosPreenchimento]:
        saldos = self.pagamento_uc.get_saldos(fundo)
        provisoes = self.pagamento_uc.get_provisoes(fundo)
        dados_gerados = self._gerar_dados_para_preenchimento(fundo, templates, saldos, provisoes)
        self.preenchedor_gw.executar(dados_gerados)
        return dados_gerados

    def _gerar_dados_para_preenchimento(
        self, fundo: str, nomes_templates: list[str], saldos: dict, provisoes:dict
    ) -> list[DadosPreenchimento]:
        dados_preenchimento: list[DadosPreenchimento] = []
        caminho_template = self.pathing_gw.get_caminho_template(fundo)

        for template in nomes_templates:
            cabecalho = self.pagamento_uc.nl_folha_gw.carregar_cabecalho(
                caminho_template,
                template,
            )

            nl = self.pagamento_uc.gerar_nl_folha(
                caminho_template,
                template,
                saldos,
                provisoes
            )
            
            if nl.esta_vazia():
                continue

            dados_preenchimento.append(DadosPreenchimento(nl, cabecalho))

        return dados_preenchimento
