import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException

from src.core.interfaces.i_siggo_service import ISiggoService
from src.infrastructure.services.web_driver_service import WebDriverService
from src.config import *

import requests


class SiggoService(WebDriverService, ISiggoService):
    """_summary_ Um driver especializado para o sistema SIGGO. Herda de WebDriver e adiciona lógicas específicas de negócio, como o fluxo de login no portal da fazenda, espera por elementos específicos de carregamento do sistema e métodos facilitadores para preencher campos e selecionar itens em menus dropdown."""

    def inicializar(self, hidden=False, download_dir = ""):
        self.setup_pandas()
        self.setup_driver(hidden, download_dir)
        if not hidden:
            self.esperar_login()
        else:
            self.auto_login()

    # Métodos controle de login
    def auto_login(self): ...
    def login_siggo(self, cpf, password):
        url = "https://siggo.fazenda.df.gov.br/Account/Login"
        self.driver.get(url)

        cpf_input_selector = '//*[@id="cpf"]'
        password_input_selector = '//*[@id="Password"]'
        button_selector = "/html/body/div[2]/div/div/div[1]/div/div/div[2]/form/button"

        self.driver.find_element(By.XPATH, value=cpf_input_selector).send_keys(
            cpf,
        )
        self.driver.find_element(By.XPATH, value=password_input_selector).send_keys(
            password,
        )
        self.driver.find_element(By.XPATH, button_selector).click()
        time.sleep(2)

    def esperar_login(
        self,
        timeout=300,
    ):
        url = "https://siggo.fazenda.df.gov.br/Account/Login"
        self.driver.get(url)

        start_time = time.time()

        while True:
            try:
                title = self.driver.find_element(
                    By.XPATH, '//*[@id="SIAC"]/div/div/div/div[2]/div/a/h4'
                )
                if title.text == "AFC":
                    break
            except:
                pass

            time.sleep(1)
            current_time = time.time()
            if current_time - start_time > timeout:
                self.driver.quit()
                raise TimeoutException("Tempo limite para login excedido.")

    def esperar_carregamento_login(self, timeout=60):
        start_time = time.time()

        while True:
            try:
                loading = self.driver.find_element(
                    By.XPATH, "/html/body/app-root/lib-login-callback/p"
                )

                current_time = time.time()
                if current_time - start_time > timeout:
                    self.driver.quit()
                    raise TimeoutException("Tempo limite para login excedido.")

                if loading.text == "carregando...":
                    time.sleep(1)
                    continue
            except:
                time.sleep(1)
                break

    # Métodos preenchimento de campos
    def preencher_campos(self, campos: dict):
        for campo, dado in campos.items():
            self.driver.find_element(By.XPATH, campo).send_keys(dado)

    def selecionar_opcoes(self, opcoes: dict):
        for campo, opcao in opcoes.items():
            Select(self.driver.find_element(By.XPATH, campo)).select_by_visible_text(
                opcao
            )



    def download_nl(self, num_nl: str):
        url_nl = f"https://siggo.fazenda.df.gov.br/{ANO_ATUAL}/afc/lista-nota-lancamento/detalhar/20101/1/{num_nl}"
        button_selector = "/html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[1]/div[2]/button[2]"

        self.acessar_link(url_nl)

        # Usando apenas uma forma de definir o diretório (seguro para qualquer SO)
        caminho_home = os.path.expanduser('~')
        download_dir = os.path.join(caminho_home, 'Downloads', 'Automático')
        
        # Garante que a pasta existe antes de tentar ler/salvar nela
        os.makedirs(download_dir, exist_ok=True)
        
        arquivos_antes = set(os.listdir(download_dir))
        
        # Clica no botão de download
        self.driver.find_element(By.XPATH, button_selector).click()
        
        tempo_maximo_espera = 60  # Segundos máximos para aguardar o download
        tempo_decorrido = 0
        arquivo_baixado = None
        
        while tempo_decorrido < tempo_maximo_espera:
            # Lista os arquivos agora e vê a diferença
            arquivos_agora = set(os.listdir(download_dir))
            arquivos_novos = arquivos_agora - arquivos_antes
            
            if arquivos_novos:
                # Pega o nome do arquivo que apareceu na pasta
                nome_temporario = list(arquivos_novos)[0]
                
                # O Chrome usa .crdownload ou .tmp enquanto o arquivo não termina de baixar
                if not nome_temporario.endswith('.crdownload') and not nome_temporario.endswith('.tmp'):
                    arquivo_baixado = os.path.join(download_dir, nome_temporario)
                    break # O download terminou de fato, sai do loop de espera
            
            time.sleep(1) # Espera 1 segundo e checa de novo
            tempo_decorrido += 1

        # --- NOVA ETAPA: Renomear o arquivo baixado ---
        if arquivo_baixado:
            # Define qual será o novo caminho/nome do arquivo
            novo_caminho = os.path.join(download_dir, f"{num_nl}.pdf")
            
            try:
                # os.replace renomeia e sobrescreve caso já exista um arquivo com esse nome
                os.replace(arquivo_baixado, novo_caminho)
                print(f"Sucesso: Arquivo salvo como {novo_caminho}")
            except Exception as e:
                print(f"Erro ao tentar renomear o arquivo: {e}")
        else:
            print(f"Erro: Tempo limite de {tempo_maximo_espera}s atingido. O download não concluiu.")


    # def request_pdf_nl(self, nl: str) -> bytes:
    #     """
    #     Realiza a requisição via requests utilizando a sessão do Selenium.
    #     Retorna o conteúdo binário do PDF.
    #     """

    #     params = {
    #             "reportName": "DetalhamentoNotaLancamento",
    #             "ext": "pdf",
    #             "unidadeGestoraId": "20101",
    #             "gestaoId": "1",
    #             "numeroNotaLancamento": nl, # Dinâmico conforme a lista
    #             "nomeUsuario": "***137531** - FERNANDA VIANA DE SOUZA"
    #     }

    #     try:
    #         base_url = f"https://siggoafc.fazenda.df.gov.br/{ANO_ATUAL}/api/Report/Publica"

    #         selenium_cookies = self.driver.get_cookies()
    #         session = requests.Session()
    #         for cookie in selenium_cookies:
    #             session.cookies.set(cookie['name'], cookie['value'])

    #         session.headers.update({
    #             "User-Agent": self.driver.execute_script("return navigator.userAgent;"),
    #             "Referer": self.driver.current_url,
    #         })
    #         response = requests.get(base_url, params=params, verify=True)
    #         response.raise_for_status() # Garante que a requisição funcionou (Status 200)

    #         return response.content

    #     except requests.exceptions.RequestException as e:
    #         print(f"Erro ao baixar a NL {nl}: {e}")
