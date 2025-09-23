# app.py (versão ajustada)

import os
import sys
import math
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from analisar import DataAnalyzer


def strip_tz_inplace(df: pd.DataFrame):
    for col in df.columns:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

def safe_to_excel(df: pd.DataFrame, path: str):
    tmp = df.copy()
    strip_tz_inplace(tmp)
    tmp.to_excel(path, index=False)

def safe_to_csv(df: pd.DataFrame, path: str):
    tmp = df.copy()
    strip_tz_inplace(tmp)
    tmp.to_csv(path, index=False, encoding="utf-8-sig")

def auto_cast_series(s: pd.Series) -> pd.Series:
    if pd.api.types.is_object_dtype(s):
        s_dt = pd.to_datetime(s, errors="coerce", utc=False, infer_datetime_format=True)
        if s_dt.notna().sum() > 0 and (s_dt.notna().mean() > 0.6):
            return s_dt
        s_num = pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")
        if s_num.notna().sum() > 0 and (s_num.notna().mean() > 0.6):
            return s_num
        return s.astype("string")
    return s


class GridXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.title("🧰 GridX — Editor & Analizador de Planilhas")
        self.geometry("1280x720")

        self.df = None
        self.filepath = None
        self.sheets = []
        self.current_sheet = None
        self.analyzer = DataAnalyzer(self.log)

        self._build_ui()

    def _build_ui(self):
        # ---------------- TOPO ----------------
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=8, pady=6)

        ctk.CTkButton(top, text="📂 Carregar", command=self.on_load).pack(side="left", padx=4)
        ctk.CTkButton(top, text="💾 Salvar", command=self.on_save).pack(side="left", padx=4)
        ctk.CTkButton(top, text="🧹 Limpar Log", command=self.clear_log).pack(side="left", padx=4)
        ctk.CTkButton(top, text="🔄 Descarregar", command=self.on_reset).pack(side="left", padx=4)

        ctk.CTkLabel(top, text="Aba:").pack(side="left", padx=(16, 4))
        self.sheet_combo = ctk.CTkComboBox(top, values=[], command=self.on_select_sheet, width=240)
        self.sheet_combo.pack(side="left", padx=4)

        # ---------------- PAINEL PRINCIPAL ----------------
        main_paned = ttk.Panedwindow(self, orient="vertical")
        main_paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Parte de cima (colunas + dados)
        top_frame = ttk.Panedwindow(main_paned, orient="horizontal")
        main_paned.add(top_frame, weight=4)

        # Lateral esquerda (colunas + botões)
        left = ctk.CTkFrame(top_frame, width=260)
        left.pack_propagate(False)
        top_frame.add(left, weight=1)

        ctk.CTkLabel(left, text="📑 Colunas (multiseleção)").pack(pady=(6, 4))
        self.columns_list = tk.Listbox(left, selectmode="extended", exportselection=False)
        self.columns_list.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        # Botões originais
        ctk.CTkButton(left, text="➕ Adicionar Coluna", command=self.add_column).pack(fill="x", padx=6, pady=2)
        ctk.CTkButton(left, text="✏️ Renomear Coluna(s)", command=self.rename_columns).pack(fill="x", padx=6, pady=2)
        ctk.CTkButton(left, text="🗑️ Deletar Coluna(s)", command=self.delete_columns).pack(fill="x", padx=6, pady=2)
        ctk.CTkButton(left, text="🔀 Alterar Tipo", command=self.change_dtype).pack(fill="x", padx=6, pady=2)
        ctk.CTkButton(left, text="📈 Analisar", command=self.open_analysis_menu).pack(fill="x", padx=6, pady=(10, 8))

        # Centro (Treeview com dados)
        center = ctk.CTkFrame(top_frame)
        top_frame.add(center, weight=4)

        self.tree = ttk.Treeview(center, show="headings")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        # Parte de baixo (log aumentável)
        bottom = ctk.CTkFrame(main_paned)
        main_paned.add(bottom, weight=1)

        ctk.CTkLabel(bottom, text="📝 Log").pack(anchor="w", padx=6)
        self.log_text = tk.Text(bottom, height=8, bg="#111", fg="#ddd")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

    # --------- FUNÇÕES AUXILIARES ----------
    def log(self, msg: str):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self.log("🧹 Log limpo.")

    def _refresh_columns_list(self):
        self.columns_list.delete(0, "end")
        if self.df is not None:
            for col in self.df.columns:
                self.columns_list.insert("end", f"{col} — {self.df[col].dtype}")

    def _rebuild_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.tree["columns"] = []
        if self.df is None or self.df.empty:
            return
        self.tree["columns"] = list(self.df.columns)
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        for _, row in self.df.head(200).iterrows():
            self.tree.insert("", "end", values=list(row))

    # --------- BOTÕES ORIGINAIS ----------
    def add_column(self):
        if self.df is not None:
            self.df["NovaColuna"] = np.nan
            self._refresh_columns_list()
            self._rebuild_tree()
            self.log("➕ Coluna adicionada.")

    def rename_columns(self):
        sel = self.columns_list.curselection()
        if not sel:
            return
        new_name = simple_input("Novo nome da coluna:")
        if new_name:
            col_index = sel[0]
            old_name = self.df.columns[col_index]
            self.df.rename(columns={old_name: new_name}, inplace=True)
            self._refresh_columns_list()
            self._rebuild_tree()
            self.log(f"✏️ Coluna renomeada: {old_name} → {new_name}")

    def delete_columns(self):
        sel = self.columns_list.curselection()
        if not sel:
            return
        cols_to_delete = [self.df.columns[i] for i in sel]
        self.df.drop(columns=cols_to_delete, inplace=True)
        self._refresh_columns_list()
        self._rebuild_tree()
        self.log(f"🗑️ Colunas deletadas: {cols_to_delete}")

    def change_dtype(self):
        sel = self.columns_list.curselection()
        if not sel:
            return
        col = self.df.columns[sel[0]]
        try:
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
            self._refresh_columns_list()
            self.log(f"🔀 Tipo de coluna alterado: {col} → numérico")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # --------- ANÁLISE ----------
    def open_analysis_menu(self):
        if self.df is None:
            messagebox.showinfo("Info", "Carregue um arquivo primeiro.")
            return
        win = ctk.CTkToplevel(self)
        win.title("📈 Análises")
        win.geometry("380x420")
        win.grab_set()
        win.focus_force()
        win.lift()

        ctk.CTkLabel(win, text="Escolha uma análise").pack(pady=(10, 6))
        ctk.CTkButton(win, text="Resumo Geral", command=lambda: self.analyzer.summary(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Correlação", command=lambda: self.analyzer.plot_correlation(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Missing", command=lambda: self.analyzer.plot_missing(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Duplicados", command=lambda: self.analyzer.detect_duplicates(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Outliers", command=lambda: self.analyzer.detect_outliers_iqr(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Série temporal", command=lambda: self.analyzer.plot_time_series(self.df)).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(win, text="Fechar", fg_color="#333", command=win.destroy).pack(pady=10)

    # --------- CARREGAR/SALVAR ----------
    def on_load(self):
        path = filedialog.askopenfilename(
            title="Selecione a planilha",
            filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Arquivos CSV", "*.csv")]
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
                self.sheets = ["__csv__"]
            else:
                xls = pd.ExcelFile(path)
                self.sheets = xls.sheet_names
                df = pd.read_excel(path, sheet_name=self.sheets[0])

            df = df.apply(auto_cast_series)
            self.filepath = path
            self.df = df
            self.current_sheet = self.sheets[0]

            self.sheet_combo.configure(values=self.sheets)
            self.sheet_combo.set(self.current_sheet)

            self._refresh_columns_list()
            self._rebuild_tree()
            self.clear_log()
            self.log("✔ Arquivo carregado.")
            self.log(f"Aba(s) encontrada(s): {self.sheets}")
        except Exception as e:
            messagebox.showerror("Erro ao carregar", str(e))

    def on_select_sheet(self, value):
        if not self.filepath or value == "__csv__":
            return
        try:
            self.current_sheet = value
            df = pd.read_excel(self.filepath, sheet_name=value)
            df = df.apply(auto_cast_series)
            self.df = df

            self._refresh_columns_list()
            self._rebuild_tree()
            self.log(f"✔ Aba '{value}' carregada.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao trocar de aba: {e}")

    def on_save(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Nenhum dataframe para salvar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                safe_to_csv(self.df, path)
            else:
                safe_to_excel(self.df, path)
            self.log(f"💾 Arquivo salvo em: {path}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def on_reset(self):
        self.df = None
        self.filepath = None
        self.sheets = []
        self.current_sheet = None
        self.sheet_combo.configure(values=[])
        self.sheet_combo.set("")
        self.columns_list.delete(0, "end")
        self._rebuild_tree()
        self.clear_log()
        self.log("🔄 Aplicação descarregada.")


# Helper simples para input
def simple_input(prompt):
    top = tk.Toplevel()
    top.title("Input")
    tk.Label(top, text=prompt).pack(padx=10, pady=10)
    entry = tk.Entry(top)
    entry.pack(padx=10, pady=10)
    entry.focus_set()
    value = {}

    def confirm():
        value["text"] = entry.get()
        top.destroy()

    tk.Button(top, text="OK", command=confirm).pack(pady=10)
    top.wait_window()
    return value.get("text")


if __name__ == "__main__":
    app = GridXApp()
    app.mainloop()
