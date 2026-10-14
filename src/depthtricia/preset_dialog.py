from dataclasses import asdict
from tkinter import messagebox
import customtkinter as ctk

from .config import DepthPreset
from .model_catalog import MODEL_STANDARD_RESOLUTIONS
from .theme import (BG_MAIN, TEXT, INPUT_BG, BORDER, BUTTON_BG, BUTTON_HOVER,
                    LANGUAGE_BG, LANGUAGE_BUTTON_BG, LANGUAGE_HOVER,
                    LANGUAGE_DROPDOWN_BG, LANGUAGE_DROPDOWN_HOVER)


class PresetDialog(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(app.tr("button.presets"))
        self.geometry("470x330")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self.transient(app)
        self.grid_columnconfigure(1, weight=1)
        menu_style = dict(fg_color=LANGUAGE_BG, button_color=LANGUAGE_BUTTON_BG,
                          button_hover_color=LANGUAGE_HOVER, text_color=TEXT,
                          dropdown_fg_color=LANGUAGE_DROPDOWN_BG,
                          dropdown_hover_color=LANGUAGE_DROPDOWN_HOVER, dropdown_text_color=TEXT)
        self.choice = ctk.StringVar(value=app.active_preset or app.tr("preset.default"))
        self.name = ctk.StringVar(value=app.active_preset)
        self.current_model = app.model_id
        self.stored_resolution = app.depth_preset.resolution
        self.model_default_label = self.standard_label()
        self.resolution = ctk.StringVar()
        self.edge_x = ctk.StringVar(value=str(app.depth_preset.edge_x))
        self.edge_y = ctk.StringVar(value=str(app.depth_preset.edge_y))
        ctk.CTkLabel(self, text=app.tr("label.preset")).grid(row=0, column=0, padx=18, pady=12, sticky="w")
        self.menu = ctk.CTkOptionMenu(self, variable=self.choice,
                                     values=[app.tr("preset.default"), *app.depth_presets], command=self.load, **menu_style)
        self.menu.grid(row=0, column=1, padx=18, pady=12, sticky="ew")
        self.row(1, "preset.name", self.name)
        ctk.CTkLabel(self, text=app.tr("preset.resolution")).grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.res_menu = ctk.CTkComboBox(self, variable=self.resolution, values=[self.model_default_label, "1218", "2048"],
                                       border_color=BORDER, **menu_style)
        self.res_menu.grid(row=2, column=1, padx=18, pady=8, sticky="ew")
        self.refresh_model()
        self.row(3, "preset.edge_x", self.edge_x)
        self.row(4, "preset.edge_y", self.edge_y)
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=5, column=0, columnspan=2, padx=18, pady=18, sticky="ew")
        for column, (key, command) in enumerate((("preset.save", self.save), ("preset.delete", self.delete), ("preset.apply", self.apply))):
            ctk.CTkButton(buttons, text=app.tr(key), width=125, command=command,
                          fg_color=BUTTON_BG, hover_color=BUTTON_HOVER, text_color=TEXT,
                          border_width=1, border_color=BORDER).grid(row=0, column=column, padx=4)

    def row(self, row, key, variable):
        ctk.CTkLabel(self, text=self.app.tr(key)).grid(row=row, column=0, padx=18, pady=8, sticky="w")
        ctk.CTkEntry(self, textvariable=variable, fg_color=INPUT_BG, border_color=BORDER).grid(row=row, column=1, padx=18, pady=8, sticky="ew")

    def standard_label(self):
        return self.app.tr("preset.model_default") + f" ({MODEL_STANDARD_RESOLUTIONS[self.app.model_id]})"

    def resolution_value(self):
        if self.current_model == "depthpro" or not self.resolution.get():
            return self.stored_resolution
        return 0 if self.resolution.get() == self.model_default_label else int(self.resolution.get())

    def refresh_model(self):
        try:
            self.stored_resolution = self.resolution_value()
        except ValueError:
            self.stored_resolution = self.resolution.get()
        self.current_model = self.app.model_id
        self.model_default_label = self.standard_label()
        native = self.current_model == "depthpro"
        self.res_menu.configure(values=[self.model_default_label, "1218", "2048"],
            state="disabled" if native else "normal", text_color="#727272" if native else TEXT)
        self.resolution.set(self.model_default_label if native or self.stored_resolution == 0
                            else str(self.stored_resolution))

    def load(self, name):
        data = self.app.depth_presets.get(name, asdict(DepthPreset()))
        self.name.set(name if name in self.app.depth_presets else "")
        value = data.get("resolution", 1218)
        self.stored_resolution = value
        self.resolution.set(self.model_default_label if self.current_model == "depthpro" or value == 0 else str(value))
        self.edge_x.set(str(data.get("edge_x", 2)))
        self.edge_y.set(str(data.get("edge_y", 1)))

    def settings(self):
        resolution = int(self.resolution_value())
        preset = DepthPreset(resolution, int(self.edge_x.get()), int(self.edge_y.get()))
        preset.validate()
        return preset

    def save(self):
        try:
            preset = self.settings()
            name = self.name.get().strip()
            if not name or name == self.app.tr("preset.default"):
                raise ValueError(self.app.tr("preset.name_required"))
        except ValueError as exc:
            messagebox.showerror(self.app.tr("dialog.error_title"), str(exc), parent=self)
            return
        self.app.depth_presets[name] = asdict(preset)
        self.app.active_preset = name
        self.app.depth_preset = preset
        self.menu.configure(values=[self.app.tr("preset.default"), *self.app.depth_presets])
        self.choice.set(name)
        self.app._save_paths()

    def delete(self):
        name = self.choice.get()
        if name in self.app.depth_presets:
            del self.app.depth_presets[name]
            self.app.active_preset = ""
            self.app.depth_preset = DepthPreset()
            self.menu.configure(values=[self.app.tr("preset.default"), *self.app.depth_presets])
            self.choice.set(self.app.tr("preset.default"))
            self.load(self.choice.get())
            self.app._save_paths()

    def apply(self):
        try:
            self.app.depth_preset = self.settings()
        except ValueError as exc:
            messagebox.showerror(self.app.tr("dialog.error_title"), str(exc), parent=self)
            return
        # A saved preset is changed only through Save, never implicitly.
        if self.name.get().strip() in self.app.depth_presets:
            if asdict(self.app.depth_preset) == self.app.depth_presets[self.name.get().strip()]:
                self.app.active_preset = self.name.get().strip()
            else:
                self.app.active_preset = ""
        else:
            self.app.active_preset = ""
        self.app._save_paths()
        self.destroy()
