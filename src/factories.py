# Importe as classes CONCRETAS de infrastructure
from src.infrastructure.email.outlook_service import OutlookService
from src.infrastructure.files.pdf_service import PdfService
from src.infrastructure.files.excel_service import ExcelService
from src.infrastructure.files.excel_service_win32 import ExcelServiceWin32

from src.infrastructure.services.preenchimento_gateway import PreenchimentoGateway
from src.infrastructure.services.nl_folha_gateway import NLFolhaGateway
from src.infrastructure.services.pathing_gateway import PathingGateway
from src.infrastructure.services.conferencia_gateway import ConferenciaGateway
from src.infrastructure.web.siggo_service import SiggoService

# Importe o Use Case de core
from src.core.usecases.baixa_diarias_usecase import BaixaDiariasUseCase
from src.core.usecases.pagamento_diaria_usecase import PagamentoDiariaUseCase
from src.core.usecases.emails_driss_usecase import EmailsDrissUseCase
from src.core.usecases.extrair_dados_r2000_usecase import ExtrairDadosR2000UseCase
from src.core.usecases.gerar_conferencia_usecase import GerarConferenciaUseCase
from src.core.usecases.pagamento_usecase import PagamentoUseCase
from src.core.usecases.preenchimento_folha_usecase import PreenchimentoFolhaUseCase
from src.core.usecases.preenchimento_nl_usecase import PreenchimentoNLUseCase
from src.core.usecases.cancelamento_rp_usecase import CancelamentoRPUseCase

# Importe as INTERFACES (opcional, mas bom para type hints)
from src.core.gateways.i_conferencia_gateway import IConferenciaGateway
from src.core.gateways.i_excel_service import IExcelService
from src.core.gateways.i_nl_folha_gateway import INLFolhaGateway
from src.core.gateways.i_outlook_service import IOutlookService
from src.core.gateways.i_pathing_gateway import IPathingGateway
from src.core.gateways.i_pdf_service import IPdfService
from src.core.gateways.i_preenchimento_gateway import IPreenchimentoGateway
from src.core.gateways.i_siggo_service import ISiggoService


from src.config import ANO_ATUAL


class UseCaseFactory:
    """
    Responsável por "montar" (construir) os use cases
    com todas as suas dependências.
    """

    def create_pagamento_use_case(self, fundo: str, win32=False) -> PagamentoUseCase:
        pathing_gw: IPathingGateway = PathingGateway()

        pasta_folha = pathing_gw.get_caminho_pasta_folha()
        caminho_template_conferencia = pathing_gw.get_caminho_template_conferencia()
        caminho_planilha_conferencia = pathing_gw.get_caminho_conferencia(fundo)
        ExcelService.copy_to(
            caminho_template_conferencia,
            pasta_folha,
            f"CONFERÊNCIA_{fundo}".upper() + ".xlsx",
        )

        excel_svc: IExcelService
        if win32:
            excel_svc = ExcelService(caminho_planilha_conferencia)
        else:
            excel_svc = ExcelServiceWin32(caminho_planilha_conferencia)

        pdf_svc: IPdfService = PdfService(pathing_gw)

        conferencia_gw: IConferenciaGateway = ConferenciaGateway(
            pathing_gw=pathing_gw, excel_svc=excel_svc
        )
        nl_folha_gw: INLFolhaGateway = NLFolhaGateway(pathing_gw)

        use_case = PagamentoUseCase(conferencia_gw, nl_folha_gw, pdf_svc)

        return use_case

    def create_gerar_conferencia_use_case(self, fundo: str) -> GerarConferenciaUseCase:
        """Cria o use case de Geração de Conferência pronto para usar."""
        pathing_gw = PathingGateway()
        pagamento_uc: PagamentoUseCase = self.create_pagamento_use_case(
            fundo, win32=True
        )
        use_case = GerarConferenciaUseCase(pagamento_uc, pathing_gw)
        return use_case

    def create_preenchimento_folha_use_case(
        self, fundo: str
    ) -> PreenchimentoFolhaUseCase:
        pathing_gw: IPathingGateway = PathingGateway()

        pagamento_uc: PagamentoUseCase = self.create_pagamento_use_case(
            fundo, win32=True
        )

        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)

        use_case = PreenchimentoFolhaUseCase(pagamento_uc, preenchedor_gw, pathing_gw)

        return use_case

    def create_preenchimento_nl_use_case(self) -> PreenchimentoNLUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        nl_folha_gw: INLFolhaGateway = NLFolhaGateway(pathing_gw)

        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)

        use_case = PreenchimentoNLUseCase(nl_folha_gw, preenchedor_gw, pathing_gw)

        return use_case

    def criar_pagamento_diaria_usecase(self) -> PagamentoDiariaUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)
        pdf_svc: IPdfService = PdfService(pathing_gw)

        use_case = PagamentoDiariaUseCase(preenchedor_gw, pathing_gw, pdf_svc)
        return use_case

    def create_extrair_dados_r2000_usecase(
        self, pasta_mes_escolhido: str
    ) -> ExtrairDadosR2000UseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        pdf_svc: IPdfService = PdfService(pathing_gw)

        try:
            caminho_planilha_reinf = pathing_gw.get_caminho_reinf(pasta_mes_escolhido)
        except:
            caminho_reinf_base = pathing_gw.get_caminho_reinf()
            caminho_completo = (
                caminho_reinf_base.split("Preenchimento Reinf.xlsx")[0]
                + pasta_mes_escolhido
            )
            ExcelService.copy_to(caminho_reinf_base, caminho_completo)
            caminho_planilha_reinf = pathing_gw.get_caminho_reinf(pasta_mes_escolhido)

        excel_svc = ExcelServiceWin32(caminho_planilha_reinf)
        use_case = ExtrairDadosR2000UseCase(excel_svc, pdf_svc, pathing_gw)

        return use_case

    def create_exportar_valores_pagos_usecase(self) -> ExtrairDadosR2000UseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        pdf_svc: IPdfService = PdfService(pathing_gw)

        caminho_planilha_reinf = pathing_gw.get_caminho_valores_pagos()
        excel_svc: IExcelService = ExcelService(caminho_planilha_reinf)

        use_case = ExtrairDadosR2000UseCase(excel_svc, pdf_svc, pathing_gw)

        return use_case

    def create_emails_driss_usecase(self) -> EmailsDrissUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        pdf_svc: IPdfService = PdfService(pathing_gw)

        caminho_planilha_emails = (
            pathing_gw.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\DRISS_{ANO_ATUAL}\\EMAIL_EMPRESAS.xlsx"
        )
        excel_svc: IExcelService = ExcelService(caminho_planilha_emails)
        email_svc: IOutlookService = OutlookService()
        use_case = EmailsDrissUseCase(pathing_gw, pdf_svc, excel_svc, email_svc)
        return use_case

    def create_cancelamento_rp_usecase(self) -> CancelamentoRPUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)
        caminho_planilha = (
            pathing_gw.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\CANCELAMENTO_RP\\CANCELAMENTO_RP_{ANO_ATUAL}.xlsx"
        )
        excel_svc: IExcelService = ExcelService(caminho_planilha)
        use_case: CancelamentoRPUseCase = CancelamentoRPUseCase(
            pathing_gw, excel_svc, preenchedor_gw
        )
        return use_case

    def create_baixa_diarias_usecase(self) -> BaixaDiariasUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)

        use_case: BaixaDiariasUseCase = BaixaDiariasUseCase(pathing_gw, preenchedor_gw)
        return use_case
