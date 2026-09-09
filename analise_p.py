"""Análise exploratória de preços de combustíveis (ANP - Preços Semestrais).

Fluxo:
    1. Carregar o CSV e localizar as colunas relevantes por nome (tolerando
       variações de acentuação/maiúsculas).
    2. Limpar e tipar os dados (moeda -> float, data -> datetime, texto -> string).
    3. Salvar um CSV tratado, com one-hot encoding da coluna de produto.
    4. Exibir tipos de variáveis, estatísticas descritivas, outliers e gráficos.

Uso:
    python analise_p.py [caminho_do_csv]
"""

import sys
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ARQUIVO_PADRAO = "Preços semestrais - AUTOMOTIVOS_2024.01_reduzido.csv"

# Nomes alternativos aceitos para cada coluna que o script precisa localizar,
# já que a grafia pode variar entre exportações (com/sem acento, sinônimos etc.).
COLUNAS_ESPERADAS = {
	"data_coleta": ["data da coleta", "data"],
	"produto": ["tipo de produto", "produto", "combustivel"],
	"preco": ["preco de venda", "preco", "valor de venda", "valor"],
	"valor_compra": ["valor de compra", "preco de compra"],
	"bandeira": ["bandeira", "marca"],
}


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------

def normalizar(valor) -> str:
	"""Remove acentos, baixa a caixa e tira espaços das pontas de um texto."""
	sem_acento = unicodedata.normalize("NFKD", str(valor))
	return "".join(c for c in sem_acento if not unicodedata.combining(c)).lower().strip()


def localizar_coluna(colunas, alternativas) -> str | None:
	"""Encontra, em `colunas`, o nome que corresponde a alguma alternativa
	(comparação normalizada, com correspondência exata ou por substring)."""
	alvos = [normalizar(a) for a in alternativas]
	for coluna in colunas:
		nome = normalizar(coluna)
		if nome in alvos or any(alvo in nome for alvo in alvos):
			return coluna
	return None


def localizar_colunas(colunas) -> dict[str, str | None]:
	"""Aplica `localizar_coluna` para cada campo definido em COLUNAS_ESPERADAS."""
	return {campo: localizar_coluna(colunas, alternativas)
			for campo, alternativas in COLUNAS_ESPERADAS.items()}


def moeda_para_float(serie: pd.Series) -> pd.Series:
	"""Converte uma coluna monetária em formato brasileiro (ex.: 'R$ 5,68')
	para float (5.68), preservando NaN onde não for possível converter."""
	texto = (serie.astype("string")
			 .str.replace("R$", "", regex=False)
			 .str.replace(".", "", regex=False)
			 .str.replace(",", ".", regex=False))
	return pd.to_numeric(texto, errors="coerce")


# ---------------------------------------------------------------------------
# Carga e limpeza
# ---------------------------------------------------------------------------

def obter_caminho_csv() -> Path:
	if len(sys.argv) >= 2:
		return Path(sys.argv[1])
	return Path(__file__).resolve().parent / ARQUIVO_PADRAO


def carregar_csv(caminho: Path) -> pd.DataFrame:
	if not caminho.exists():
		raise SystemExit(
			f"Arquivo não encontrado: {caminho}\n"
			"Informe o caminho do arquivo CSV: python analise_p.py dados.csv"
		)
	return pd.read_csv(caminho, sep=None, engine="python")


def limpar_texto(df: pd.DataFrame) -> pd.DataFrame:
	"""Remove espaços extras de colunas de texto e trata string vazia como ausência."""
	for coluna in df.select_dtypes(include=["object", "str"]):
		df[coluna] = df[coluna].astype("string").str.strip().replace("", pd.NA)
	return df


def tratar_dados(df: pd.DataFrame, colunas: dict) -> pd.DataFrame:
	"""Aplica as conversões de tipo (moeda, data, texto) nas colunas identificadas."""
	preco = colunas["preco"]
	if preco is None:
		raise KeyError("Coluna de preço não encontrada.")
	df[preco] = moeda_para_float(df[preco])

	valor_compra = colunas["valor_compra"]
	if valor_compra:
		df[valor_compra] = moeda_para_float(df[valor_compra])

	data_coleta = colunas["data_coleta"]
	if data_coleta:
		df[data_coleta] = pd.to_datetime(df[data_coleta], dayfirst=True, errors="coerce")

	produto = colunas["produto"]
	if produto:
		df[produto] = df[produto].astype("string").str.upper()

	return df


def remover_colunas_vazias(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
	vazias = [c for c in df.columns if df[c].isna().all()]
	return df.drop(columns=vazias), vazias


def aplicar_dummies_produto(df: pd.DataFrame, produto: str | None) -> tuple[pd.DataFrame, pd.DataFrame | None]:
	"""Cria colunas one-hot para o produto (poucos níveis, sem ordem natural)."""
	if not produto:
		return df, None
	dummies = pd.get_dummies(df[produto], prefix="produto", dtype=int)
	return pd.concat([df, dummies], axis=1), dummies


def preparar_dados(caminho_csv: Path) -> dict:
	"""Executa toda a etapa de carga + limpeza e devolve o necessário para a análise."""
	df = carregar_csv(caminho_csv)
	df = limpar_texto(df)

	colunas = localizar_colunas(df.columns)
	df = tratar_dados(df, colunas)

	dados = df.dropna(subset=[colunas["preco"]])
	dados, colunas_vazias = remover_colunas_vazias(dados)
	dados, dummies = aplicar_dummies_produto(dados, colunas["produto"])

	return {
		"dados": dados,
		"colunas": colunas,
		"colunas_vazias": colunas_vazias,
		"dummies": dummies,
	}


def salvar_dados_tratados(dados: pd.DataFrame, caminho_original: Path) -> Path:
	caminho_saida = caminho_original.with_name(f"{caminho_original.stem}_tratado_com_dummies.csv")
	dados.to_csv(caminho_saida, index=False, sep=";")
	return caminho_saida


# ---------------------------------------------------------------------------
# Relatórios em texto
# ---------------------------------------------------------------------------

def classificar_tipo(serie: pd.Series) -> str:
	if pd.api.types.is_datetime64_any_dtype(serie):
		return "temporal"
	return "quantitativa" if pd.api.types.is_numeric_dtype(serie) else "qualitativa"


def imprimir_tipos_variaveis(dados: pd.DataFrame) -> None:
	print("Tipos de variáveis:")
	for coluna in dados.columns:
		print(f"{coluna}: {classificar_tipo(dados[coluna])}")


def calcular_resumo_preco(dados: pd.DataFrame, preco: str, produto: str | None) -> pd.DataFrame | pd.Series:
	if produto:
		return dados.groupby(produto)[preco].agg(
			media="mean", mediana="median", desvio_padrao="std", variancia="var"
		).round(2)
	return dados[preco].agg(["mean", "median", "std", "var"]).round(2)


def detectar_outliers(dados: pd.DataFrame, preco: str, produto: str | None) -> pd.DataFrame:
	"""Detecta outliers pelo critério do IQR (1,5x).

	Quando `produto` está disponível, o IQR é calculado por grupo de produto
	em vez de sobre a base inteira — isso evita, por exemplo, tratar preços
	normais de etanol (~R$ 3,71) como outliers só por estarem distantes da
	faixa de preço do diesel (~R$ 6,01)."""
	if produto:
		agrupado = dados.groupby(produto)[preco]
		q1 = agrupado.transform(lambda serie: serie.quantile(0.25))
		q3 = agrupado.transform(lambda serie: serie.quantile(0.75))
	else:
		q1 = dados[preco].quantile(0.25)
		q3 = dados[preco].quantile(0.75)

	limite = 1.5 * (q3 - q1)
	return dados[(dados[preco] < q1 - limite) | (dados[preco] > q3 + limite)]


def calcular_medias_por_bandeira(dados: pd.DataFrame, preco: str, bandeira: str) -> pd.Series:
	return dados.groupby(bandeira)[preco].mean().sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def plotar_boxplot_e_histograma(dados: pd.DataFrame, preco: str, produto: str | None) -> None:
	sns.set_theme(style="whitegrid")
	fig, (eixo_box, eixo_hist) = plt.subplots(1, 2, figsize=(14, 5))

	if produto:
		sns.boxplot(data=dados, x=produto, y=preco, ax=eixo_box)
	else:
		sns.boxplot(y=dados[preco], ax=eixo_box)
	eixo_box.set_title("Boxplot dos preços")

	sns.histplot(dados[preco], bins=30, kde=True, ax=eixo_hist)
	eixo_hist.set_title("Histograma dos preços de combustíveis")

	plt.tight_layout()
	Path("imagens").mkdir(parents=True, exist_ok=True)
	plt.savefig("imagens/boxplot_precos.png", dpi=300, bbox_inches="tight")
	plt.show()


def plotar_medias_por_bandeira(medias: pd.Series) -> None:
	medias.plot.bar(title="Preço médio por bandeira", ylabel="Preço médio", figsize=(9, 5))
	plt.xticks(rotation=45, ha="right")
	plt.tight_layout()
	Path("imagens").mkdir(parents=True, exist_ok=True)
	plt.savefig("imagens/medias_por_bandeira.png", dpi=300, bbox_inches="tight")
	plt.show()


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------

def main() -> None:
	caminho_csv = obter_caminho_csv()
	preparado = preparar_dados(caminho_csv)

	dados = preparado["dados"]
	colunas = preparado["colunas"]
	preco, produto, bandeira = colunas["preco"], colunas["produto"], colunas["bandeira"]

	caminho_tratado = salvar_dados_tratados(dados, caminho_csv)

	print(f"Arquivo carregado: {caminho_csv}")
	print(f"Arquivo tratado salvo em: {caminho_tratado}")
	print(f"Linhas: {len(dados)} | Colunas após limpeza: {len(dados.columns)}")
	if preparado["colunas_vazias"]:
		print(f"Colunas removidas por estarem totalmente vazias: {', '.join(preparado['colunas_vazias'])}")
	if preparado["dummies"] is not None:
		print(f"Colunas dummy criadas: {', '.join(preparado['dummies'].columns)}")

	imprimir_tipos_variaveis(dados)

	print("\nEstatísticas do preço por tipo de produto:")
	print(calcular_resumo_preco(dados, preco, produto))

	outliers = detectar_outliers(dados, preco, produto)
	print(f"\nOutliers detectados: {len(outliers)}")
	print(outliers[[preco]].head(20))

	plotar_boxplot_e_histograma(dados, preco, produto)

	if bandeira:
		medias = calcular_medias_por_bandeira(dados, preco, bandeira)
		print("\nPreço médio por bandeira:")
		print(medias.round(2))
		plotar_medias_por_bandeira(medias)


if __name__ == "__main__":
	main()