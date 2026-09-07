# Análise de Preços de Combustíveis (ANP - Preços Semestrais)

Script em Python para limpeza e análise exploratória de dados de preços de
combustíveis automotivos (padrão dos arquivos de "Preços Semestrais" da ANP).

O script identifica as colunas relevantes automaticamente (mesmo com pequenas
variações de nome/acentuação), converte valores monetários e datas, remove
colunas totalmente vazias, gera uma versão tratada do CSV (com one-hot
encoding do produto) e produz um relatório com estatísticas descritivas,
detecção de outliers e gráficos.

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
   - Registros identificados como outliers (regra do IQR: 1,5×IQR).
   - Preço médio por bandeira.
6. **Gera gráficos** (via `matplotlib`/`seaborn`):
   - Boxplot dos preços por tipo de produto.
   - Histograma da distribuição geral dos preços.
   - Gráfico de barras do preço médio por bandeira.

## Requisitos

- Python 3.10+
- Dependências:
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
etapas que dependem delas são simplesmente puladas.

## Saídas geradas

- **CSV tratado**: `<nome_original>_tratado_com_dummies.csv`, salvo na mesma
  pasta do arquivo de entrada, separado por `;`.
- **Gráficos**: exibidos em janelas interativas (`plt.show()`); nada é salvo
  em disco automaticamente.

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
  (IQR): valores abaixo de `Q1 - 1,5×IQR` ou acima de `Q3 + 1,5×IQR` sobre
  **todo** o conjunto de preços (não é calculada separadamente por produto).
- A coluna de produto é convertida para caixa alta antes do one-hot encoding,
  para evitar categorias duplicadas por diferença de capitalização.