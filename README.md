# App Automação de Processos SECON
## 🚀 Executando o Projeto

### 1. Inicialize o ambiente virtual (venv)

-   **Linux/Mac:**
```Bash
    python -m venv venv
    source venv/bin/activate
```
    
-   **Windows (PowerShell):**
```PowerShell
 python -m venv venv
 .\venv\Scripts\Activate.ps1
```
    

### 2. Instale as dependências
```Bash
pip install -r requirements.txt
```

### 3. Execute o Main
```Bash
python -m src.main
```


## 📦 Gerando Executáveis
Existem duas formas de gerar os executáveis das controllers:
### Opção A: Script Automático (Windows)
Esse script utiliza o pyinstaller para gerar executáveis para cada controller automaticamente:
```PowerShell
./build.bat
```

### Opção B: Manualmente (PyInstaller)
Caso você queira gerar apenas para uma controller específica,acesse a pasta raiz pelo terminal e execute o comando abaixo, substituindo os caminhos conforme necessário:

**Com console (padrão):**
```Bash
python -m PyInstaller --hiddenimport win32timezone --onefile --name "NOME_DO_EXECUTAVEL" .\src\adapters\controllers\arquivo.py
```

**Sem console (modo silencioso):** Use a flag `--noconsole` se não quiser que a janela preta do terminal apareça:
```Bash
python -m PyInstaller --hiddenimport win32timezone --onefile --noconsole --name "NOME_DO_EXECUTAVEL" .\src\adapters\controllers\arquivo.py
```
___
# 🏗️ Arquitetura do Projeto

O projeto **Automação de Processos SECON** foi construído seguindo os princípios da **Clean Architecture** (Arquitetura Limpa). O objetivo principal desta abordagem é desacoplar as regras de negócio (o que o sistema _faz_) das ferramentas externas (como o sistema _executa_), facilitando a manutenção, testes e a substituição de tecnologias (ex: trocar Selenium por outra lib, ou Excel por Banco de Dados) sem quebrar a lógica principal.

## 🧅 Camadas da Aplicação

O projeto está estruturado em camadas concêntricas, onde as dependências apontam apenas para dentro (do nível mais externo para o mais interno).
<img width="969" height="632" alt="830153b2-22ba-4def-8e4e-a3ee63b2ab5d_1938x1246" src="https://github.com/user-attachments/assets/f52de484-1a8f-4071-ae57-058c1170ebe9" />

### 1. Core (Domain/Entities e UseCases)

Localização: `src/core/`

Esta é a camada mais interna e não deve ter dependências de bibliotecas externas (como Selenium, Pandas complexo, Win32, etc), exceto tipos de dados básicos.
-   **Use Cases (`src/core/usecases`):** Contém a lógica de negócio pura. Cada classe aqui representa uma ação específica que o usuário deseja realizar (ex: `CancelamentoRPUseCase`, `PagamentoUseCase`). Eles orquestram o fluxo de dados.
    
-   **Gateways / Interfaces (`src/core/gateways`):** Definem os **contratos** (Classes Abstratas/Interfaces) que a camada de infraestrutura deve cumprir. Por exemplo, o Use Case diz "Preciso de algo que leia Excel" (`IExcelService`), mas ele não sabe _como_ o Excel é lido.

- **Entities / Domain (`src/core/domain`):** Representam os objetos de negócio da aplicação e as regras de negócio mais fundamentais. São as estruturas de dados com comportamento (métodos) que encapsulam o estado e garantem a sua validade (Ex: Proposta, Cliente, Fatura). Elas não dependem de Use Cases ou de qualquer camada externa.
> Até o presente momento ainda não foram implementadas as entidades/domínios. A maioria dos dados são DataFrames ou dicionários :p

### 2. Adapters (Controladores)

Localização: `src/adapters/controllers/`

Atuam como o ponto de entrada da aplicação para cada funcionalidade. Os _Controllers_ recebem a intenção do usuário (geralmente via menu do terminal), instanciam o Use Case correto através da _Factory_ e iniciam a execução.

-   **Exemplo:** `CancelamentoRPController` é chamado pelo `main.py`, pede inputs ao usuário se necessário e chama `CancelamentoRPUseCase.executar()`.
    

### 3. Infrastructure (O Mundo Externo)

Localização: `src/infrastructure/`

Aqui residem as implementações concretas das interfaces definidas no _Core_. É a camada "suja", onde lidamos com bibliotecas, I/O, APIs e automação.

-   **Files (`src/infrastructure/files`):** Implementações reais de leitura de arquivos (`ExcelService`, `PdfService`).
    
-   **Web (`src/infrastructure/web`):** Automação de navegador. Aqui está o `SiggoService` (Selenium) que interage com o site da Fazenda.
    
-   **Email (`src/infrastructure/email`):** Integração com Outlook (`OutlookService`).
    
-   **Services (`src/infrastructure/services`):** Serviços que unem lógica de infraestrutura, como o `PreenchimentoGateway` que traduz dados puros em ações no navegador.
    

### 4. Main & Factories

-   **`src/main.py`:** O ponto de entrada. Apenas exibe o menu e roteia para a Controller correta.
    
-   **`src/factories.py`:** Responsável pela **Injeção de Dependência**. É aqui que o "quebra-cabeça" é montado. A Factory cria o Use Case e entrega a ele as ferramentas de Infraestrutura (Excel, Selenium) que ele precisa para trabalhar.


## 🔄 Fluxo de Dados (Exemplo: Cancelamento RP)

Para ilustrar, veja como o fluxo percorre as camadas no caso de uso de Cancelamento de Restos a Pagar:

1.  **Controller (`Adapters`):** O usuário seleciona a opção no menu. O Controller chama a Factory.
    
2.  **Factory:** Cria o `ExcelService` (Infra) e o `PreenchimentoGateway` (Infra) e os injeta dentro do `CancelamentoRPUseCase`.
    
3.  **Use Case (`Core`):**
    
    -   Chama `self.excel_service.get_sheet()` (Interface) para pegar os dados.
        
    -   Aplica regras de negócio (agrupamentos, cálculos de totais, formatação de strings).
        
    -   Chama `self.preenchimento_gateway.executar(dados_tratados)`.
        
4.  **Infrastructure:** O `PreenchimentoGateway` recebe os dados limpos e usa o Selenium para digitar no site do SIGGO.


## Estudo de Caso: `IExcelService`

Um exemplo prático dessa arquitetura no projeto é a injeção de dependência da interface `IExcelService`. Atualmente, possuímos duas implementações concretas localizadas em `src/infrastructure/files`:

1.  **Implementação com `openpyxl`:** Manipulação padrão de arquivos `.xlsx`.
    
2.  **Implementação com `win32com`:** Manipulação via automação nativa do Excel no Windows.
    

**O cenário de mudança:** Inicialmente, o projeto utilizava apenas a versão com `openpyxl`. No entanto, identificou-se que a manipulação do arquivo fazia com que a planilha perdesse conexões vitais com bancos de dados externos em certas abas.

**A solução arquitetural:** Para corrigir isso, foi necessário criar uma nova implementação utilizando a biblioteca `win32com`, que interage diretamente com o aplicativo Excel instalado, preservando as conexões.

Graças à _Clean Architecture_, o processo de migração foi simples:

1.  Criamos a nova classe concreta implementando `IExcelService`.
    
2.  Alteramos a linha de instanciação na **Factory** (`src/factories.py`).
  
**Resultado:** O código das _Controllers_, dos _Use Cases_ e a antiga implementação permaneceram **intactos**. Isso demonstra o poder do desacoplamento: mudamos a tecnologia de infraestrutura sem afetar a regra de negócio.
___

# 🛠 Guia de Desenvolvimento

Para criar uma nova funcionalidade (_feature_) no projeto, o fluxo de trabalho consiste em quatro etapas principais:

1.  [**Criar o Use Case:**](#criando-um-usecase) A regra de negócio.
    
2.  [**Implementar Gateways/Services:**](#implementando-gateways) O acesso a dados ou ferramentas externas (**se necessário**).
    
3.  [**Definir a Factory:**](#definindo-uma-nova-factory) A injeção de dependências.
    
4.  [**Criar a Controller:**](#criando-uma-controller) O ponto de entrada da execução.
    


## Criando um usecase

Caso você queira implementar uma nova _feature_, você deve criar um novo **Use Case**. Isso implica também que será necessária uma nova **Controller** para executar esse caso de uso.

O processo de implementação é direto:

1.   **Crie o arquivo:** Crie um novo arquivo para o seu _usecase_.
    
2.   **Análise de dependências:** Decida quais _Services_ ou _Gateways_ serão usados.
 > **Exemplo:** O `CancelamentoRPUseCase` precisa ler dados de uma planilha (`IExcelService`), processar esses dados e então preencher páginas no Siggo (`IPreenchimentoGateway`). _Nota: Se precisar implementar novos services/gateways, confira a seção: [Implementando Gateways](#implementando-gateways)._
    
3. **Defina o método `executar`:** Este método deve conter a lógica principal, dividida em passos claros e modulares. Veja o exemplo do `CancelamentoRPUseCase`:
```python
def executar(self):
    # 1. Obter os dados da planilha
    dados_planilha = self.obter_dados_cancelamento()

    # 2. Preparar os dados para o preenchimento (gerar NLs)
    dados_preenchimento = self.preparar_dados_preenchimento(dados_planilha)

    # 3. Preencher NLs no siggo
    self.preencher_dados_siggo(dados_preenchimento)
```
4. **Implemente os sub-métodos:**
- Métodos simples como `obter_dados_cancelamento` e `preencher_dados_siggo` geralmente apenas chamam os _services/gateways_ para importar ou exportar dados.
- Métodos de processamento, como `preparar_dados_preenchimento`, conterão a lógica mais robusta e serão o "coração" do Use Case.

## Implementando Gateways
Conforme definido na arquitetura, os **Gateways** atuam como a ponte entre a lógica de negócio (Core) e o mundo externo (bibliotecas, APIs, arquivos). O objetivo é que o Core dependa apenas de **interfaces** (contratos), sem nunca saber _como_ os dados são efetivamente processados
### 1. Definir a Interface

Crie um arquivo em `src/core/gateways`.

-   **Convenção:** O arquivo deve começar com `i_` seguido do nome (ex: `i_conferencia_gateway.py`).

-   **Conteúdo:** Uma classe abstrata definindo os métodos obrigatórios, utilizando o decorador `@abstractmethod`.

### 2. Implementar a Classe Concreta
Vá até a camada de infraestrutura (`src/infrastructure`) para criar a implementação real.

> **⚠️ Nota sobre a Estrutura de Pastas:** Atualmente, o projeto divide as implementações em duas categorias: 
> -   **Serviços Externos:** Wrappers de bibliotecas (ex: `ExcelService`, `SiggoService`), localizados em pastas temáticas como `files` ou `web`.
> -   **Lógica Interna:** Adaptadores de lógica de negócio (ex: `ConferenciaGateway`, `TemplateFolhaGateway`), localizados geralmente em `src/infrastructure/services`. 

## Definindo uma nova Factory

As factories centralizam a criação dos objetos e a injeção de dependências. Elas estão unificadas no arquivo `src/factories.py`. 

Para registrar seu novo Use Case:
1.  Abra a classe `UseCaseFactory`.
2.  Crie um novo método para instanciar seu caso de uso.
3.  Instancie cada dependência necessária e injete-a no construtor do Use Case.
    

### Exemplo Prático:
Suponha que seu Use Case tenha o seguinte construtor:
```python
class CancelamentoRPUseCase:
    def __init__(self, pathing_gw: IPathingGateway, excel_svc: IExcelService, preenchimento_gw: IPreenchimentoGateway):
        self.pathing_gw = pathing_gw
        self.excel_svc = excel_svc
        self.preenchimento_gw = preenchimento_gw
```
Na `UseCaseFactory`, o método de criação ficaria assim:
```python
def create_cancelamento_rp_usecase(self) -> CancelamentoRPUseCase:
    # 1. Instanciar as dependências (Infraestrutura)
    pathing_gw: IPathingGateway = PathingGateway() # Faz a lógica de gerenciamento de caminhos
    siggo_service: ISiggoService = SiggoService() # Faz integração com o site do SIGGO
    
    # Alguns gateways podem depender de outros services (Injeção aninhada)
    preenchedor_gw: IPreenchimentoGateway = PreenchimentoGateway(siggo_service) # Preencher NLs no SIGGO

    # Configuração de parâmetros dinâmicos (ex: caminhos de arquivo)
    caminho_planilha = (
        pathing_gw.get_caminho_raiz_secon()
        + f"SECON - General\\ANO_ATUAL\\CANCELAMENTO_RP\\CANCELAMENTO_RP_{ANO_ATUAL}.xlsx"
    )
    excel_svc: IExcelService = ExcelService(caminho_planilha) 

    # 2. Instanciar e retornar o Use Case (Core)
    use_case: CancelamentoRPUseCase = CancelamentoRPUseCase(
        pathing_gw, excel_svc, preenchedor_gw
    )
    
    return use_case
```
> OBS: Como cada ExcelService trabalha com apenas UM ARQUIVO excel,  é necessário sempre passar o caminho do arquivo ao instanciá-lo. Para isso não ocorrer deve ocorrer uma refatoração da interface original e de suas classes concretas.

## Criando uma Controller

Finalmente, devemos criar a **Controller** (Controladora). Na Clean Architecture, a controller atua como um **Adapter** (Adaptador): ela é responsável por receber a interação do mundo externo (seja um clique do usuário ou um comando no terminal), converter essa intenção e chamar o caso de uso apropriado.

Ao contrário dos Use Cases, a Controller **pode** conhecer a tecnologia de interação (neste caso, o terminal/console), mas não deve conter regras de negócio complexas.

### O Processo de Criação

1.  **Instanciação da Factory:** A controller é responsável por iniciar a `UseCaseFactory` para obter o caso de uso com todas as dependências (Gateways) já injetadas.
    
2.  **Interação com Usuário (View):** Utilizamos o `ConsoleService` para mostrar menus e capturar a escolha do usuário. Futuramente podemos utilizar um `GUIService` e trocar a lógica da controller para uma mais robusta.
    
3.  **Execução:** Passamos os dados limpos para o método `executar()` do Use Case.
    

### Exemplo: ExportarValoresPagosController

Abaixo, o exemplo corrigido e comentado de uma controller simples:
```python
def ExportarValoresPagosController():
    app_view = ConsoleService() # Service para interagir com usuário
    factory = UseCaseFactory()
    use_case = factory.create_exportar_valores_pagos_uc()

    # selecão mês de interesse
    while True:
        app_view.display_menu(
            NOMES_MESES,
            "Selecione o mês:",
            selecionar_todos=False,
        )

        mes_escolhido = app_view.get_user_input(
            PASTAS_MESES,
            multipla_escolha=True,
        )

        if mes_escolhido
            # Controller passa mês escolhido na execução do usecase
            use_case.exportar_valores_pagos(mes_escolhido) 
            app_view.show_success("Valores pagos exportados com sucesso!")
            break
```
**Resumo do Fluxo**

1.  **User** interage com **Controller** (via Console).
2.  **Controller** coleta dados brutos.
3.  **Controller** chama **Use Case**.
4.  **Use Case** orquestra **Gateways** e retorna resultado.
5.  **Controller** exibe sucesso/erro para o **User**.
