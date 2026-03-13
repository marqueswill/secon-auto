import re
import sys
from typing import Optional
from src.config import *
from src.core.gateways.i_pathing_gateway import IPathingGateway


# TODO: ajustar métodos que recebem variáveis globais de src.config para receberem parâmetros no lugar
# TODO: ajustar projeto para se livrar das variáveis globais
# TODO: modificar pathing gateway para pegar os caminhos dos arquivos salvos em uma DB, de forma
# que os caminhos possam ser setados pelo próprio usuário. Os caminhos atuais seriam o "default", mas
# não seriam fixos. Por exemplo, carreguei o template e deixo ele salvo. Fazer uma interface para os templates
# no próprio app para não depender da planilha?
class PathingGateway(IPathingGateway):
    """_summary_ Centraliza a lógica de diretórios e caminhos de arquivos do sistema. Ele detecta automaticamente se o usuário está utilizando o caminho base local ou o OneDrive e fornece os caminhos absolutos para templates, conferências, relatórios em PDF e arquivos de exportação, baseados no ano e mês atuais.

    Args:
        IPathingGateway (_type_): _description_
    """

    def __init__(self) -> None:
        self.username = os.getlogin().strip()
        super().__init__()

    def get_caminho_raiz_secon(self) -> str:
        """
        Determina o caminho correto para o arquivo de template,
        verificando se o usuário está usando o caminho base ou o do OneDrive.
        """
        username = self.username
        caminho_base = (
            f"C:\\Users\\{username}\\Tribunal de Contas do Distrito Federal\\"
        )
        caminho_onedrive = f"C:\\Users\\{username}\\OneDrive - Tribunal de Contas do Distrito Federal\\"
        if os.path.exists(caminho_base + "SECON - General\\"):
            caminho_raiz = caminho_base
        elif os.path.exists(caminho_onedrive + "SECON - General\\"):
            caminho_raiz = caminho_onedrive
        else:
            raise FileNotFoundError(
                f"Não foi possível encontrar o caminho base ou do OneDrive para o usuário {username}."
            )
        return caminho_raiz

    def get_caminho_template(self, tipo_folha: str) -> str:
        caminho = (
            self.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\FOLHA_DE_PAGAMENTO_{ANO_ATUAL}\\TEMPLATES\\TEMPLATES_NL_{tipo_folha.upper()}.xlsx"
        )

        if os.path.exists(caminho):
            return caminho
        else:
            raise FileNotFoundError(
                f"O arquivo especificado '{caminho}' não foi encontrado."
            )

    def get_caminho_conferencia(self, fundo: str):

        caminho = (
            self.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\FOLHA_DE_PAGAMENTO_{ANO_ATUAL}\\{PASTA_MES_ATUAL}\\CONFERÊNCIA_{fundo}.xlsx"
        )

        return caminho

    def get_caminho_template_conferencia(self):
        caminho = (
            self.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\FOLHA_DE_PAGAMENTO_{ANO_ATUAL}\\TEMPLATES\\TEMPLATE_CONFERÊNCIA.xlsx"
        )
        return caminho

    def get_caminho_pasta_folha(self):
        return (
            self.get_caminho_raiz_secon()
            + f"SECON - General\\ANO_ATUAL\\FOLHA_DE_PAGAMENTO_{ANO_ATUAL}\\{PASTA_MES_ATUAL}"
        )

    def get_caminho_tabela_demofin(self):
        # Crie o caminho para a pasta onde o arquivo está

        caminho_pasta = self.get_caminho_pasta_folha()

        # Defina o padrão para o nome do arquivo (DEMOFIN_TABELA)
        # 're.IGNORECASE' ignora maiúsculas/minúsculas
        # '\\' é usado para escapar o caractere especial '-'
        # '*' torna o traço opcional
        padrao_nome = re.compile(r"demofin\s*[-_]?\s*tabela\.xlsx", re.IGNORECASE)

        # Itere sobre os arquivos na pasta e encontre o que corresponde ao padrão
        caminho_completo = None
        for nome_arquivo in os.listdir(caminho_pasta):
            if padrao_nome.search(nome_arquivo):
                caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
                break

        # Verifique se o arquivo foi encontrado antes de prosseguir
        if caminho_completo:
            return caminho_completo
        else:
            raise FileNotFoundError("Nenhum arquivo DEMOFIN_TABELA foi encontrado.")

    def get_caminho_pdf_relatorio(self) -> str | None:
        diretorio_alvo = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            f"FOLHA_DE_PAGAMENTO_{ANO_ATUAL}",
            PASTA_MES_ATUAL,
        )

        caminho_pdf_relatorio = ""

        if os.path.exists(diretorio_alvo):
            for nome_arquivo in os.listdir(diretorio_alvo):
                # Converte para minúsculas para ignorar caixa alta/baixa
                nome_lower = nome_arquivo.lower()
                if nome_lower.startswith("relatórios") and nome_lower.endswith(".pdf"):
                    caminho_pdf_relatorio = os.path.join(diretorio_alvo, nome_arquivo)
                    return caminho_pdf_relatorio
        else:
            raise FileNotFoundError(
                f"Atenção: O diretório '{diretorio_alvo}' não foi encontrado."
            )

        if caminho_pdf_relatorio == "":
            raise FileNotFoundError(
                "Nenhum arquivo PDF começando com 'RELATÓRIOS' foi encontrado."
            )

    def get_current_file_path(self) -> str:
        diretorio_atual = os.path.dirname(os.path.abspath(sys.argv[0]))
        return diretorio_atual

    def listar_arquivos(self, caminho: str) -> list[str]:
        try:
            arquivos = os.listdir(caminho)
            return arquivos
        except FileNotFoundError:
            raise FileNotFoundError(
                f"O arquivo especificado '{caminho}' não foi encontrado."
            )

    def get_caminhos_nes_diaria(self, arquivos_selecionados: list[str]) -> list[str]:
        dir_path = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            "NL_AUTOMATICA",
            "NE_DIÁRIAS",
        )

        caminhos = [os.path.join(dir_path, pdf) for pdf in arquivos_selecionados]

        return caminhos

    def get_caminhos_demonstrativos(self, pasta_mes: str):
        dir_path = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            "LIQ_DESPESA",
            pasta_mes,
        )
        arquivos = os.listdir(dir_path)
        caminhos = [os.path.join(dir_path, pdf) for pdf in arquivos]

        return caminhos

    def get_caminho_reinf(self, pasta_mes: str | None = None) -> str:
        pasta_adicional = [] if not pasta_mes else [pasta_mes]

        caminho = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            "EFD-REINF",
            *pasta_adicional,
            "Preenchimento Reinf.xlsx",
        )

        if os.path.exists(caminho):
            return caminho
        else:
            raise FileNotFoundError(
                f"O arquivo especificado '{caminho}' não foi encontrado."
            )

    def get_caminho_valores_pagos(self):
        caminho = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            "EFD-REINF",
            "VALORES_PAGOS.xlsx",
        )

        if os.path.exists(caminho):
            return caminho
        else:
            raise FileNotFoundError(
                f"O arquivo especificado '{caminho}' não foi encontrado."
            )

    def get_caminho_pdf_driss(self) -> str:
        arquivo_driss = (
            f"DRISS_{f"{MES_ANTERIOR:02d}" if not TESTE else "TESTES"}_{ANO_ATUAL}.pdf"
        )
        caminho = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            f"DRISS_{ANO_ATUAL}",
            PASTA_MES_ANTERIOR,
            arquivo_driss,
        )

        if os.path.exists(caminho):
            return caminho
        else:
            raise FileNotFoundError(
                f"O arquivo especificado '{caminho}' não foi encontrado."
            )

    def get_caminhos_pdfs_envio_driss(self) -> list[str]:
        dir_path = os.path.join(
            self.get_caminho_raiz_secon(),
            "SECON - General",
            "ANO_ATUAL",
            f"DRISS_{ANO_ATUAL}",
            PASTA_MES_ANTERIOR,
            "ENVIADOS",
        )
        arquivos = os.listdir(dir_path)
        caminhos = [os.path.join(dir_path, pdf) for pdf in arquivos]

        return caminhos

    def get_downloads_path(self):
        dir_path = os.path.join("C:", "Users", self.username, "Downloads")
        return dir_path
