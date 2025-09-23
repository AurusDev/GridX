import pandas as pd
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, END, Listbox, MULTIPLE, ttk, PanedWindow

# ------------------------------------------------------------
# Estado global
# ------------------------------------------------------------
df: pd.DataFrame | None = None
excel_file: pd.ExcelFile | None = None

# ------------------------------------------------------------
# Aparência
# ------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("📊 Editor & Analisador de Planilhas — CustomTkinter")
app.geometry("1400x850")

# ------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------
def log(msg: str):
    log_box.insert(END, msg + "\n")
    log_box.see(END)

def refresh_columns_listbox():
    columns_listbox.delete(0, END)
    if df is None:
        return
    for col in df.columns:
        dtype = str(df[col].dtype)
        columns_listbox.insert(END, f"{col} — {dtype}")

def selected_column_names():
    if df is None:
        return []
    indices = list(columns_listbox.curselection())
    names = []
    for i in indices:
        item = columns_listbox.get(i)
        name = item.split(" — ")[0]
        names.append(name)
    return names

def update_preview(dataframe: pd.DataFrame):
    """Atualiza o grid de preview com conteúdo do DataFrame"""
    for item in preview_table.get_children():
        preview_table.delete(item)
    preview_table["columns"] = list(dataframe.columns)
    preview_table["show"] = "headings"

    for col in dataframe.columns:
        preview_table.heading(col, text=col)
        preview_table.column(col, width=120, anchor="center")

    for _, row in dataframe.head(100).iterrows():
        preview_table.insert("", "end", values=list(row))

    # Atualiza rodapé
    update_footer(dataframe)

def update_footer(dataframe: pd.DataFrame | None):
    """Atualiza contador de linhas, colunas e nulos"""
    if dataframe is None:
        shape_label.configure(text="Linhas: 0 | Colunas: 0 | Nulos: 0")
    else:
        nulos = int(dataframe.isna().sum().sum())
        shape_label.configure(
            text=f"Linhas: {dataframe.shape[0]} | Colunas: {dataframe.shape[1]} | Nulos: {nulos}"
        )

# ------------------------------------------------------------
# Tipagem automática
# ------------------------------------------------------------
def _try_numeric(col: pd.Series) -> pd.Series:
    return pd.to_numeric(col, errors="ignore")

def _try_datetime(col: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(col):
        return col
    return pd.to_datetime(col, errors="ignore", infer_datetime_format=True)

def auto_infer_types(df_in: pd.DataFrame) -> pd.DataFrame:
    out = df_in.copy()
    for c in out.columns:
        original = out[c].dtype
        tmp = _try_numeric(out[c])
        tmp2 = _try_datetime(tmp)
        out[c] = tmp2
        new = out[c].dtype
        if new != original:
            log(f"🔎 '{c}' convertido de {original} → {new}")
    return out

# ------------------------------------------------------------
# Excel-safe helper
# ------------------------------------------------------------
def make_excel_safe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_dtype(out[col]) or pd.api.types.is_datetime64tz_dtype(out[col]):
            try:
                out[col] = out[col].dt.tz_localize(None)
            except Exception:
                out[col] = pd.to_datetime(out[col], errors="coerce").dt.tz_localize(None)
    return out

# ------------------------------------------------------------
# Ações principais
# ------------------------------------------------------------
def carregar_arquivo():
    global excel_file, df
    path = filedialog.askopenfilename(
        title="Selecione a planilha",
        filetypes=[("Excel", "*.xlsx *.xls"), ("CSV", "*.csv")]
    )
    if not path:
        return
    try:
        if path.lower().endswith(".csv"):
            df = pd.read_csv(path)
            excel_file = None
            df = auto_infer_types(df)
            update_preview(df)
            refresh_columns_listbox()
            log("✅ Arquivo CSV carregado com sucesso!")
        else:
            excel_file = pd.ExcelFile(path)
            sheet_combo.configure(values=excel_file.sheet_names)
            sheet_combo.set(excel_file.sheet_names[0])
            carregar_aba(excel_file.sheet_names[0])
            log(f"✅ Arquivo Excel carregado. Abas encontradas: {excel_file.sheet_names}")
    except Exception as e:
        messagebox.showerror("Erro ao carregar", str(e))

def carregar_aba(sheet_name):
    global df
    if excel_file is None:
        return
    df = excel_file.parse(sheet_name)
    df = auto_infer_types(df)
    refresh_columns_listbox()
    update_preview(df)
    log(f"📄 Aba '{sheet_name}' carregada com sucesso!")

def salvar_arquivo():
    if df is None:
        messagebox.showwarning("Aviso", "Nenhum arquivo para salvar!")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
    )
    if not path:
        return
    try:
        df_to_save = make_excel_safe(df)
        if path.lower().endswith(".csv"):
            df_to_save.to_csv(path, index=False)
        else:
            df_to_save.to_excel(path, index=False)
        log(f"💾 Arquivo salvo em: {path}")
        messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro ao salvar", str(e))

# ------------------------------------------------------------
# Funções de edição
# ------------------------------------------------------------
def adicionar_coluna():
    global df
    if df is None:
        return
    nome = simpledialog.askstring("Adicionar coluna", "Nome da nova coluna:")
    if not nome:
        return
    if nome in df.columns:
        messagebox.showwarning("Aviso", "Já existe uma coluna com esse nome.")
        return
    default_value = simpledialog.askstring("Valor padrão (opcional)", "Deixe em branco para NaN:")
    df[nome] = default_value if (default_value not in [None, ""]) else pd.NA
    log(f"➕ Coluna adicionada: '{nome}'")
    refresh_columns_listbox()
    update_preview(df)

def deletar_colunas():
    global df
    if df is None:
        return
    cols = selected_column_names()
    if not cols:
        return
    df.drop(columns=cols, inplace=True)
    log(f"🗑️ Colunas deletadas: {', '.join(cols)}")
    refresh_columns_listbox()
    update_preview(df)

def renomear_colunas():
    global df
    if df is None:
        return
    cols = selected_column_names()
    if not cols:
        return
    mapping = {}
    for c in cols:
        novo = simpledialog.askstring("Renomear", f"Novo nome para '{c}':")
        if not novo:
            continue
        mapping[c] = novo
    if mapping:
        df.rename(columns=mapping, inplace=True)
        log(f"✏️ Renomeadas: {mapping}")
        refresh_columns_listbox()
        update_preview(df)

def alterar_tipo_colunas():
    global df
    if df is None:
        return
    cols = selected_column_names()
    if not cols:
        return
    tipo = simpledialog.askstring("Alterar tipo", "Digite o tipo (string, int, float, datetime, bool):")
    ok, fail = [], []
    for c in cols:
        try:
            if tipo == "string":
                df[c] = df[c].astype("string")
            elif tipo == "int":
                df[c] = pd.to_numeric(df[c], errors="raise").astype("Int64")
            elif tipo == "float":
                df[c] = pd.to_numeric(df[c], errors="raise").astype("Float64")
            elif tipo == "datetime":
                df[c] = pd.to_datetime(df[c], errors="raise", infer_datetime_format=True).dt.tz_localize(None)
            elif tipo == "bool":
                df[c] = df[c].astype("string").str.strip().str.lower().map(
                    {"true": True, "false": False, "1": True, "0": False, "sim": True, "não": False, "nao": False}
                )
            ok.append(c)
        except Exception as e:
            fail.append(f"{c} ({e})")
    if ok:
        log(f"🔁 Tipo aplicado '{tipo}' em: {', '.join(ok)}")
    if fail:
        log(f"⚠️ Falha em: {', '.join(fail)}")
    refresh_columns_listbox()
    update_preview(df)

def resetar_log():
    global df, excel_file
    log_box.delete("1.0", END)
    df = None
    excel_file = None

    # Limpa listbox
    columns_listbox.delete(0, END)

    # Limpa grid
    for item in preview_table.get_children():
        preview_table.delete(item)
    preview_table["columns"] = []

    # Reseta ComboBox
    sheet_combo.set("")
    sheet_combo.configure(values=[])

    # Reset rodapé
    update_footer(None)

    log("🧹 Reset: aplicação limpa.")

# ------------------------------------------------------------
# Layout
# ------------------------------------------------------------
top_frame = ctk.CTkFrame(app)
top_frame.pack(fill="x", padx=16, pady=12)

btn_load = ctk.CTkButton(top_frame, text="📂 Carregar", command=carregar_arquivo)
btn_save = ctk.CTkButton(top_frame, text="💾 Salvar", command=salvar_arquivo)
btn_reset = ctk.CTkButton(top_frame, text="🧹 Limpar Log", command=resetar_log)

btn_load.pack(side="left", padx=6)
btn_save.pack(side="left", padx=6)
btn_reset.pack(side="left", padx=6)

sheet_combo = ctk.CTkComboBox(top_frame, values=[], command=carregar_aba)
sheet_combo.pack(side="left", padx=6)

body = ctk.CTkFrame(app)
body.pack(fill="both", expand=True, padx=16, pady=8)

# Lado esquerdo: listbox
left = ctk.CTkFrame(body)
left.pack(side="left", fill="y", padx=(0,12), pady=4)

ctk.CTkLabel(left, text="📋 Colunas (multiseleção)").pack(padx=8, pady=(8,4))
columns_listbox = Listbox(left, selectmode=MULTIPLE, width=38, height=18)
columns_listbox.pack(padx=8, pady=4)

btn_add = ctk.CTkButton(left, text="➕ Adicionar Coluna", command=adicionar_coluna)
btn_rename = ctk.CTkButton(left, text="✏️ Renomear Coluna(s)", command=renomear_colunas)
btn_delete = ctk.CTkButton(left, text="🗑️ Deletar Coluna(s)", command=deletar_colunas)
btn_type = ctk.CTkButton(left, text="🧬 Alterar Tipo", command=alterar_tipo_colunas)

btn_add.pack(fill="x", padx=8, pady=6)
btn_rename.pack(fill="x", padx=8, pady=6)
btn_delete.pack(fill="x", padx=8, pady=6)
btn_type.pack(fill="x", padx=8, pady=6)

# Área central: PanedWindow
paned = PanedWindow(body, orient="vertical")
paned.pack(fill="both", expand=True, side="left")

# Grid
preview_frame = ctk.CTkFrame(paned)
preview_table = ttk.Treeview(preview_frame)
preview_table.pack(fill="both", expand=True, side="left")

scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_table.yview)
scroll_y.pack(side="right", fill="y")
preview_table.configure(yscroll=scroll_y.set)

scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=preview_table.xview)
scroll_x.pack(side="bottom", fill="x")
preview_table.configure(xscroll=scroll_x.set)

# Log
log_frame = ctk.CTkFrame(paned)
log_box = ctk.CTkTextbox(log_frame)
log_box.pack(fill="both", expand=True)

# Adiciona ao paned
paned.add(preview_frame, stretch="always")
paned.add(log_frame, stretch="always")

# Rodapé fixo
footer_frame = ctk.CTkFrame(app)
footer_frame.pack(fill="x", padx=16, pady=(0,8), side="bottom")
shape_label = ctk.CTkLabel(footer_frame, text="Linhas: 0 | Colunas: 0 | Nulos: 0", anchor="e")
shape_label.pack(anchor="e", padx=10)

log("👋 Bem-vindo! Carregue um arquivo para começar.")
app.mainloop()
