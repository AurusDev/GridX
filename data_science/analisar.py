# analisar.py
# Classe DataAnalyzer para análises exploratórias
# Requer: pandas, numpy, matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class DataAnalyzer:
    def __init__(self, log_fn):
        """
        log_fn: função que recebe uma string para registrar no painel de log
        """
        self.log = log_fn

    # ---------- TEXTOS ----------
    def dataset_info(self, df: pd.DataFrame):
        self.log("📦 Informações do Dataset:")
        self.log(f" - Formato: {df.shape[0]} linhas x {df.shape[1]} colunas")
        nmiss = df.isna().sum().sum()
        self.log(f" - Valores ausentes (total): {int(nmiss)}")
        self.log(f" - Tipos:\n{df.dtypes.to_string()}")

    def summary(self, df: pd.DataFrame):
        self.dataset_info(df)
        self.log("\n📊 Estatísticas descritivas (numéricas):")
        desc_num = df.describe(include=[np.number]).transpose()
        if not desc_num.empty:
            self.log(desc_num.to_string())
        else:
            self.log(" - Não há colunas numéricas.")

        self.log("\n📋 Estatísticas (categóricas):")
        desc_cat = df.describe(include=["object", "string"]).transpose()
        if not desc_cat.empty:
            self.log(desc_cat.to_string())
        else:
            self.log(" - Não há colunas categóricas.")

    def profile_columns(self, df: pd.DataFrame, cols):
        for col in cols:
            if col not in df.columns:
                self.log(f"⚠ Coluna '{col}' não encontrada.")
                continue
            s = df[col]
            self.log(f"\n🔎 Coluna: {col}")
            self.log(f" - Tipo: {s.dtype}")
            self.log(f" - Nulos: {int(s.isna().sum())} ({s.isna().mean():.1%})")
            self.log(f" - Valores únicos: {s.nunique(dropna=True)}")

            if pd.api.types.is_numeric_dtype(s):
                self.log(" - Estatísticas numéricas:")
                self.log(s.describe().to_string())
            else:
                vc = s.astype("string").value_counts(dropna=True).head(10)
                if not vc.empty:
                    self.log(" - Top categorias:")
                    self.log(vc.to_string())
                else:
                    self.log(" - Sem categorias não nulas para exibir.")

    # ---------- GRÁFICOS ----------
    def plot_column(self, df: pd.DataFrame, col: str):
        if col not in df.columns:
            self.log(f"⚠ Coluna '{col}' não encontrada.")
            return
        s = df[col].dropna()
        if s.empty:
            self.log(f"⚠ Coluna '{col}' só contém nulos.")
            return

        plt.figure()
        if pd.api.types.is_numeric_dtype(s):
            s.plot(kind="hist", bins=20)
            plt.title(f"Distribuição — {col}")
            plt.xlabel(col)
            plt.ylabel("Frequência")
        else:
            s.astype("string").value_counts().head(20).plot(kind="bar")
            plt.title(f"Top categorias — {col}")
            plt.xlabel("Categoria")
            plt.ylabel("Contagem")
        plt.tight_layout()
        plt.show()
        self.log(f"📈 Gráfico exibido para a coluna: {col}")

    def plot_correlation(self, df: pd.DataFrame):
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] < 2:
            self.log("⚠ Poucas colunas numéricas para correlação.")
            return
        corr = num_df.corr(numeric_only=True)
        self.log("\n🔗 Correlação (pearson):")
        self.log(corr.to_string())

        plt.figure()
        plt.imshow(corr, cmap="coolwarm", interpolation="nearest")
        plt.title("Matriz de Correlação")
        plt.colorbar()
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
        plt.yticks(range(len(corr.columns)), corr.columns)
        plt.tight_layout()
        plt.show()
        self.log("📈 Heatmap de correlação exibido.")

    def plot_missing(self, df: pd.DataFrame):
        miss = df.isna().sum()
        self.log("\n🕳️ Missing por coluna:")
        self.log(miss.to_string())

        plt.figure()
        miss.plot(kind="bar")
        plt.title("Valores ausentes por coluna")
        plt.ylabel("Qtde de nulos")
        plt.tight_layout()
        plt.show()
        self.log("📈 Gráfico de missing exibido.")

    def detect_duplicates(self, df: pd.DataFrame):
        dups = df.duplicated()
        n = int(dups.sum())
        self.log(f"\n🔁 Linhas duplicadas: {n}")
        if n > 0:
            self.log("Exemplo (primeiras linhas duplicadas):")
            self.log(df[dups].head(5).to_string(index=False))

    def detect_outliers_iqr(self, df: pd.DataFrame):
        num_df = df.select_dtypes(include=[np.number])
        if num_df.empty:
            self.log("⚠ Não há colunas numéricas para outliers.")
            return

        self.log("\n🚨 Outliers por IQR:")
        found_any = False
        for col in num_df.columns:
            s = num_df[col].dropna()
            if s.empty:
                continue
            q1, q3 = np.percentile(s, [25, 75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            n = int(mask.sum())
            if n > 0:
                found_any = True
                self.log(f" - {col}: {n} outliers")
                self.log(df.loc[mask, [col]].head(5).to_string(index=False))

                plt.figure()
                plt.boxplot(s.dropna(), vert=True)
                plt.title(f"Boxplot — {col}")
                plt.ylabel(col)
                plt.tight_layout()
                plt.show()
        if not found_any:
            self.log(" - Nenhum outlier detectado (IQR).")

    def plot_time_series(self, df: pd.DataFrame):
        dt_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        if not dt_cols or not num_cols:
            self.log("⚠ Para série temporal, preciso de 1 coluna datetime e 1 numérica.")
            return
        dt = dt_cols[0]
        num = num_cols[0]
        s = df[[dt, num]].dropna().sort_values(dt)
        if s.empty:
            self.log("⚠ Dados insuficientes para série temporal.")
            return

        plt.figure()
        plt.plot(s[dt], s[num])
        plt.title(f"Série Temporal — {num} por {dt}")
        plt.xlabel(dt)
        plt.ylabel(num)
        plt.tight_layout()
        plt.show()
        self.log(f"📈 Série temporal exibida ({num} vs {dt}).")
