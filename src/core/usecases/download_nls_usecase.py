import time
from pandas.io.common import file_path_to_url
from src.core.gateways.i_pdf_service import IPdfService
from src.config import *
from src.core.gateways.i_pathing_gateway import IPathingGateway
from src.core.gateways.i_siggo_service import ISiggoService

import requests


class DownloadNLsUsecase:
    def __init__(self, pathing_gw: IPathingGateway, pdf_svc:IPdfService, siggo_svc: ISiggoService) -> None:
        self.pathing_gw = pathing_gw
        self.pdf_svc =pdf_svc
        self.siggo_svc = siggo_svc

    def executar(self, lista_nls: list[str]):
        pdfs_nls = self.download_nls(lista_nls)
        dados = self.parse_nls(pdfs_nls)
        self.exportar_dados(dados)

    def download_nls(self, lista_nls):
        download_dir = self.pathing_gw.get_caminho_download_nl()
        # self.siggo_svc.inicializar(hidden=False, download_dir=download_dir)

        # for num_nl in lista_nls:
        #     self.siggo_svc.download_nl(num_nl)

        pdfs = self.pdf_svc.get_nls_baixadas(lista_nls)
        return pdfs

    def parse_nls(self, pdfs_nls): 
        dados = []
        for nl in pdfs_nls: 
            print(nl)
            break

    def exportar_dados(self, dados): ...
