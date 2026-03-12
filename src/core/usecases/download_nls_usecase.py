class DownloadNLsUsecase:
    def __init__(self) -> None:
        pass

    def executar(self, lista_nls:list[str]):...
        # PASSO 1
        # Acessar https://siggo.fazenda.df.gov.br/2026/afc/lista-nota-lancamento
        
        # PASSO 2
        # Para cada NL, clicar para imprimir e salvar na pasta desejada
        # OUUUUU usar request para dar um get em cada NL,
        # Ex: {
        # 	"GET": {
        # 		"scheme": "https",
        # 		"host": "siggoafc.fazenda.df.gov.br",
        # 		"filename": "/2026/api/Report/Publica",
        # 		"query": {
        # 			"reportName": "DetalhamentoNotaLancamento",
        # 			"ext": "pdf",
        # 			"unidadeGestoraId": "20101",
        # 			"gestaoId": "1",
        # 			"numeroNotaLancamento": "2026NL00431", #variável
        # 			"nomeUsuario": "***137531** - FERNANDA VIANA DE SOUZA"
        # 		},
        # 		"remote": {
        # 			"Endereço": "10.70.203.240:443"
        # 		}
        # 	}
        # }

        # PASSO 3
        # Salvar os PDFs em uma pasta

        # PASSO 4
        # Fazer parse desses PDF

        # PASSO 5
        # Processar o que tiver que processar

        # PASSO 6
        # Chorar

