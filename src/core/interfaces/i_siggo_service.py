from abc import ABC, abstractmethod

from src.core.interfaces.i_web_driver_service import IWebDriverService


class ISiggoService(IWebDriverService):
    """_summary_ Faz a interação com o sistema Siggo."""

    @abstractmethod
    def login_siggo(self, cpf, password): ...

    @abstractmethod
    def esperar_login(self, timeout=60): ...

    @abstractmethod
    def esperar_carregamento_login(self, timeout=60): ...

    @abstractmethod
    def preencher_campos(self, campos: dict): ...

    @abstractmethod
    def selecionar_opcoes(self, opcoes: dict): ...


    @abstractmethod
    def download_nl(self, num_nl:str):...