import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import json
import os
import threading

from config import load_config, save_config, get_api_key
from utils.ai_helper import generate_test_cases
from utils.jira_export import generate_jira_csv, generate_xray_csv, sanitize_filename

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

FONT_FAMILY = "Consolas"
FONT_SIZE = 14

BG_FRAME = "#1a1a2e"
BG_CARD = "#16213e"
FG_PRIMARY = "#0f3460"
ACCENT = "#4ecca3"
TEXT_COLOR = "#e0e0e0"

class TestCaseCard(ctk.CTkFrame):
    def __init__(self, master, test_case, index, on_delete, on_edit, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=8, **kwargs)
        self.test_case = test_case
        self.index = index

        self.grid_columnconfigure(2, weight=1)

        header = f"#{test_case.get('id', '')}  {test_case.get('resumen', '')}"
        lbl_id = ctk.CTkLabel(self, text=header,
                              font=(FONT_FAMILY, 12, "bold"), text_color=ACCENT, anchor="w")
        lbl_id.grid(row=0, column=0, padx=(10, 5), pady=(8, 0), sticky="w")

        tipo = test_case.get("tipo_test", "Manual")
        lbl_tipo = ctk.CTkLabel(self, text=f"[{tipo}]",
                                font=(FONT_FAMILY, 11), text_color="#6bcb77", anchor="w")
        lbl_tipo.grid(row=0, column=1, padx=(0, 5), pady=(8, 0), sticky="w")

        lbl_desc = ctk.CTkLabel(self, text=test_case.get("descripcion", ""),
                                font=(FONT_FAMILY, FONT_SIZE), text_color=TEXT_COLOR,
                                anchor="w", wraplength=400, justify="left")
        lbl_desc.grid(row=0, column=2, padx=(5, 10), pady=(8, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=3, padx=(5, 10), pady=(8, 0), sticky="e")

        btn_edit = ctk.CTkButton(btn_frame, text="✎", width=30, height=24,
                                 font=(FONT_FAMILY, 12), fg_color=FG_PRIMARY,
                                 hover_color="#1a5276", command=self._on_edit)
        btn_edit.pack(side="left", padx=2)

        btn_del = ctk.CTkButton(btn_frame, text="✕", width=30, height=24,
                                font=(FONT_FAMILY, 12), fg_color="#6b2020",
                                hover_color="#8b3030", command=self._on_delete)
        btn_del.pack(side="left", padx=2)

        self._expanded = False
        self._detail_frame = None

        self.bind("<Button-1>", self._toggle_expand)
        lbl_id.bind("<Button-1>", self._toggle_expand)
        lbl_desc.bind("<Button-1>", self._toggle_expand)

        self._on_delete_cb = on_delete
        self._on_edit_cb = on_edit

    def _toggle_expand(self, event=None):
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        if self._detail_frame:
            return
        self._expanded = True
        self._detail_frame = ctk.CTkFrame(self, fg_color="#0d1b2a", corner_radius=6)
        self._detail_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="ew")
        self._detail_frame.grid_columnconfigure(0, weight=1)

        tc = self.test_case
        fields = [
            ("Acción", tc.get("accion", "")),
            ("Datos de Prueba", tc.get("datos_prueba", "")),
            ("Resultado Esperado", tc.get("resultado_esperado", "")),
        ]
        if tc.get("directorio"):
            fields.append(("Directorio", tc.get("directorio", "")))

        for label, value in fields:
            if value:
                self._add_detail_row(label, value)

    def _add_detail_row(self, label, value):
        row = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(row, text=label, font=(FONT_FAMILY, 11, "bold"),
                     text_color=ACCENT, width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=value, font=(FONT_FAMILY, 12),
                     text_color=TEXT_COLOR, anchor="w", wraplength=500, justify="left").pack(
            side="left", padx=10, fill="x", expand=True)

    def _collapse(self):
        self._expanded = False
        if self._detail_frame:
            self._detail_frame.destroy()
            self._detail_frame = None

    def _on_edit(self):
        self._on_edit_cb(self.index)

    def _on_delete(self):
        self._on_delete_cb(self.index)


class EditTestCaseDialog(ctk.CTkToplevel):
    def __init__(self, parent, test_case, on_save):
        super().__init__(parent)
        self.title("Editar Caso de Prueba")
        self.geometry("650x550")
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save
        self._test_case = dict(test_case)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(5, weight=1)

        fields = [
            ("ID", "id", "entry"),
            ("Resumen", "resumen", "entry"),
            ("Descripcion", "descripcion", "text"),
            ("Acción", "accion", "text"),
            ("Datos de Prueba", "datos_prueba", "text"),
            ("Resultado Esperado", "resultado_esperado", "text"),
        ]

        self._entries = {}
        for i, (label, key, widget_type) in enumerate(fields):
            ctk.CTkLabel(self, text=label, font=(FONT_FAMILY, 12)).grid(
                row=i, column=0, padx=10, pady=5, sticky="nw")
            if widget_type == "entry":
                widget = ctk.CTkEntry(self, font=(FONT_FAMILY, FONT_SIZE), fg_color=BG_CARD)
                widget.insert(0, test_case.get(key, ""))
                widget.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            else:
                widget = ctk.CTkTextbox(self, height=55 if key == "descripcion" else 50,
                                        font=(FONT_FAMILY, 12), fg_color=BG_CARD)
                widget.insert("0.0", test_case.get(key, ""))
                widget.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self._entries[key] = widget

        row_offset = len(fields)
        ctk.CTkLabel(self, text="Tipo de Test", font=(FONT_FAMILY, 12)).grid(
            row=row_offset, column=0, padx=10, pady=5, sticky="w")
        tipo_var = tk.StringVar(value=test_case.get("tipo_test", "Manual"))
        tipo_menu = ctk.CTkOptionMenu(self, values=["Manual", "Automático"],
                                      variable=tipo_var, font=(FONT_FAMILY, 12),
                                      fg_color=FG_PRIMARY, button_color=ACCENT)
        tipo_menu.grid(row=row_offset, column=1, padx=10, pady=5, sticky="w")
        self._tipo_var = tipo_var

        row_offset += 1
        ctk.CTkLabel(self, text="Directorio", font=(FONT_FAMILY, 12)).grid(
            row=row_offset, column=0, padx=10, pady=5, sticky="w")
        dir_entry = ctk.CTkEntry(self, font=(FONT_FAMILY, FONT_SIZE), fg_color=BG_CARD)
        dir_entry.insert(0, test_case.get("directorio", ""))
        dir_entry.grid(row=row_offset, column=1, padx=10, pady=5, sticky="ew")
        self._dir_entry = dir_entry

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row_offset + 1, column=0, columnspan=2, pady=15)
        ctk.CTkButton(btn_frame, text="Guardar", font=(FONT_FAMILY, FONT_SIZE),
                       fg_color=ACCENT, text_color="#000",
                       command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", font=(FONT_FAMILY, FONT_SIZE),
                       fg_color="#444", command=self.destroy).pack(side="left", padx=5)

    def _save(self):
        def get_text(key):
            w = self._entries[key]
            if isinstance(w, ctk.CTkTextbox):
                return w.get("0.0", "end").strip()
            return w.get().strip()

        for key in ["id", "resumen", "descripcion", "accion", "datos_prueba", "resultado_esperado"]:
            self._test_case[key] = get_text(key)
        self._test_case["tipo_test"] = self._tipo_var.get()
        self._test_case["directorio"] = self._dir_entry.get().strip()
        self._on_save(self._test_case)
        self.destroy()


class ListModelsResult(ctk.CTkToplevel):
    def __init__(self, parent, models):
        super().__init__(parent)
        self.title("Modelos Disponibles")
        self.geometry("550x400")
        self.transient(parent)

        text = ctk.CTkTextbox(self, font=(FONT_FAMILY, 13), fg_color=BG_CARD, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("0.0", models)
        text.configure(state="disabled")


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("Ajustes")
        self.geometry("520x320")
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save
        self._config = dict(config)

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="API Key de Gemini", font=(FONT_FAMILY, 12)).grid(
            row=0, column=0, padx=10, pady=15, sticky="w")
        api_var = tk.StringVar(value=config.get("api_key", ""))
        api_entry = ctk.CTkEntry(self, textvariable=api_var, font=(FONT_FAMILY, 14),
                                 fg_color=BG_CARD, show="*", width=300)
        api_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self._api_var = api_var

        ctk.CTkLabel(self, text="Modelo", font=(FONT_FAMILY, 12)).grid(
            row=1, column=0, padx=10, pady=10, sticky="w")
        current_model = config.get("model", "gemini-2.0-flash")
        models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash"]
        if current_model not in models:
            models.insert(0, current_model)
        model_var = tk.StringVar(value=current_model)
        model_menu = ctk.CTkOptionMenu(self, values=models,
                                       variable=model_var, font=(FONT_FAMILY, 12),
                                       fg_color=FG_PRIMARY, button_color=ACCENT, width=200)
        model_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self._model_var = model_var

        test_btn = ctk.CTkButton(self, text="🔍 Listar modelos",
                                  font=(FONT_FAMILY, 11), fg_color=FG_PRIMARY,
                                  hover_color="#1a5276", command=self._list_models)
        test_btn.grid(row=1, column=1, padx=(220, 0), pady=10, sticky="w")

        ctk.CTkLabel(self, text="Proyecto Jira (key)", font=(FONT_FAMILY, 12)).grid(
            row=2, column=0, padx=10, pady=10, sticky="w")
        proj_var = tk.StringVar(value=config.get("project_key", ""))
        proj_entry = ctk.CTkEntry(self, textvariable=proj_var, font=(FONT_FAMILY, 14),
                                  fg_color=BG_CARD, width=150)
        proj_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self._proj_var = proj_var

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_frame, text="Guardar", font=(FONT_FAMILY, FONT_SIZE),
                       fg_color=ACCENT, text_color="#000",
                       command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", font=(FONT_FAMILY, FONT_SIZE),
                       fg_color="#444", command=self.destroy).pack(side="left", padx=5)

    def _list_models(self):
        api_key = self._api_var.get().strip()
        if not api_key:
            messagebox.showwarning("API Key requerida", "Poné la API key primero.")
            return
        try:
            import urllib.request, json
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            lines = []
            for m in models:
                name = m.get("name", "")
                desc = m.get("description", "")
                if "generateContent" in m.get("supportedMethods", []):
                    lines.append(f"{name}  —  {desc[:100]}")
            result = "\n".join(lines) if lines else "No se encontraron modelos con generateContent."
            ListModelsResult(self, result)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron listar modelos:\n{e}")

    def _save(self):
        self._config["api_key"] = self._api_var.get().strip()
        self._config["model"] = self._model_var.get()
        self._config["project_key"] = self._proj_var.get().strip()
        self._on_save(self._config)
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QA Test Case Generator — Gemini")
        self.geometry("1200x750")
        self.minsize(900, 600)

        self._config = load_config()
        self._test_cases = []
        self._cards = []

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_main_area()
        self._build_status_bar()

    def _build_topbar(self):
        top = ctk.CTkFrame(self, fg_color=BG_FRAME, height=50)
        top.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text="🧪 QA Test Case Generator",
                     font=(FONT_FAMILY, 18, "bold"), text_color=ACCENT).pack(side="left", padx=15, pady=8)

        btn_settings = ctk.CTkButton(top, text="⚙ Ajustes", font=(FONT_FAMILY, 13),
                                     fg_color=FG_PRIMARY, hover_color="#1a5276",
                                     width=100, command=self._open_settings)
        btn_settings.pack(side="right", padx=10, pady=8)

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color=BG_FRAME)
        main.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        self._build_input_panel(main)
        self._build_results_panel(main)

    def _build_input_panel(self, parent):
        left = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=5)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(left, text="Historia de Usuario", font=(FONT_FAMILY, 14, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(left, text="Código de HU", font=(FONT_FAMILY, 11),
                     text_color=TEXT_COLOR).grid(row=1, column=0, padx=10, pady=(0, 2), sticky="w")
        self._hu_entry = ctk.CTkEntry(left, font=(FONT_FAMILY, FONT_SIZE),
                                       fg_color="#0d1b2a", placeholder_text="Ej: HU-123")
        self._hu_entry.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")

        ctk.CTkLabel(left, text="Criterios de Aceptación (uno por línea)",
                     font=(FONT_FAMILY, 11), text_color=TEXT_COLOR).grid(
            row=3, column=0, padx=10, pady=(5, 2), sticky="w")
        self._story_text = ctk.CTkTextbox(left, font=(FONT_FAMILY, FONT_SIZE),
                                           fg_color="#0d1b2a", wrap="word")
        self._story_text.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self._generate_btn = ctk.CTkButton(
            left, text="🚀 Generar Casos de Prueba", font=(FONT_FAMILY, 15, "bold"),
            fg_color=ACCENT, text_color="#000", height=42,
            hover_color="#3db88b", command=self._generate)
        self._generate_btn.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")

    def _build_results_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 5), pady=5)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(right, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_bar.grid_columnconfigure(0, weight=1)

        self._results_count = ctk.CTkLabel(top_bar, text="Casos generados: 0",
                                            font=(FONT_FAMILY, 14, "bold"), text_color=ACCENT)
        self._results_count.pack(side="left")

        export_btn = ctk.CTkButton(top_bar, text="📥 Exportar CSV (Jira)",
                                    font=(FONT_FAMILY, 12), fg_color=FG_PRIMARY,
                                    hover_color="#1a5276", command=self._export_jira_csv)
        export_btn.pack(side="right", padx=3)

        export_xray_btn = ctk.CTkButton(top_bar, text="📥 Exportar Xray",
                                         font=(FONT_FAMILY, 12), fg_color=FG_PRIMARY,
                                         hover_color="#1a5276", command=self._export_xray_csv)
        export_xray_btn.pack(side="right", padx=3)

        clear_btn = ctk.CTkButton(top_bar, text="🗑 Limpiar",
                                   font=(FONT_FAMILY, 12), fg_color="#6b2020",
                                   hover_color="#8b3030", command=self._clear_results)
        clear_btn.pack(side="right", padx=3)

        self._canvas = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._canvas.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))

    def _build_status_bar(self):
        status = ctk.CTkFrame(self, fg_color=BG_FRAME, height=28)
        status.grid(row=2, column=0, sticky="ew")
        self._status_label = ctk.CTkLabel(status, text="Listo",
                                           font=(FONT_FAMILY, 11), text_color="#888")
        self._status_label.pack(side="left", padx=10)

    def _set_status(self, text):
        self._status_label.configure(text=text)
        self.update_idletasks()

    def _render_cards(self):
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        for i, tc in enumerate(self._test_cases):
            card = TestCaseCard(
                self._canvas, tc, i,
                on_delete=self._delete_case,
                on_edit=self._edit_case,
            )
            card.pack(fill="x", padx=5, pady=3)
            self._cards.append(card)

        self._results_count.configure(text=f"Casos generados: {len(self._test_cases)}")

    def _generate(self):
        story = self._story_text.get("0.0", "end").strip()
        hu_code = self._hu_entry.get().strip()

        if not story:
            messagebox.showwarning("Falta información",
                                    "Ingresá los criterios de aceptación antes de generar.")
            return

        self._generate_btn.configure(state="disabled", text="⏳ Generando...")
        self._set_status("Generando casos de prueba con Gemini...")

        def task():
            try:
                api_key = get_api_key()
                cases = generate_test_cases(
                    api_key, story,
                    model=self._config.get("model", "gemini-2.0-flash"),
                    hu_code=hu_code,
                )
                self.after(0, self._on_generated, cases)
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                self.after(0, self._on_error, err_msg)

        threading.Thread(target=task, daemon=True).start()

    def _on_generated(self, cases):
        self._test_cases = cases[:50]
        self._render_cards()
        self._generate_btn.configure(state="normal", text="🚀 Generar Casos de Prueba")
        self._set_status(f"✅ {len(cases)} casos generados")
        messagebox.showinfo("Completado", f"Se generaron {len(cases)} casos de prueba.")

    def _on_error(self, error):
        self._generate_btn.configure(state="normal", text="🚀 Generar Casos de Prueba")
        self._set_status("❌ Error")
        messagebox.showerror("Error", error)

    def _delete_case(self, index):
        if 0 <= index < len(self._test_cases):
            del self._test_cases[index]
            self._render_cards()

    def _edit_case(self, index):
        if 0 <= index < len(self._test_cases):
            def on_save(updated):
                self._test_cases[index] = updated
                self._render_cards()
            EditTestCaseDialog(self, self._test_cases[index], on_save)

    def _clear_results(self):
        self._test_cases.clear()
        self._render_cards()
        self._set_status("Resultados limpiados")

    def _export_jira_csv(self):
        if not self._test_cases:
            messagebox.showwarning("Sin datos", "No hay casos de prueba para exportar.")
            return
        fname = f"test_cases_jira_{sanitize_filename(self._hu_entry.get().strip() or 'export')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=fname,
            filetypes=[("CSV files", "*.csv")],
        )
        if filepath:
            generate_jira_csv(self._test_cases, filepath)
            self._set_status(f"Exportado a {os.path.basename(filepath)}")

    def _export_xray_csv(self):
        if not self._test_cases:
            messagebox.showwarning("Sin datos", "No hay casos de prueba para exportar.")
            return
        fname = f"test_cases_xray_{sanitize_filename(self._hu_entry.get().strip() or 'export')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=fname,
            filetypes=[("CSV files", "*.csv")],
        )
        if filepath:
            generate_xray_csv(self._test_cases, filepath)
            self._set_status(f"Exportado a {os.path.basename(filepath)}")

    def _open_settings(self):
        SettingsDialog(self, self._config, self._on_save_config)

    def _on_save_config(self, config):
        self._config = config
        save_config(config)
        self._set_status("Configuración guardada")

    def _on_close(self):
        if self._test_cases:
            fname = "autosave_test_cases.json"
            path = os.path.join(os.path.dirname(__file__), "..", "data", fname)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._test_cases, f, indent=2, ensure_ascii=False)
            except IOError:
                pass
        self.destroy()
