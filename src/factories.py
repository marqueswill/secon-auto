# Importe as classes CONCRETAS de infrastructure
from src.infrastructure.services.outlook_service import OutlookService
from src.infrastructure.services.pdf_service import PdfService
from src.infrastructure.services.excel_service import ExcelService
from src.infrastructure.services.excel_service_win32 import ExcelServiceWin32
from src.infrastructure.services.siggo_service import SiggoService

from src.infrastructure.gateways.preenchimento_gateway import PreenchimentoGateway
from src.infrastructure.gateways.nl_folha_gateway import TemplateFolhaGateway
from src.infrastructure.gateways.pathing_gateway import PathingGateway
from src.infrastructure.gateways.conferencia_gateway import ConferenciaGateway

# Importe o Use Case de core
from src.core.usecases.baixa_diarias_uc import BaixaDiariasUseCase
from src.core.usecases.pagamento_diaria_uc import PagamentoDiariaUseCase
from src.core.usecases.emails_driss_uc import EmailsDrissUseCase
from src.core.usecases.extrair_dados_r2000_uc import ExtrairDadosR2000UseCase
from src.core.usecases.gerar_conferencia_uc import GerarConferenciaUseCase
from src.core.usecases.pagamento_uc import PagamentoUseCase
from src.core.usecases.preenchimento_folha_uc import PreenchimentoFolhaUseCase
from src.core.usecases.preenchimento_nl_uc import PreenchimentoNLUseCase
from src.core.usecases.cancelamento_rp_uc import CancelamentoRPUseCase
from src.core.usecases.download_nls_uc import DownloadNLsUsecase

# Importe as INTERFACES (opcional, mas bom para type hints)
from src.core.interfaces.i_conferencia_gateway import IConferenciaGateway
from src.core.interfaces.i_excel_service import IExcelService
from src.core.interfaces.i_nl_folha_gateway import ITemplateFolhaGateway
from src.core.interfaces.i_outlook_service import IOutlookService
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_pdf_service import IPdfService
from src.core.interfaces.i_preenchimento_gateway import IPreenchimentoGateway
from src.core.interfaces.i_siggo_service import ISiggoService


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
        nl_folha_gw: ITemplateFolhaGateway = TemplateFolhaGateway(pathing_gw)

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
        nl_folha_gw: ITemplateFolhaGateway = TemplateFolhaGateway(pathing_gw)

        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)

        use_case = PreenchimentoNLUseCase(nl_folha_gw, preenchedor_gw, pathing_gw)

        return use_case

    def create_pagamento_diaria_uc(self) -> PagamentoDiariaUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)
        pdf_svc: IPdfService = PdfService(pathing_gw)

        use_case = PagamentoDiariaUseCase(preenchedor_gw, pathing_gw, pdf_svc)
        return use_case

    def create_extrair_dados_r2000_uc(
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

    def create_exportar_valores_pagos_uc(self) -> ExtrairDadosR2000UseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        pdf_svc: IPdfService = PdfService(pathing_gw)

        caminho_planilha_reinf = pathing_gw.get_caminho_valores_pagos()
        excel_svc: IExcelService = ExcelService(caminho_planilha_reinf)

        use_case = ExtrairDadosR2000UseCase(excel_svc, pdf_svc, pathing_gw)

        return use_case

    def create_emails_driss_uc(self) -> EmailsDrissUseCase:
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

    def create_cancelamento_rp_uc(self) -> CancelamentoRPUseCase:
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

    def create_baixa_diarias_uc(self) -> BaixaDiariasUseCase:
        pathing_gw: IPathingGateway = PathingGateway()
        siggo_service: ISiggoService = SiggoService()
        preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service)

        use_case: BaixaDiariasUseCase = BaixaDiariasUseCase(pathing_gw, preenchedor_gw)
        return use_case

    def create_download_nls_uc(self) -> DownloadNLsUsecase:
        pathing_gw: IPathingGateway = PathingGateway()

        siggo_service: ISiggoService = SiggoService()
        use_case: DownloadNLsUsecase = DownloadNLsUsecase(pathing_gw, siggo_service)
        return use_case
