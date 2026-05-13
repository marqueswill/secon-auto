# 📚 DOCUMENTAÇÃO TÉCNICA — secon-auto

> Sistema de automação de processos contábeis do SECON/TCDF (Tribunal de Contas do Distrito Federal).

---

## 1. Visão Geral

O `secon-auto` automatiza tarefas repetitivas do setor de contabilidade do TCDF:

| Opção | Processo | Descrição |
|---|---|---|
| 1 | **Folha de Pagamento** | Lê demofin/PDF de relatório, gera conferência e preenche NLs no SIGGO |
| 2 | **NL Automática** | Preenche Notas de Lançamento no SIGGO automaticamente |
| 3 | **Pagamento de Diárias** | Lê NE de diárias (PDF) e preenche NL no SIGGO |
| 4 | **Extrair Dados R2000** | Lê demonstrativos de INSS (PDF), gera planilhas R-2010-1/2 para EFD-REINF |
| 5 | **Exportar Valores Pagos** | Exporta valores de NFs pagas para planilha de controle |
| 6 | **E-mails DRISS** | Divide PDF do DRISS por empresa e prepara e-mails via Outlook |
| 7 | **Cancelamento de RP** | Lê planilha de Restos a Pagar e preenche NLs de cancelamento |
| 8 | **Baixa de Diárias** | Lê CSV de adiantamentos e preenche NLs de baixa no SIGGO |

---

## 2. Arquitetura — Clean Architecture

```
src/
├── core/                    ← REGRAS DE NEGÓCIO (sem dependências externas)
│   ├── entities/            ← Entidades de domínio (dataclasses)
│   ├── interfaces/          ← Contratos/ABCs
│   ├── parsers/             ← Extração de dados de PDFs
│   └── usecases/            ← Lógica de cada processo
│
├── infrastructure/          ← IMPLEMENTAÇÕES CONCRETAS
│   ├── gateways/            ← Acesso a arquivos e ao SIGGO
│   └── services/            ← Excel, PDF, Outlook, WebDriver
│
├── adapters/                ← INTERFACE COM USUÁRIO
│   └── controllers/         ← Recebem input e orquestram
│
├── factories.py             ← Injeção de dependências
├── config.py                ← Configurações globais
└── main.py                  ← Menu principal
```

### Fluxo de execução

```
main.py → Controller → UseCaseFactory → UseCase → Gateway/Service → SIGGO / Excel / PDF
```

---

## 3. `config.py` — Configurações Globais

| Variável | Descrição | Exemplo |
|---|---|---|
| `TESTE` | Se `True`, usa pasta `"TESTES"` em tudo | `False` |
| `ANO_ATUAL` | Ano corrente | `2025` |
| `MES_ATUAL` | Mês corrente (1–12) | `5` |
| `MES_ANTERIOR` | Mês anterior (trata virada de ano) | `4` |
| `NOME_MES_ATUAL` | Nome do mês atual | `"MAIO"` |
| `NOME_MES_ANTERIOR` | Nome do mês anterior | `"ABRIL"` |
| `PASTA_MES_ATUAL` | Pasta do mês atual | `"05-MAIO"` |
| `PASTA_MES_ANTERIOR` | Pasta do mês anterior | `"04-ABRIL"` |

> ⚠️ Para rodar em modo de teste: `TESTE = True` em `config.py`.

---

## 4. `main.py` — Menu Principal

Exibe menu numerado no console. Usuário digita número ou `X` para sair. Instancia o Controller correspondente e captura erros sem encerrar o programa.

---

## 5. `factories.py` — UseCaseFactory

Centraliza a criação de use cases com dependências já injetadas.

| Método | Use Case |
|---|---|
| `create_pagamento_use_case(fundo)` | `PagamentoUseCase` |
| `create_gerar_conferencia_use_case(fundo)` | `GerarConferenciaUseCase` |
| `create_preenchimento_folha_use_case(fundo)` | `PreenchimentoFolhaUseCase` |
| `create_preenchimento_nl_use_case()` | `PreenchimentoNLUseCase` |
| `create_pagamento_diaria_uc()` | `PagamentoDiariaUseCase` |
| `create_extrair_dados_r2000_uc(pasta_mes)` | `ExtrairDadosR2000UseCase` |
| `create_exportar_valores_pagos_uc()` | `ExtrairDadosR2000UseCase` |
| `create_emails_driss_uc()` | `EmailsDrissUseCase` |
| `create_cancelamento_rp_uc()` | `CancelamentoRPUseCase` |
| `create_baixa_diarias_uc()` | `BaixaDiariasUseCase` |
| `create_download_nls_uc()` | `DownloadNLsUsecase` |

> 💡 Ao criar novo use case, adicione o método `create_X_uc()` aqui.

---

## 6. Entidades (`core/entities/entities.py`)

### `NotaLancamento`
Dados tabulares de uma NL. Valida automaticamente no `__post_init__`:
- Colunas obrigatórias: `EVENTO`, `INSCRIÇÃO`, `CLASS. CONT`, `CLASS. ORC`, `FONTE`, `VALOR`
- `EVENTO` → 6 dígitos | `CLASS. CONT` → 9 dígitos | `CLASS. ORC` → 8 dígitos

### `TemplateNL` (herda `NotaLancamento`)
Adiciona colunas: `SOMAR`, `SUBTRAIR`, `TIPO`.

### `CabecalhoNL`
Campos do cabeçalho da NL no SIGGO: `prioridade`, `credor`, `gestao`, `processo`, `observacao`, `contrato`.

### `DadosPreenchimento`
Agrupa `NotaLancamento + CabecalhoNL` para passar ao `PreenchimentoGateway`.

### `NotaEmpenho` / `ItemEmpenho`
Dados de NEs (Notas de Empenho) de diárias.

---

## 7. Interfaces (`core/interfaces/`)

| Interface | Implementações |
|---|---|
| `IExcelService` | `ExcelService` (openpyxl), `ExcelServiceWin32` (COM) |
| `IPdfService` | `PdfService` |
| `ISiggoService` | `SiggoService` |
| `IOutlookService` | `OutlookService` |
| `IPathingGateway` | `PathingGateway` |
| `IPreenchimentoGateway` | `PreenchimentoGateway` |
| `IConferenciaGateway` | `ConferenciaGateway` |
| `ITemplateFolhaGateway` | `TemplateFolhaGateway` |

---

## 8. Parsers (`core/parsers/`)

### `DemonstrativoParser.parse_dados_inss(caminho_pdf)` → `dict | None`
Extrai via Regex do PDF de guia de INSS:

| Campo retornado | Regex buscado no PDF |
|---|---|
| `PROCESSO` | `"PROCESSO Nº : XXXX"` |
| `CNPJ` | `"CNPJ DO PRESTADOR/FORNECEDOR: ..."` |
| `VALOR_NF` | `"VALOR DA NF: R$ X.XXX,XX"` |
| `NUM_NF` | Número antes de `"Emissão:"` |
| `DATA_EMISSAO` | `"Emissão: DD/MM/YYYY"` |
| `TIPO_INSS` | `"TIPO DE SERVIÇO INSS: N"` |
| `BASE_CALCULO_INSS` | `"BASE DE CÁLCULO INSS: ..."` |
| `VALOR_INSS_RETIDO` | `"VALOR DE INSS RETIDO: ..."` |
| `CPRB` | `"CONTRIBUINTE DA CPRB? S/N"` → `1/0` |

Retorna `None` para Pessoa Física (sem CNPJ).

> 🔴 Esta classe é a versão antiga. A versão melhorada está em `PdfService.parse_dados_inss()`. Use via `PdfService`.

---

### `FolhaPagamentoParser`

- `parse_relatorio_folha(fundo)` → `{"PROVENTOS": DataFrame, "DESCONTOS": DataFrame}`
  - Lê o PDF de relatório DEMOFIM, separa por fundo (RGPS/FINANCEIRO/CAPITALIZADO)
  - Colunas: `NOME NAT`, `COD NAT`, `PROVENTO` ou `DESCONTO`

- `parse_dados_provisoes(fundo)` → `dict`
  - Lê última página do PDF (Provisionamento de Férias)
  - Retorna: `{"ADICIONAL DE FÉRIAS": {"PROVISIONADO": 0.0, "REALIZADO": 0.0, "BAIXA": 0.0}, ...}`
  - Benefícios: Adicional de Férias, Abono Pecuniário, 13º Salário, Licença Prêmio

---

### `NotaEmpenhoParser.parser_diarias(caminho_pdf)` → `dict`
Extrai campos de PDFs de NE de diárias: `nune`, `credor`, `fonte`, `valor`, `natureza`, `subitem`.

> ⚠️ O método `executar()` está incompleto (`...`). Apenas `parser_diarias` funciona.

---

### `NotaLancamentoParser`
Extrai dados de NLs diretamente do SIGGO via Selenium (sem baixar PDF).
- `get_lista_nls()` → lê de planilha Excel (aba `lista_nls`, coluna `NUM_NL`)
- `parse_pagina_nl(num_nl)` → acessa URL SIGGO e extrai tabela por XPath

---

## 9. Use Cases (`core/usecases/`)

### `PagamentoUseCase` — Folha de Pagamento

| Método | O que faz |
|---|---|
| `get_dados_conferencia(fundo)` | Lê DEMOFIN, filtra por fundo, cria pivot de proventos/descontos |
| `separar_proventos(df)` | Filtra CDG_NAT começando com `"3"` |
| `separar_descontos(df)` | Filtra CDG_NAT começando com `"2"` ou `"4"` |
| `gerar_saldos(...)` | Monta `{TIPO: {COD_NAT: SALDO}}` |
| `get_saldos(fundo)` | Orquestra conferência → retorna saldos finais |
| `gerar_nl_folha(template, nome, saldos, provisoes)` | Preenche template com saldos calculados → `NotaLancamento` |
| `soma_codigos(codigos_str, dicionario)` | Soma valores de múltiplos códigos de natureza |

**Tipos de despesa**: `ATIVO`, `INATIVO`, `COMPENSATÓRIA`, `PENSIONISTA`, `ADIANTAMENTO FÉRIAS`.

---

### `ExtrairDadosR2000UseCase` — EFD-REINF

| Método | O que faz |
|---|---|
| `executar(meses)` | Itera meses, extrai INSS, gera DataFrames e exporta |
| `extrair_dados_inss(pasta_mes)` | Coleta PDFs da pasta → DataFrame |
| `gerar_dataframes_reinf(df)` | Filtra INSS retido > 0, monta R-2010-1 e R-2010-2 |
| `exportar_planilhas_r2000(df1, df2)` | Deleta linhas antigas e escreve na planilha REINF |
| `exportar_valores_pagos(meses)` | Exporta valores brutos de NFs por mês |

**CNPJ tomador fixo**: `00534560000126`

---

### `EmailsDrissUseCase` — E-mails DRISS

| Método | O que faz |
|---|---|
| `executar()` | Orquestra todo o fluxo |
| `get_pdf_por_empresa()` | Identifica empresa em cada página do PDF via regex |
| `exportar_pdfs_driss(...)` | Salva PDF individual por empresa na pasta `ENVIADOS` |
| `encontrar_emails_empresa(nome)` | Busca e-mail na planilha `EMAIL_EMPRESAS.xlsx` (aba `E-MAIL`) |
| `preparar_envio_emails_driss(...)` | Cria rascunhos no Outlook |
| `gerar_mensagem()` | HTML com saudação dinâmica (bom dia/tarde/noite) |

> ⚠️ `send=False, display=True` — e-mails são **abertos como rascunho**, não enviados.

---

### `CancelamentoRPUseCase` — Restos a Pagar

Lê aba `CANCELAMENTO_RP`, agrupa por processo/contrato/NE e monta:
- Evento `540032` (detalhes por NE)
- Evento `550923` (total da natureza)
- Evento `570569` (com fonte alterada: `1→3`, `2→4`, `7→8`)

---

### `BaixaDiariasUseCase` — Baixa de Diárias

Lê CSV da pasta `BAIXA_DIARIAS`, agrupa por processo e monta NL com:
- Evento fixo: `560379`
- CLASS. CONT fixo: `332110100`
- Observação: `"BAIXA DE ADIANTAMENTO DE VIAGENS..."`

---

## 10. Services (`infrastructure/services/`)

### `ExcelService` (openpyxl — sem Excel instalado)

| Método | O que faz |
|---|---|
| `get_sheet(nome, as_dataframe)` | Retorna aba como objeto openpyxl ou DataFrame |
| `exportar_para_planilha(df, sheet, ...)` | Escreve DataFrame com formatação (cabeçalho azul, zebra) |
| `delete_rows(sheet, start, end)` | Apaga intervalo de linhas |
| `fit_columns(sheet)` | Ajusta largura das colunas |
| `copy_to(origem, destino, nome)` | **Estático** — copia arquivo |
| `save()` | Salva o workbook |

---

### `PdfService`

| Método | O que faz |
|---|---|
| `parse_dados_inss(caminho)` | Extrai dados de demonstrativo INSS (versão com normalização de espaços) |
| `get_pdfs_driss(caminho)` | Retorna páginas do DRISS (exceto última) |
| `export_pages(pages, path)` | Cria novo PDF com páginas selecionadas |
| `get_nls_baixadas(lista_nls)` | Lê PDFs de NLs em `~/Downloads/Automático` |

---

### `SiggoService`

| Método | O que faz |
|---|---|
| `inicializar(hidden)` | Inicia driver, abre SIGGO e aguarda login |
| `esperar_login(timeout=300)` | Aguarda 5 min pelo elemento `AFC` na tela |
| `preencher_campos(dict)` | Preenche campos por XPath |
| `selecionar_opcoes(dict)` | Seleciona dropdowns por XPath |
| `download_nl(num_nl)` | Baixa PDF da NL, aguarda e renomeia para `{num_nl}.pdf` |

> ⚠️ Login é **manual** por padrão. O usuário precisa logar em até 5 minutos.

---

## 11. Gateways (`infrastructure/gateways/`)

### `PathingGateway` — Caminhos de Arquivo

Detecta automaticamente caminho base ou OneDrive:

| Método | Caminho |
|---|---|
| `get_caminho_raiz_secon()` | Raiz do SharePoint (`Tribunal de Contas...` ou `OneDrive - ...`) |
| `get_caminho_pasta_folha()` | `.../FOLHA_DE_PAGAMENTO_{ANO}/{MES}` |
| `get_caminho_conferencia(fundo)` | `.../CONFERÊNCIA_{fundo}.xlsx` |
| `get_caminho_template(tipo)` | `.../TEMPLATES/TEMPLATES_NL_{tipo}.xlsx` |
| `get_caminho_tabela_demofin()` | Busca `DEMOFIN*TABELA.xlsx` na pasta do mês |
| `get_caminho_pdf_relatorio()` | Busca PDF que começa com `"relatórios"` |
| `get_caminho_reinf(pasta_mes)` | `.../EFD-REINF/{pasta_mes}/Preenchimento Reinf.xlsx` |
| `get_caminhos_demonstrativos(pasta_mes)` | Todos os PDFs em `.../LIQ_DESPESA/{pasta_mes}` |
| `get_caminho_pdf_driss()` | `.../DRISS_{ANO}/{MES_ANT}/DRISS_{MM}_{ANO}.pdf` |
| `get_caminho_download_nl()` | `~/Downloads/Automático` |

---

### `PreenchimentoGateway` — Automação SIGGO

| Método | O que faz |
|---|---|
| `executar(dados, divisao_par)` | Abre nova aba por NL, preenche cabeçalho e linhas |
| `preparar_preechimento_cabecalho(cab)` | Mapeia `CabecalhoNL` para XPaths do formulário |
| `preparar_preenchimento_nl(dados)` | Clica "Incluir" e mapeia cada linha para XPaths |
| `separar_por_pagina(df, tamanho)` | Divide em chunks de 24 ou 25 linhas |
| `extrair_dados_preenchidos()` | Lê dados de volta de todas as abas abertas |

> ⚠️ SIGGO aceita **máx. ~25 linhas por NL**. NLs grandes são divididas automaticamente.

---

## 12. Exceções (`core/exceptions.py`)

| Exceção | Quando ocorre |
|---|---|
| `LoginSiggoError` | Credenciais inválidas ou senha expirada |
| `ConexaoSiggoError` | Conexão instável com o SIGGO |
| `SiggoIndisponivelError` | Site fora do ar ou timeout |
| `ErroPreenchimentoSiggoError` | Falha ao preencher campo |
| `PlanilhaNaoEncontradaError` | Arquivo `.xlsx` não existe |
| `PlanilhaEmUsoError` | Arquivo aberto no Excel (`PermissionError`) |
| `FormatoPlanilhaInvalidoError` | Colunas obrigatórias ausentes |
| `DadosAusentesError` | Campo obrigatório vazio |
| `PdfIllegivelError` | PDF escaneado sem OCR |
| `CaminhoRedeNaoEncontradoError` | Pasta de rede inacessível (VPN) |
| `OutlookNaoConfiguradoError` | Outlook Desktop não instalado |

---

## 13. Guia de Manutenção

### Adicionar um novo processo
1. Criar `UseCase` em `src/core/usecases/`
2. Criar método `create_X_uc()` em `src/factories.py`
3. Criar `Controller` em `src/adapters/controllers/`
4. Registrar no dict `opcoes` em `src/main.py`

### Alterar caminhos de arquivo → `pathing_gateway.py`
### Alterar campos do SIGGO → `preenchimento_gateway.py` (XPaths)
### Alterar lógica de cálculo de NLs → `pagamento_uc.py`, método `gerar_nl_folha()`

### Troubleshooting

| Problema | Causa | Solução |
|---|---|---|
| `PermissionError` ao abrir Excel | Planilha aberta no Excel | Fechar o arquivo |
| `FileNotFoundError` | Pasta/arquivo não existe | Verificar se pasta do mês existe |
| `TimeoutException` | Login não feito a tempo | Logar no SIGGO em até 5 min |
| `ValueError: Aba X não encontrada` | Nome da aba errado na planilha | Verificar nomes das abas |
| PDF retornando `None` | PDF de Pessoa Física (sem CNPJ) | Esperado — PF é ignorado |

### Dependências

| Biblioteca | Uso |
|---|---|
| `pandas` | DataFrames em todo o sistema |
| `openpyxl` | Leitura/escrita de `.xlsx` sem Excel |
| `pypdf` | Extração de texto de PDFs |
| `selenium` | Automação web do SIGGO |
| `pywin32` | Outlook/Excel via COM (Windows) |

---

*Documentação gerada em 13/05/2026*
