from src.infrastructure.services.nl_folha_gateway import TemplateFolhaGateway


class TemplateFolhaGatewayMock(TemplateFolhaGateway):
    def __init__(self, pathing_gw):
        super().__init__(pathing_gw)
