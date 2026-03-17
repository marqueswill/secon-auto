# Use Cases
from src.infrastructure.web.siggo_service import SiggoService
from src.core.usecases.preenchimento_nl_usecase import PreenchimentoNLUseCase
from src.core.usecases.gerar_conferencia_usecase import GerarConferenciaUseCase
from src.core.usecases.preenchimento_folha_usecase import PreenchimentoFolhaUseCase
from src.core.usecases.pagamento_usecase import PagamentoUseCase

# Services
from src.infrastructure.services.preenchimento_gateway import PreenchimentoGateway
from src.infrastructure.services.conferencia_gateway import ConferenciaGateway


# Interfaces
from src.core.interfaces.i_nl_folha_gateway import ITemplateFolhaGateway
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_excel_service import IExcelService
from src.core.interfaces.i_conferencia_gateway import IConferenciaGateway
from src.core.interfaces.i_preenchimento_gateway import IPreenchimentoGateway
from src.core.interfaces.i_siggo_service import ISiggoService

# Mocks
from tests.mocks.conferencia_gateway_mock import ConferenciaGatewayMock
from tests.mocks.excel_service_mock import ExcelServiceMock
from tests.mocks.nl_folha_gateway_mock import TemplateFolhaGatewayMock
from tests.mocks.pathing_gateway_mock import PathingGatewayMock
from tests.mocks.preenchimento_gateway_mock import PreenchimentoGatewayMock
from tests.mocks.siggo_service_mock import SiggoServiceMock


class UseCaseFactoryMock:
    """
    Responsável por "montar" (construir) os use cases
    com todas as suas dependências.
    """

    def __init__(self, mocker):
        pass

    def create_pagamento_use_case(self, fundo: str) -> PagamentoUseCase:
        pathing_gw: PathingGatewayMock = PathingGatewayMock()

        caminho_planilha_conferencia = pathing_gw.get_caminho_conferencia(fundo)
        excel_svc: ExcelServiceMock = ExcelServiceMock(caminho_planilha_conferencia)

        conferencia_gw: ConferenciaGatewayMock = ConferenciaGatewayMock(
            pathing_gw=pathing_gw, excel_svc=excel_svc
        )
        nl_folha_gw: TemplateFolhaGatewayMock = TemplateFolhaGatewayMock(pathing_gw)

        use_case = PagamentoUseCase(conferencia_gw, nl_folha_gw)

        return use_case

    def create_gerar_conferencia_use_case(self, fundo: str) -> GerarConferenciaUseCase:
        """Cria o use case de Geração de Conferência pronto para usar."""

        pagamento_uc: PagamentoUseCase = self.create_pagamento_use_case(fundo)
        use_case = GerarConferenciaUseCase(pagamento_uc)
        return use_case

    def create_preenchimento_folha_use_case(
        self, fundo: str
    ) -> PreenchimentoFolhaUseCase:
        pagamento_uc: PagamentoUseCase = self.create_pagamento_use_case(fundo)

        siggo_service: ISiggoService = SiggoServiceMock()
        preenchedor_gw = PreenchimentoGatewayMock(siggo_service)

        use_case = PreenchimentoFolhaUseCase(pagamento_uc, preenchedor_gw)

        return use_case

    def create_preenchimento_nl_use_case(self) -> PreenchimentoNLUseCase:
        pathing_gw: IPathingGateway = PathingGatewayMock()
        nl_folha_gw: ITemplateFolhaGateway = TemplateFolhaGatewayMock(pathing_gw)

        siggo_service: ISiggoService = SiggoServiceMock()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGatewayMock(siggo_service)

        use_case = PreenchimentoNLUseCase(nl_folha_gw, preenchedor_gw)

        return use_case


class GatewayFactoryMock:

    def __init__(self, mocker):
        pass

    def create_conferecia_gateway(self) -> IConferenciaGateway:
        pathing_gw_mock = PathingGatewayMock()
        excel_svc_mock = ExcelServiceMock(
            pathing_gw_mock.get_caminho_conferencia("RGPS")
        )

        gateway: IConferenciaGateway = ConferenciaGateway(
            pathing_gw=pathing_gw_mock, excel_svc=excel_svc_mock
        )

        return gateway

    def create_pathing_gateway(self) -> PathingGatewayMock:
        gateway = PathingGatewayMock()
        return gateway

    def create_excel_service(self, fundo) -> ExcelServiceMock:
        pathing_gw_mock = PathingGatewayMock()
        excel_svc = ExcelServiceMock(pathing_gw_mock.get_caminho_conferencia(fundo))
        return excel_svc

    def create_excel_service_with_path(self, caminho_arquivo) -> ExcelServiceMock:
        excel_svc = ExcelServiceMock(caminho_arquivo)
        return excel_svc

    def create_preenchimento_gateway(self) -> PreenchimentoGatewayMock:
        siggo_service = SiggoServiceMock()
        gateway = PreenchimentoGatewayMock(siggo_service)
        return gateway
