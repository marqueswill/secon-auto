from src.core.entities.entities import NotaLancamento
from src.core.interfaces.i_siggo_service import ISiggoService
from src.config import ANO_ATUAL
import pandas as pd

class NotaLancamentoParser:

    def __init__(self, siggo_svc: ISiggoService) -> None:
        self.siggo_svc = siggo_svc

    def parse_siggo(self, nls: list[str]) -> list[NotaLancamento] | None:
        def limpar_moeda(valor):
            if pd.isna(valor) or valor == "":
                return 0.0
            
            valor = str(valor).strip()
            
            # Se NÃO tem vírgula, dividimos por 100 para criar as casas decimais
            if "," not in valor:
                try:
                    valor_limpo = valor.replace(".", "")
                    return float(valor_limpo) / 100
                except ValueError:
                    return 0.0

            valor = valor.replace(".", "")  # Remove separador de milhar
            valor = valor.replace(",", ".")  # Troca decimal pt-BR para padrão Python
            
            try:
                return float(valor)
            except ValueError:
                return 0.0

        MAPEAMENTO_COLUNAS = {
            "Evento": "EVENTO",
            "Inscrição": "INSCRIÇÃO",
            "Class. Contábil": "CLASS. CONT",
            "Class. Orçamentaria": "CLASS. ORC",
            "Fonte de Recurso": "FONTE",
            "Valor": "VALOR",
        }

        SUBSTITUICOES_FONTE = {
            "1500.1": "100000000",
            "1501.1001": "100100000",
        }

        try:
            self.siggo_svc.inicializar()
            dados_extraidos: list[NotaLancamento] = []
            for num_nl in nls:
                print(f"Extraindo dados de {num_nl}")
                url = f"https://siggo.fazenda.df.gov.br/{ANO_ATUAL}/afc/lista-nota-lancamento/detalhar/20101/1/{num_nl}"
                self.siggo_svc.acessar_link(url)

                xpath_tabela_nl = "/html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table"
                tabela_extraida = self.siggo_svc.get_table_by_xpath(xpath_tabela_nl)
                if tabela_extraida is not None:
                    tabela_extraida = tabela_extraida.rename(columns=MAPEAMENTO_COLUNAS)
                    tabela_extraida.columns = [c.strip() for c in tabela_extraida.columns]
                    tabela_extraida["FONTE"] = (
                        tabela_extraida["FONTE"]
                        .astype(str)
                        .str.strip()
                        .replace(SUBSTITUICOES_FONTE)
                    )
                    tabela_extraida["VALOR"] = tabela_extraida["VALOR"].apply(limpar_moeda)
                    nota_lancamento = NotaLancamento(tabela_extraida, num_nl)
                    dados_extraidos.append(nota_lancamento)
                else:
                    raise Exception("Tabela da NL foi não encontrada na página.")
            return dados_extraidos
        except:
            print(f"Ocorreu um erro durante o parse das NLs")
        finally:
            self.siggo_svc.finalizar()


        # INFORMAÇÕES PARA EXTRAIR:
        # Tabela com dados lançamento: "/html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[3]/div/div/p-table/div/div/table"
        # Data de Emissão: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[1]/div/div[1]/input
        # Data de Lançamento:
        # Lançado em:
        # Nº Documento:
        # Prioridade de Pagamento: /html/body/app-root/lib-layout/div/app-nota-lancamento-detalhar/div/div/div[2]/form/div/div[1]/div/div[5]/input
        # Unidade Gestora:
        # Gestão:
        # Credor:
        # Contrato:
        # Fatura/NF:
        # Processo:
        # Histórico:
        # Observação:
