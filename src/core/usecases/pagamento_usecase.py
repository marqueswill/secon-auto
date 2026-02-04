from typing import cast
import numpy as np
import pandas as pd
from pandas import DataFrame
from src.core.gateways.i_pdf_service import IPdfService
from src.core.gateways.i_conferencia_gateway import IConferenciaGateway
from src.core.gateways.i_nl_folha_gateway import INLFolhaGateway
from src.core.entities.entities import NotaLancamento


class PagamentoUseCase:
    """_summary_ Contém a lógica de negócio para o processamento dos dados das folhas pagamento. Processa os dados
    do demofin e do relatório para gerar a conferência, além de gerar as NLs de folha de pagamento.
    """

    def __init__(
        self,
        conferencia_gw: IConferenciaGateway,
        nl_folha_gw: INLFolhaGateway,
        pdf_svc: IPdfService,
    ):
        self.conferencia_gw = conferencia_gw
        self.nl_folha_gw = nl_folha_gw
        self.pdf_svc = pdf_svc

    def get_dados_conferencia(self, fundo, agrupar=True, adiantamento_ferias=False):
        cod_fundos = {
            "RGPS": 1,
            "FINANCEIRO": 2,
            "CAPITALIZADO": 3,
            "INATIVO": 4,
            "PENSÃO": 5,
        }

        tabela_demofin = self.conferencia_gw.get_tabela_demofin()

        # Remove "." dos códigos
        tabela_demofin["CDG_NAT_DESPESA"] = tabela_demofin[
            "CDG_NAT_DESPESA"
        ].str.replace(".", "")

        tabela_demofin["NME_NAT_DESPESA"] = tabela_demofin[
            "NME_NAT_DESPESA"
        ].str.strip()

        tabela_demofin["NME_NAT_DESPESA"] = tabela_demofin[
            "NME_NAT_DESPESA"
        ].str.replace(r"\s+", " ", regex=True)

        # Filtra a tabela para o fundo específico
        filtro_fundo = tabela_demofin["CDG_FUNDO"] == cod_fundos[fundo]

        # Seleciona colunas de interesse
        plan_folha = tabela_demofin.loc[
            filtro_fundo,
            [
                "CDG_PROVDESC",
                "NME_NAT_DESPESA",
                "CDG_NAT_DESPESA",
                "VALOR_AUXILIAR",
                "NME_PROVDESC",
            ],
        ]

        # Identifica os proventos e descontos e os tipos de cada (compensatoria, inativo, ativo, pensionista...)
        plan_folha["RUBRICA"] = plan_folha.apply(self._cria_coluna_rubrica, axis=1)
        plan_folha["TIPO_DESPESA"] = plan_folha.apply(self._cria_coluna_tipo, axis=1)

        # Apenas valores absolutos (lógica de saldo)
        plan_folha["VALOR_AUXILIAR"] = plan_folha["VALOR_AUXILIAR"].abs()

        # Agrupa os dados por CDG_PROVDESC, NME_NAT_DESPESA, CDG_NAT_DESPESA e TIPO_DESPESA
        plan_folha = pd.pivot_table(
            plan_folha,
            values="VALOR_AUXILIAR",
            index=[
                "CDG_PROVDESC",
                "NME_NAT_DESPESA",
                "CDG_NAT_DESPESA",
                "TIPO_DESPESA",
            ],
            columns="RUBRICA",
            aggfunc="sum",
        )

        conferencia_folha = (
            plan_folha.groupby(
                ["CDG_PROVDESC", "NME_NAT_DESPESA", "CDG_NAT_DESPESA", "TIPO_DESPESA"]
            )[["PROVENTO", "DESCONTO"]]
            .agg(lambda x: np.sum(np.abs(x)))
            .reset_index()
        )

        # Aplica a função pra criar a coluna "AJUSTE"
        conferencia_folha["AJUSTE"] = conferencia_folha["CDG_PROVDESC"].apply(
            self._categorizar_rubrica
        )

        conferencia_folha.sort_values(by=["CDG_NAT_DESPESA"])

        mask = (conferencia_folha["CDG_NAT_DESPESA"].str.startswith("3")) & (
            conferencia_folha["CDG_NAT_DESPESA"].str.len() == 9
        )

        conferencia_folha.loc[mask, "CDG_NAT_DESPESA"] = conferencia_folha.loc[
            mask, "CDG_NAT_DESPESA"
        ].str.slice(1)

        if not agrupar:
            return conferencia_folha

        if adiantamento_ferias:
            conferencia_folha_final = (
                conferencia_folha.groupby(
                    ["NME_NAT_DESPESA", "CDG_NAT_DESPESA", "TIPO_DESPESA", "AJUSTE"]
                )[["PROVENTO", "DESCONTO"]]
                .agg(lambda x: np.sum(np.abs(x)))
                .reset_index()
            )
        else:
            conferencia_folha_final = (
                conferencia_folha.groupby(
                    ["NME_NAT_DESPESA", "CDG_NAT_DESPESA", "TIPO_DESPESA"]
                )[["PROVENTO", "DESCONTO"]]
                .agg(lambda x: np.sum(np.abs(x)))
                .reset_index()
            )

        return conferencia_folha_final

    # Faz distinção entre proventos e descontos
    def _cria_coluna_rubrica(self, row):
        cdg_nat_despesa = str(row["CDG_NAT_DESPESA"])
        valor = row["VALOR_AUXILIAR"]

        if cdg_nat_despesa.startswith("3"):
            if valor > 0:
                return "PROVENTO"
            else:
                return "DESCONTO"
        elif cdg_nat_despesa.startswith("2") or cdg_nat_despesa.startswith("4"):
            if valor < 0:
                return "DESCONTO"
            else:
                return "PROVENTO"
        else:
            return ""  # Ou algum outro valor padrão, se necessário

    # Identifica a rubrica de adiantamento de férias
    def _categorizar_rubrica(self, rubrica):
        if rubrica in [11962, 21962, 32191, 42191, 52191, 61962]:
            return "ADIANTAMENTO FÉRIAS"
        return ""

    def _cria_coluna_tipo(self, row):
        cdg_nat_despesa = str(row["CDG_NAT_DESPESA"])
        nome_despesa = str(row["NME_PROVDESC"])

        tipo = "ATIVO"
        if cdg_nat_despesa == "331909401" and "COMPENSATÓRIA" in nome_despesa:
            tipo = "COMPENSATÓRIA"

        if cdg_nat_despesa == "333900811":
            if "INATIVO" in nome_despesa:
                tipo = "INATIVO"
            elif "PENSIONISTA" in nome_despesa:
                tipo = "PENSIONISTA"

        return tipo

    def separar_proventos(self, conferencia_rgps_final: DataFrame):
        prov_folha = conferencia_rgps_final.loc[
            conferencia_rgps_final["CDG_NAT_DESPESA"].str.startswith("3")
        ]

        coluna_saldo_proventos = prov_folha["PROVENTO"] - prov_folha["DESCONTO"]
        prov_folha = prov_folha.loc[
            :,
            [
                "NME_NAT_DESPESA",
                "CDG_NAT_DESPESA",
                "PROVENTO",
                "DESCONTO",
                "TIPO_DESPESA",
            ],
        ].assign(SALDO=coluna_saldo_proventos)

        prov_folha = prov_folha.sort_values(by=["CDG_NAT_DESPESA"])

        return prov_folha

    def separar_descontos(self, conferencia_rgps_final: DataFrame):
        desc_folha = conferencia_rgps_final.loc[
            ~conferencia_rgps_final["CDG_NAT_DESPESA"].str.startswith("3")
        ]

        coluna_saldo_descontos = desc_folha["DESCONTO"] - desc_folha["PROVENTO"]

        desc_folha = desc_folha.loc[
            :,
            [
                "NME_NAT_DESPESA",
                "CDG_NAT_DESPESA",
                "DESCONTO",
                "PROVENTO",
                "TIPO_DESPESA",
            ],
        ].assign(SALDO=coluna_saldo_descontos)

        desc_folha = desc_folha.sort_values(by=["CDG_NAT_DESPESA"])

        return desc_folha

    def gerar_saldos(
        self, dados_conferencia_ferias, dados_proventos, dados_descontos
    ) -> dict[str, dict]:
        saldos_proventos = list(
            zip(
                dados_proventos["TIPO_DESPESA"],
                dados_proventos["CDG_NAT_DESPESA"],
                dados_proventos["SALDO"],
            )
        )
        saldos_descontos = list(
            zip(
                dados_descontos["TIPO_DESPESA"],
                dados_descontos["CDG_NAT_DESPESA"],
                dados_descontos["SALDO"],
            )
        )

        proventos_ferias = list(
            zip(
                dados_conferencia_ferias["AJUSTE"],
                dados_conferencia_ferias["CDG_NAT_DESPESA"],
                dados_conferencia_ferias["PROVENTO"],
            )
        )
        descontos_ferias = list(
            zip(
                dados_conferencia_ferias["AJUSTE"],
                dados_conferencia_ferias["CDG_NAT_DESPESA"],
                dados_conferencia_ferias["DESCONTO"],
            )
        )

        # Faz um dicionário com todos os saldos (proventos e descontos) segmentados pelo tipo do saldo
        saldos = {
            "ATIVO": {},
            "INATIVO": {},
            "COMPENSATÓRIA": {},
            "PENSIONISTA": {},
            "PROVENTO ADIANTAMENTO FÉRIAS": {},
            "DESCONTO ADIANTAMENTO FÉRIAS": {},
        }

        for line in saldos_proventos + saldos_descontos:
            saldos[line[0]][line[1]] = line[2]
        for line in proventos_ferias:
            saldos["PROVENTO ADIANTAMENTO FÉRIAS"][line[1]] = line[2]
        for line in descontos_ferias:
            saldos["DESCONTO ADIANTAMENTO FÉRIAS"][line[1]] = line[2]

        return saldos

    def get_saldos(self, fundo) -> dict[str, dict]:
        conferencia_completa = self.get_dados_conferencia(fundo)
        conferencia_ferias = self.get_dados_conferencia(fundo, adiantamento_ferias=True)

        proventos = self.separar_proventos(conferencia_completa)
        descontos = self.separar_descontos(conferencia_completa)

        saldos = self.gerar_saldos(conferencia_ferias, proventos, descontos)

        return saldos

    def get_provisoes(self, fundo) -> dict[str, dict]:
        return self.pdf_svc.parse_dados_provisoes(fundo)

    def extrair_dados_relatorio(self, fundo_escolhido: str):
        return self.pdf_svc.parse_relatorio_folha(fundo_escolhido)

    def gerar_nl_folha(
        self,
        caminho_template: str,
        nome_template: str,
        saldos: dict,
        provisoes: dict = {},
    ) -> NotaLancamento:
        """_summary_ Recebe um fundo e o nome de um nome de uma nl e preenche o template encontrado
        com os valores de saldo passados.
        """

        template = self.nl_folha_gw.carregar_template_nl(
            caminho_template, nome_template
        )

        if template is None:
            raise Exception(f"Não foi possível carregar o template: {nome_template}.")

        folha_pagamento = template.dados
        folha_pagamento["VALOR"] = 0.0

        # Calcula o valor para cada linha
        for idx, row in folha_pagamento.iterrows():
            evento = str(row.get("EVENTO", ""))
            insc = str(row.get("INSCRIÇÃO", ""))
            class_orc = str(row.get("CLASS. ORC", ""))
            class_cont = str(row.get("CLASS. CONT", ""))
            somar = row.get("SOMAR", [])
            subtrair = row.get("SUBTRAIR", [])
            tipo = (
                "ATIVO"
                if row.get("TIPO", "") in {"", "nan", "."}
                else row.get("TIPO", "")
            )

            if tipo == "MANUAL":
                folha_pagamento.at[idx, "VALOR"] = 0.000001
            elif tipo in [
                "13o SALÁRIO",
                "ABONO PECUNIÁRIO",
                "ADICIONAL DE FÉRIAS",
                "LICENÇA PRÊMIO",
            ]:
                if len(provisoes) == 0:
                    raise Exception("Não foram encontradas provisões.")
                valor_beneficio = self.obter_valor_provisionado(provisoes, tipo, evento)
                folha_pagamento.at[idx, "VALOR"] = valor_beneficio
            elif tipo in [
                "ATIVO",
                "INATIVO",
                "COMPENSATÓRIA",
                "PENSIONISTA",
                "DESCONTO ADIANTAMENTO FÉRIAS",
                "PROVENTO ADIANTAMENTO FÉRIAS",
            ]:
                valor_somar = self.soma_codigos(str(somar), saldos[tipo])
                valor_subtrair = self.soma_codigos(str(subtrair), saldos[tipo])
                valor = valor_somar - valor_subtrair
                folha_pagamento.at[idx, "VALOR"] = valor
            else:
                raise Exception(f"Tipo para cálculo de valor inválido: '{tipo}'")

        folha_pagamento.drop(columns=["SOMAR", "SUBTRAIR", "TIPO"], inplace=True)
        folha_pagamento = folha_pagamento[folha_pagamento["VALOR"] > 0]
        folha_pagamento = cast(pd.DataFrame, folha_pagamento)
        folha_pagamento = folha_pagamento.sort_values(by=["INSCRIÇÃO", "CLASS. ORC"])
        folha_pagamento.reset_index(drop=True, inplace=True)

        return NotaLancamento(folha_pagamento)

    def soma_codigos(self, codigos: str, dicionario: dict):
        lista_codigos = list(map(str.strip, codigos.split(",")))
        lista_codigos = [
            c[1:] if c.startswith("33") and len(c) == 9 else c for c in lista_codigos
        ]
        resultado = sum(float(dicionario.get(str(c), 0.0)) for c in lista_codigos)

        return resultado

    def obter_valor_provisionado(
        self, provisoes: dict, tipo: str, evento: str
    ) -> float:

        provisionado = provisoes[tipo]["PROVISIONADO"]
        realizado = provisoes[tipo]["REALIZADO"]
        baixa = provisoes[tipo]["BAIXA"]
        saldo = abs(provisionado - realizado)

        if tipo == "LICENÇA PRÊMIO":
            return provisionado

        if provisionado > realizado and evento in ["560655", "560656", "560657"]:
            return saldo

        if provisionado <= realizado and evento in ["510005", "515001"]:
            return saldo


        return 0.0

    # def gerar_nl_provisoes(self, fundo: str, saldos: dict) -> NotaLancamento:
    #     dados_provisoes = self.pdf_svc.parse_dados_provisoes()
    #     provisoes_fundo = dados_provisoes[fundo]

    #     df = DataFrame(
    #         columns=pd.Index(
    #             {
    #                 "EVENTO",
    #                 "INSCRIÇÃO",
    #                 "CLASS. CONT",
    #                 "CLASS. ORC",
    #                 "FONTE",
    #                 "VALOR",
    #             }
    #         )
    #     )

    #     for beneficio in provisoes_fundo.keys():
    #         provi = provisoes_fundo[beneficio]["Provisionado"]
    #         realiz = provisoes_fundo[beneficio]["Realizado"]
    #         baixa = provisoes_fundo[beneficio]["Baixa"]

    #         if beneficio == "Adicional de Férias":
    #             evento1 = ...
    #             evento2 = ...

    #             inscricao1 = ...
    #             inscricao2 = ...

    #             class_cont1 = ...
    #             class_cont2 = ...

    #             class_orc1 = ...
    #             class_orc2 = ...

    #             valor1 = ...
    #             valor2 = ...

    #         elif beneficio == "Abono Pecuniário":
    #             evento1 = ...
    #             evento2 = ...

    #             inscricao1 = ...
    #             inscricao2 = ...

    #             class_cont1 = ...
    #             class_cont2 = ...

    #             class_orc1 = ...
    #             class_orc2 = ...

    #             valor1 = ...
    #             valor2 = ...
    #         elif beneficio == "13º Salário":
    #             evento1 = "560655" if provi > realiz else "510005"
    #             evento2 = "" if evento1 == "560655" else "515001"

    #             inscricao1 = ...
    #             inscricao2 = ...

    #             class_cont1 = ...
    #             class_cont2 = ...

    #             class_orc1 = ...
    #             class_orc2 = ...

    #             valor1 = ...
    #             valor2 = ...
    #         elif beneficio == "Licença Prêmio":
    #             evento1 = ...
    #             evento2 = ...

    #             inscricao1 = ...
    #             inscricao2 = ...

    #             class_cont1 = ...
    #             class_cont2 = ...

    #             class_orc1 = ...
    #             class_orc2 = ...

    #             valor1 = ...
    #             valor2 = ...

    #         print(provi, realiz, baixa)
    #     print(df)
    #     print(dados_provisoes)

    #     exit()

    #     return NotaLancamento(DataFrame(), "PROVISOES")
