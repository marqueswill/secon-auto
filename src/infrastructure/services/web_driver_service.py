from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

import pandas as pd
from pandas import DataFrame
import time
import os

from src.core.interfaces.i_web_driver_service import IWebDriverService
from src.config import *


class WebDriverService(IWebDriverService):
    """_summary_ Um wrapper genérico em torno do Selenium WebDriver. Configura as opções do navegador (Chrome), gerencia a sessão, manipula abas e janelas, e fornece métodos básicos de espera e navegação."""

    driver: SeleniumWebDriver

    def inicializar(self, hidden=False, download_dir=""):
        self.setup_pandas()
        self.setup_driver(hidden, download_dir)

    def finalizar(self):
        self.driver.quit()

    def setup_pandas(self):
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_colwidth", None)
        pd.set_option("display.width", 0)
        pd.set_option("display.expand_frame_repr", False)

    def setup_driver(self, hidden=False, download_dir=""):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
        options.add_argument("--log-level=3")  # Suppress Chrome logs
        options.add_argument("--silent")

        # --- NOVA CONFIGURAÇÃO DE DOWNLOAD ---
        # Cria um caminho absoluto na pasta do seu projeto: ./Downloads/Automático/

        # Garante que a pasta exista antes do Chrome tentar baixar algo nela

        if download_dir != "":
            os.makedirs(download_dir, exist_ok=True)
            # Adiciona as preferências ao Chrome
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,  # Impede a janela "Salvar como"
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            options.add_experimental_option("prefs", prefs)

        if hidden:
            options.add_argument("--headless=new")
            options.add_argument(
                "--window-size=1920,1080"
            )  # Garante que os elementos renderizem corretamente

        self.driver = webdriver.Chrome(options=options)

    def get_driver(self):
        return self.driver

    def recarregar_pagina(self):
        self.driver.refresh()
        time.sleep(1)

    def fechar_pagina_atual(self):
        self.driver.close()
        abas = self.driver.window_handles
        self.driver.switch_to.window(abas[-1])
        time.sleep(1)

    def nova_aba(self):
        self.driver.execute_script("window.open('');")
        abas = self.driver.window_handles
        self.driver.switch_to.window(abas[-1])

    def acessar_link(self, link):
        self.driver.get(link)
        msg_carregando = "/html/body/app-root/lib-layout/div[1]/div"
        self.esperar_carregamento(msg_carregando, timeout=120)

        # time.sleep(3)

    def fechar_primeira_aba(self):
        abas = self.driver.window_handles
        self.driver.switch_to.window(abas[0])
        self.driver.close()
        self.driver.switch_to.window(abas[1])

    def esperar_carregamento(self, xpath: str, timeout=60):
        start_time = time.time()

        while True:
            try:
                loading = self.driver.find_element(By.XPATH, xpath)

                current_time = time.time()
                if current_time - start_time > timeout:
                    self.driver.quit()
                    raise TimeoutException("Tempo limite para  excedido.")

                if loading.text == "Carregando":
                    time.sleep(1)
                    continue
            except:
                time.sleep(2)
                break


    def get_element_by_xpath(self, xpath:str) -> str:
        element = self.driver.find_element(By.XPATH, xpath)
        return element.text

    def get_table_by_xpath(self, xpath:str) -> DataFrame | None:
        # 1. Locate the table element
        table_element = self.driver.find_element(By.XPATH, xpath)
        
        # 2. Get the HTML of the table
        table_html = table_element.get_attribute('outerHTML')
        if table_html:
            df = pd.read_html(table_html)[0]
            return df
        else:
            return None

        # 3. Use Pandas to read the HTML string
        # read_html returns a list of DataFrames; we take the first one [0]