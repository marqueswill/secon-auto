import win32com.client as win32

from src.core.interfaces.i_outlook_service import IOutlookService


class OutlookService(IOutlookService):
    """_summary_ Implementa a automação do envio de e-mails utilizando a aplicação desktop do Microsoft Outlook (via biblioteca win32com). Permite criar e enviar e-mails com destinatário, assunto, corpo (texto ou HTML) e anexos, além de selecionar a conta de envio correta.

    Args:
        IOutlookService (_type_): _description_
    """
    def send_email(
        self,
        mail_to,
        subject,
        body,
        html,
        attachments=None,
        mail_from=None,
        inbox=None,
        send=True,
        display=False,
    ):
        try:
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)

            mail.To = mail_to
            mail.Subject = subject
            mail.Body = body
            mail.HTMLBody = html

            if attachments:
                for att in attachments:
                    mail.Attachments.Add(att)

            if mail_from:

                found_account = False

                for account in outlook.Session.Accounts:
                    if account.SmtpAddress == mail_from:
                        mail.SendUsingAccount = account
                        found_account = True
                        break

                if not found_account:
                    raise Exception(
                        f"O email {mail_from} não está conectado ao Outlook (classic). Verifique se o email está correto ou logado."
                    )

            if inbox:
                mail.SentOnBehalfOfName = inbox

            if display:
                mail.Display()

            if send:
                pass
                # mail.Send()

        except Exception as e:
            raise Exception(f"Ocorreu um erro inesperado ao enviar o email: {e}\n")
