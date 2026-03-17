from datetime import datetime
import re
from pandas import DataFrame
from pypdf import PageObject

from src.core.interfaces.i_outlook_service import IOutlookService
from src.core.interfaces.i_pathing_gateway import IPathingGateway
from src.core.interfaces.i_excel_service import IExcelService
from src.core.interfaces.i_pdf_service import IPdfService

from src.config import *


class EmailsDrissUseCase:
    def __init__(
        self,
        pathing_gw: IPathingGateway,
        pdf_svc: IPdfService,
        excel_svc: IExcelService,
        email_svc: IOutlookService,
    ):
        self.pdf_svc = pdf_svc
        self.excel_svc = excel_svc
        self.pathing_gw = pathing_gw
        self.email_svc = email_svc

    def executar(self):
        caminho_pdf = self.pathing_gw.get_caminho_pdf_driss()
        pdfs_para_enviar = self.pdf_svc.parse_pdf_driss(caminho_pdf)
        emails_para_enviar = self.encontrar_emails_para_enviar(pdfs_para_enviar)

        self.exportar_pdfs_driss(pdfs_para_enviar)
        self.preparar_envio_emails_driss(pdfs_para_enviar, emails_para_enviar)


    def preparar_envio_emails_driss(
        self,
        pdfs_para_enviar: dict[str, list[PageObject]],
        emails_para_enviar: dict[str, list[str]],
    ):

        empresas_com_email = 0
        num_pdfs = len(pdfs_para_enviar)
        empresas_nao_encontradas = []
        pdfs_exportados = self.pathing_gw.get_caminhos_pdfs_envio_driss()
        for nome_empresa, emails_empresa in emails_para_enviar.items():
            print()
            inbox_mail = "secon.gab@tc.df.gov.br"
            body, html = self.gerar_mensagem()
            subject = "Declaração de Retenção do ISS"
            attachments = [
                caminho for caminho in pdfs_exportados if nome_empresa in caminho
            ]

            if emails_empresa is None:
                empresas_nao_encontradas.append(nome_empresa)
                print(
                    f"A empresa não foi encontrada na planilha de mails: {nome_empresa}"
                )
                continue

            empresas_com_email += 1
            for email_empresa in emails_empresa:

                print(f"Preparando envio para '{email_empresa}'")

                self.email_svc.send_email(
                    mail_to=email_empresa,
                    inbox=inbox_mail,
                    subject=subject,
                    html=html,
                    body=body,
                    attachments=attachments,
                    # mail_from=mail_from,
                    send=False,
                    display=True,
                )

        print(f"\nNúmero de empresas com email: {empresas_com_email}")
        print(f"Número de pdfs para enviar  : {num_pdfs}")
        if len(empresas_nao_encontradas) > 0:
            print("Não foram encontrados emails para empresas seguintes:")
            for empresa in empresas_nao_encontradas:
                print(empresa)

    def exportar_pdfs_driss(self, pdfs_para_enviar: dict[str, list[PageObject]]):
        for nome_empresa_pdf, paginas in pdfs_para_enviar.items():
            nome_formatado = (
                nome_empresa_pdf.upper().replace("/", "-").upper().replace("  ", " ")
            )
            print(f"Exportando pdf para empresa {nome_empresa_pdf}")

            caminho_saida = (
                self.pathing_gw.get_caminho_raiz_secon()
                + f"SECON - General\\ANO_ATUAL\\DRISS_{ANO_ATUAL}\\{PASTA_MES_ANTERIOR}\\ENVIADOS\\DRISS_{NOME_MES_ANTERIOR} - {nome_formatado}.pdf"
            )
            self.pdf_svc.export_pages(paginas, caminho_saida)

    def encontrar_emails_para_enviar(
        self, pdfs_para_enviar: dict[str, list[PageObject]]
    ) -> dict[str, list[str]]:
        emails_para_enviar = {}
        for nome_empresa_pdf, _ in pdfs_para_enviar.items():
            emails_encontrados = self.encontrar_emails_empresa(nome_empresa_pdf)
            emails_para_enviar.update(
                {
                    nome_empresa_pdf: emails_encontrados,  # usa o nome do PDF ao invés da planilha
                }
            )

        return emails_para_enviar

    def encontrar_emails_empresa(self, nome_empresa_pdf: str) -> list[str]:
        planilha_emails = self.excel_svc.get_sheet(
            sheet_name="E-MAIL", as_dataframe=True, columns="B:C"
        )
        nome_pdf_limpo = nome_empresa_pdf.upper().strip()

        emails_encontrados = []
        for i, row in planilha_emails.iterrows():
            # TODO: melhorar essa lógica de sigla/abreviação
            nome_empresa_planilha = str(row["EMPRESA"]).upper().strip()
            inicio_nome_empresa = nome_empresa_planilha.split()[0]
            if nome_pdf_limpo == nome_empresa_planilha or nome_pdf_limpo.startswith(
                inicio_nome_empresa
            ):
                emails_planilha = [
                    email
                    for email in str(row["E-MAIL"]).strip().replace(" ", "").split(";")
                    if email != ""
                ]
                return emails_planilha

    def gerar_mensagem(self) -> tuple[str, str]:
        hora = datetime.now().hour
        if 0 <= hora < 12:
            saudacao = "Bom dia"
        elif 12 <= hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"

        msg_html = f"""
        <p>{saudacao},</p>
        <p>Segue anexa a Declaração de Retenção do ISS referente ao mês de {NOME_MES_ANTERIOR}/{ANO_ATUAL}.</p>
        <p>Solicito a confirmação de recebimento desta mensagem.</p>
        <br>
        <p>Atenciosamente,</p>
        <p>Serviço de Contabilidade</p>
        <p>Tribunal de Contas do Distrito Federal</p>
        """

        msg_txt = re.sub("<[^>]+>", "", msg_html).strip().replace("  ", "")

        return msg_txt, msg_html
