from abc import ABC, abstractmethod

from src.infrastructure.services.web_driver_service import WebDriverService


class IOutlookService(WebDriverService):

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
    ): ...
