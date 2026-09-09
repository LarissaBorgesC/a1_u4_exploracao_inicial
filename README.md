# Análise de Preços de Combustíveis (ANP - Preços Semestrais)

Script em Python para limpeza e análise exploratória de dados de preços de
combustíveis automotivos (padrão dos arquivos de "Preços Semestrais" da ANP).

O script identifica as colunas relevantes automaticamente (mesmo com pequenas
variações de nome/acentuação), converte valores monetários e datas, remove
colunas totalmente vazias, gera uma versão tratada do CSV (com one-hot
encoding do produto) e produz um relatório com estatísticas descritivas,
detecção de outliers e gráficos salvos em disco.

## Estrutura do projeto

```
.
├── analise_p.py                              # script principal
├── requirements.txt                          # dependências do projeto
├── README.md
├── Preços semestrais - AUTOMOTIVOS_2024.01_reduzido.csv   # arquivo de entrada (exemplo)
└── imagens/                                  # gerada automaticamente pelo script
    ├── boxplot_precos.png
    └── medias_por_bandeira.png
```

## O que o script faz

1. **Carrega** o CSV informado (detecta automaticamente o separador `,` ou `;`).
2. **Limpa** os dados:
   - Remove espaços extras de colunas de texto e trata string vazia como valor ausente.
   - Converte a coluna de preço (e de valor de compra, se existir) do formato
     monetário brasileiro (`"R$ 5,68"`) para `float` (`5.68`).
   - Converte a coluna de data para `datetime`.
   - Remove colunas 100% vazias.
3. **Enriquece** os dados com colunas *dummy* (one-hot encoding) a partir da
   coluna de produto.
4. **Salva** o resultado tratado em um novo CSV: `<nome_original>_tratado_com_dummies.csv`.
5. **Exibe no terminal**:
   - Classificação de cada coluna (qualitativa, quantitativa ou temporal).
   - Estatísticas descritivas do preço (média, mediana, desvio-padrão, variância) por tipo de produto.
   - Registros identificados como outliers (regra do IQR calculado **por produto**, veja "Observações").
   - Preço médio por bandeira.
6. **Gera e salva gráficos** (via `matplotlib`/`seaborn`), em janela interativa e em arquivo `.png` dentro da pasta `imagens/`:
   - Boxplot dos preços por tipo de produto + histograma da distribuição geral dos preços (`imagens/boxplot_precos.png`).
   - Gráfico de barras do preço médio por bandeira (`imagens/medias_por_bandeira.png`).

## Requisitos

- Python 3.10+
- Dependências listadas em [`requirements.txt`](requirements.txt): `pandas`, `matplotlib`, `seaborn`.

Instalação recomendada (idealmente dentro de um ambiente virtual):

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Se preferir instalar sem o arquivo:

```bash
pip install pandas matplotlib seaborn
```

## Como usar

```bash
python analise_p.py [caminho_do_csv]
```

- Se `caminho_do_csv` não for informado, o script procura por um arquivo chamado
  `Preços semestrais - AUTOMOTIVOS_2024.01_reduzido.csv` na mesma pasta do script.
- Se o arquivo não for encontrado, o script encerra com uma mensagem explicativa.

Exemplo:

```bash
python analise_p.py "dados/Preços semestrais - AUTOMOTIVOS_2024.01.csv"
```

## Colunas esperadas no CSV

O script localiza as colunas pelo nome, tolerando variações de acentuação,
maiúsculas/minúsculas e pequenos sinônimos. Não é necessário que os nomes
sejam exatamente iguais aos listados abaixo — apenas conter uma das
alternativas.

| Campo interno | Alternativas de nome aceitas | Obrigatório |
|---|---|---|
| `preco` | "preço de venda", "preço", "valor de venda", "valor" | **Sim** |
| `produto` | "tipo de produto", "produto", "combustível" | Não |
| `bandeira` | "bandeira", "marca" | Não |
| `data_coleta` | "data da coleta", "data" | Não |
| `valor_compra` | "valor de compra", "preço de compra" | Não |

Se a coluna de preço não for encontrada, o script interrompe a execução com
um erro (`KeyError: Coluna de preço não encontrada.`).

Colunas ausentes (como `bandeira` ou `produto`) não quebram o script — as
etapas que dependem delas são simplesmente puladas. Sem a coluna `produto`,
por exemplo, o IQR dos outliers volta a ser calculado sobre a base inteira
(veja "Observações").

## Saídas geradas

- **CSV tratado**: `<nome_original>_tratado_com_dummies.csv`, salvo na mesma
  pasta do arquivo de entrada, separado por `;`.
- **Gráficos**: exibidos em janelas interativas (`plt.show()`) **e** salvos
  em disco na pasta `imagens/` (criada automaticamente se não existir),
  em 300 dpi:
  - `imagens/boxplot_precos.png`
  - `imagens/medias_por_bandeira.png`

## Estrutura do código

O script é organizado em funções por responsabilidade, sem estado global além
do fluxo em `main()`:

- **Texto**: `normalizar`, `localizar_coluna`, `localizar_colunas`, `moeda_para_float`
- **Carga e limpeza**: `obter_caminho_csv`, `carregar_csv`, `limpar_texto`,
  `tratar_dados`, `remover_colunas_vazias`, `aplicar_dummies_produto`,
  `preparar_dados`, `salvar_dados_tratados`
- **Relatórios em texto**: `classificar_tipo`, `imprimir_tipos_variaveis`,
  `calcular_resumo_preco`, `detectar_outliers`, `calcular_medias_por_bandeira`
- **Gráficos**: `plotar_boxplot_e_histograma`, `plotar_medias_por_bandeira`
- **Orquestração**: `main()`

## Observações

- A detecção de outliers usa o critério clássico do intervalo interquartil
  (IQR): valores abaixo de `Q1 - 1,5×IQR` ou acima de `Q3 + 1,5×IQR`. Quando a
  coluna `produto` é encontrada, o Q1/Q3 é calculado **por produto**
  (`groupby(produto)`), evitando que a diferença natural de faixa de preço
  entre combustíveis (ex.: etanol ~R$ 3,71 vs. diesel ~R$ 6,01) gere falsos
  outliers. Sem a coluna `produto`, o cálculo cai para o IQR global da base.
- A coluna de produto é convertida para caixa alta antes do one-hot encoding,
  para evitar categorias duplicadas por diferença de capitalização.