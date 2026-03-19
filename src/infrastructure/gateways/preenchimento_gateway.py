from typing import Dict
from pandas import DataFrame
import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.core.interfaces.i_preenchimento_gateway import IPreenchimentoGateway
from src.core.interfaces.i_siggo_service import ISiggoService
from src.config import *

from src.core.entities.entities import CabecalhoNL, DadosPreenchimento, NotaLancamento


# TODO: verificar formato dos DFs para o preenchimento
class PreenchimentoGateway(IPreenchimentoGateway):
    """_summary_ Orquestra o processo de preenchimento automático no sistema web (SIGGO). Ele traduz os dados dos DataFrames (vindos dos casos de uso) em ações de navegação, selecionando opções e preenchendo campos na interface web através do SiggoService. Também possui funcionalidade para extrair dados já preenchidos da tela.

    Args:
        IPreenchimentoGateway (_type_): _description_
    """

    def __init__(self, siggo_service: ISiggoService):
        self.siggo_driver = siggo_service
        super().__init__()

    def executar(self, dados: list[DadosPreenchimento], divisao_par=True):
        self.siggo_driver.inicializar()
        link_lancamento_nl = (
            f"https://siggo.fazenda.df.gov.br/{ANO_ATUAL}/afc/nota-de-lancamento"
        )
        for dado in dados:
            lancamento = dado.lancamento
            caebecalho = dado.cabecalho

            if lancamento.esta_vazia():
                continue

            linhas_por_nl = 24 if divisao_par else 25
            dados_por_pagina = self.separar_por_pagina(lancamento.dados, linhas_por_nl)
            for dados_lancamentos in dados_por_pagina:
                tentativa = 0
                while True:
                    tentativa += 1
                    try:

                        self.siggo_driver.nova_aba()
                        self.siggo_driver.acessar_link(link_lancamento_nl)
                        self._remove_first_row()

                        campos_cabecalho = self.preparar_preechimento_cabecalho(
                            caebecalho
                        )
                        self.siggo_driver.selecionar_opcoes(campos_cabecalho["opcoes"])
                        self.siggo_driver.preencher_campos(campos_cabecalho["campos"])

                        campos_lancamentos = self.preparar_preenchimento_nl(
                            dados_lancamentos
                        )
                        self.siggo_driver.preencher_campos(campos_lancamentos)
                        print("Preenchimento feito com sucesso. Indo para próxima NL.")
                        break
                    except Exception as e:
                        print(f"Ocorreu um erro: {e}")
                        print(f"\nTentativas feitas: {tentativa}")
                        if tentativa == 3:
                            print(f"Preenchimento falhou 3 vezes. NL foi ignorada")
                            break
                        else:
                            print(f"Preenchimento falhou, tentando novamente.")
                            # self.siggo_driver.recarregar_pagina()
                            self.siggo_driver.fechar_pagina_atual()
                            continue

        self.siggo_driver.fechar_primeira_aba()

    # TODO: carregar cabeçalho dinamicamente
    def preparar_preechimento_cabecalho(self, cabecalho: CabecalhoNL):

        cabecalho.observacao = cabecalho.observacao.replace(
            "<MONTH>", NOME_MES_ATUAL
        ).replace("<YEAR>", str(ANO_ATUAL))

        id_campo_gestao = {
            "2 - CNPJ": '//*[@id = "cocredorCNPJ"]/input',
            "4 - UG/Gestão": '//*[@id="codigoCredor"]/input',
        }[cabecalho.credor]

        return {
            "campos": {
                '//*[@id="prioridadePagamento"]/input': cabecalho.prioridade,
                id_campo_gestao: cabecalho.gestao,
                '//*[@id="nuProcesso"]/input': cabecalho.processo,
                '//*[@id="observacao"]': cabecalho.observacao,
                '//*[@id="nuContrato"]': cabecalho.contrato,
            },
            "opcoes": {
                '//*[@id="tipoCredor"]': cabecalho.credor,
            },
        }

    def _remove_first_row(self):

        delete_button = '//*[@id="ui-fieldset-0-content"]/div/div/div[1]/div/table/tbody/tr/td[7]/button'
        driver = self.siggo_driver.get_driver()
        try:
            wait = WebDriverWait(driver, 2)
            wait.until(
                EC.invisibility_of_element_located(
                    (By.CLASS_NAME, "preloader-backdrop")
                )
            )
            botao_remover = wait.until(
                EC.element_to_be_clickable((By.XPATH, delete_button))
            )
            botao_remover.click()

        except TimeoutException:
            # print(
            #     f"ERRO: O botão 'Remover' não ficou clicável a tempo."
            # )
            raise

    def preparar_preenchimento_nl(self, dados) -> dict:
        linhas = dados.shape[0]
        campos = {}
        driver = self.siggo_driver.get_driver()
        for i in range(linhas):
            include_button = '//*[@id="incluirCampoLancamentos"]'

            wait = WebDriverWait(driver, 2)
            botao_incluir = wait.until(
                EC.element_to_be_clickable((By.XPATH, include_button))
            )
            botao_incluir.click()

            evento = str(dados.iloc[i]["EVENTO"])
            inscricao = str(dados.iloc[i]["INSCRIÇÃO"])
            class_cont = str(dados.iloc[i]["CLASS. CONT"]).replace(".", "")
            class_orc = str(dados.iloc[i]["CLASS. ORC"]).replace(".", "")
            fonte = str(dados.iloc[i]["FONTE"])
            valor = "{:.2f}".format(round(float(dados.iloc[i]["VALOR"]), 2))

            valores = [evento, inscricao, class_cont, class_orc, fonte, valor]

            for j in range(6):
                seletor = f'//*[@id="ui-fieldset-0-content"]/div/div/div[1]/div/table/tbody/tr[{i+1}]/td[{j+1}]/input'
                campos[seletor] = str(valores[j])

        return campos

    def separar_por_pagina(self, dataframe: DataFrame, tamanho_pagina=25):
        return [
            dataframe.iloc[i : i + tamanho_pagina]
            for i in range(0, len(dataframe), tamanho_pagina)
        ]

    def extrair_dados_preenchidos(self) -> list[DadosPreenchimento]:
        """
        Orquestra a extração de dados do cabeçalho e da tabela de lançamentos
        de TODAS AS ABAS de NL abertas.
        """
        driver = self.siggo_driver.get_driver()
        todos_os_dados_abas = []

        try:
            handles_abas = driver.window_handles

            for i, handle in enumerate(handles_abas):
                driver.switch_to.window(handle)

                cabecalho_data = self._extrair_dados_cabecalho()
                nl_data_df = self._extrair_dados_nl()

                todos_os_dados_abas.append(
                    DadosPreenchimento(nl_data_df, cabecalho_data)
                )

        except Exception as e:
            print(f"Erro ao iterar sobre as abas e extrair dados: {e}")
            return todos_os_dados_abas

        return todos_os_dados_abas

    def _extrair_dados_cabecalho(self) -> CabecalhoNL:
        """
        Extrai os dados preenchidos dos campos do cabeçalho da NL
        e retorna uma instância de CabecalhoNL.
        """
        driver = self.siggo_driver.get_driver()
        # Inicializa a dataclass com os valores padrão
        cabecalho = CabecalhoNL()

        try:
            # 1. Extrair "Tipo Credor" (Dropdown) -> Mapeia para cabecalho.credor
            seletor_credor = '//*[@id="tipoCredor"]'
            elemento_credor = driver.find_element(By.XPATH, seletor_credor)
            credor_selecionado = Select(elemento_credor).first_selected_option.text
            cabecalho.credor = credor_selecionado

            # 2. Extrair "Prioridade" (Input)
            seletor_prioridade = '//*[@id="prioridadePagamento"]/input'
            cabecalho.prioridade = str(
                driver.find_element(By.XPATH, seletor_prioridade).get_attribute("value")
            )

            # 3. Extrair "Gestão" (Dinâmico)
            id_campo_gestao_map = {
                "2 - CNPJ": '//*[@id = "cocredorCNPJ"]/input',
                "4 - UG/Gestão": '//*[@id="codigoCredor"]/input',
            }

            if credor_selecionado in id_campo_gestao_map:
                seletor_gestao = id_campo_gestao_map[credor_selecionado]
                cabecalho.gestao = str(
                    driver.find_element(By.XPATH, seletor_gestao).get_attribute("value")
                )
            else:
                # Mantém o padrão da dataclass ("") ou define outro
                cabecalho.gestao = ""

            # 4. Extrair "Processo" (Input)
            seletor_processo = '//*[@id="nuProcesso"]/input'
            cabecalho.processo = str(
                driver.find_element(By.XPATH, seletor_processo).get_attribute("value")
            )

            # 5. Extrair "Observação" (Textarea)
            seletor_obs = '//*[@id="observacao"]'
            cabecalho.observacao = str(
                driver.find_element(By.XPATH, seletor_obs).get_attribute("value")
            )

            # Nota: O campo 'contrato' existe na dataclass mas não na extração.
            # Ele permanecerá com o valor padrão definido na dataclass.

            return cabecalho

        except Exception as e:
            print(f"Erro ao extrair dados do cabeçalho: {e}")
            # Retorna o objeto parcialmente preenchido ou vazio, respeitando o Type Hint
            return cabecalho

    def _extrair_dados_nl(self) -> NotaLancamento:
        """
        Extrai os dados preenchidos da tabela de lançamentos.
        Retorna um DataFrame.
        """
        driver = self.siggo_driver.get_driver()
        colunas = ["EVENTO", "INSCRIÇÃO", "CLASS. CONT", "CLASS. ORC", "FONTE", "VALOR"]
        base_tbody_xpath = (
            '//*[@id="ui-fieldset-0-content"]/div/div/div[1]/div/table/tbody'
        )
        dados_coletados = []

        try:
            # Encontra todas as linhas <tr> na tabela
            linhas_elementos = driver.find_elements(By.XPATH, f"{base_tbody_xpath}/tr")
        except Exception:
            # Tabela não encontrada ou vazia
            return NotaLancamento(DataFrame(columns=pd.Index(colunas)))

        # Loop por cada linha <tr> (índice do XPath começa em 1)
        for i in range(1, len(linhas_elementos) + 1):
            linha_dados = {}
            seletor_base_linha = f"{base_tbody_xpath}/tr[{i}]"

            try:
                # Loop por cada coluna <td> (índice do XPath começa em 1)
                for j in range(1, 7):  # 6 colunas
                    seletor_input = f"{seletor_base_linha}/td[{j}]/input"
                    valor = driver.find_element(By.XPATH, seletor_input).get_attribute(
                        "value"
                    )

                    # Usa os nomes das colunas para popular o dicionário
                    nome_coluna = colunas[j - 1]
                    linha_dados[nome_coluna] = valor if valor not in [None, ""] else "."

                dados_coletados.append(linha_dados)

            except Exception as e:
                print(f"Aviso: Não foi possível ler a linha {i} da tabela. Erro: {e}")
                continue

        if not dados_coletados:
            return NotaLancamento(DataFrame(columns=pd.Index(colunas)))

        df = pd.DataFrame(dados_coletados)

        # Converte a coluna de valor para numérico, similar ao `preparar`
        if "VALOR" in df.columns:
            df["VALOR"] = (
                df["VALOR"]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".")
                .astype(float)
                .replace(0.0, 0.000001)
            )

        return NotaLancamento(df)
