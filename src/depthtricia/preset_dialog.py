from dataclasses import asdict
from tkinter import messagebox
import customtkinter as ctk

from .config import DepthPreset
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
        self.resolution = ctk.StringVar(value=str(app.depth_preset.resolution) if app.depth_preset.resolution else app.tr("preset.model_default"))
        self.edge_x = ctk.StringVar(value=str(app.depth_preset.edge_x))
        self.edge_y = ctk.StringVar(value=str(app.depth_preset.edge_y))
        ctk.CTkLabel(self, text=app.tr("label.preset")).grid(row=0, column=0, padx=18, pady=12, sticky="w")
        self.menu = ctk.CTkOptionMenu(self, variable=self.choice,
                                     values=[app.tr("preset.default"), *app.depth_presets], command=self.load, **menu_style)
        self.menu.grid(row=0, column=1, padx=18, pady=12, sticky="ew")
        self.row(1, "preset.name", self.name)
        ctk.CTkLabel(self, text=app.tr("preset.resolution")).grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.res_menu = ctk.CTkComboBox(self, variable=self.resolution, values=[app.tr("preset.model_default"), "1218", "2048"],
                                       border_color=BORDER, **menu_style)
        self.res_menu.grid(row=2, column=1, padx=18, pady=8, sticky="ew")
        if app.model_id == "depthpro":
            self.res_menu.configure(state="disabled", text_color="#727272")
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

    def load(self, name):
        data = self.app.depth_presets.get(name, asdict(DepthPreset()))
        self.name.set(name if name in self.app.depth_presets else "")
        value = data.get("resolution", 1218)
        self.resolution.set(str(value) if value else self.app.tr("preset.model_default"))
        self.edge_x.set(str(data.get("edge_x", 2)))
        self.edge_y.set(str(data.get("edge_y", 1)))

    def settings(self):
        resolution = 0 if self.resolution.get() == self.app.tr("preset.model_default") else int(self.resolution.get())
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
