import time
from pandas.io.common import file_path_to_url
from src.config import *
from src.core.gateways.i_pathing_gateway import IPathingGateway
from src.core.gateways.i_siggo_service import  ISiggoService

import requests

class DownloadNLsUsecase:
    def __init__(self, pathing_gw:IPathingGateway, siggo_svc: ISiggoService) -> None:
        self.pathing_gw = pathing_gw
        self.siggo_svc = siggo_svc

    def executar(self, lista_nls:list[str]):


        self.siggo_svc.inicializar(hidden=False)
        
        
        for num_nl in lista_nls:
            self.siggo_svc.download_nl(num_nl)