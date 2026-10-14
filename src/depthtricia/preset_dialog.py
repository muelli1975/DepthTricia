from dataclasses import asdict
from tkinter import messagebox
import customtkinter as ctk

from .config import InferencePreset, BUILTIN_PRESETS
from .model_catalog import DEPTH_MODELS, MODEL_STANDARD_RESOLUTIONS
from .theme import (BG_MAIN, TEXT, TEXT_DISABLED, INPUT_BG, BORDER, BUTTON_BG, BUTTON_HOVER,
                    LANGUAGE_BG, LANGUAGE_BUTTON_BG, LANGUAGE_HOVER,
                    LANGUAGE_DROPDOWN_BG, LANGUAGE_DROPDOWN_HOVER)


class PresetDialog(ctk.CTkToplevel):
    """Edit a complete profile; built-ins can only be saved under a custom name."""
    def __init__(self, app, create=False):
        super().__init__(app)
        self.app = app
        self.title(app.tr("preset.create" if create else "preset.edit"))
        self.geometry("510x390")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self.transient(app)
        self.grid_columnconfigure(1, weight=1)
        profile = app.current_profile()
        self.editing_name = app.active_preset if not create else ""
        self.name = ctk.StringVar(value=self.editing_name)
        self.model_id = profile.model_id
        self.device_names = {"auto": app.tr("device.auto"), "cuda": "NVIDIA", "cpu": "CPU"}
        self.model = ctk.StringVar(value=DEPTH_MODELS[profile.model_id])
        self.device = ctk.StringVar(value=self.device_names[profile.device])
        self.resolution = ctk.StringVar()
        self.stored_resolution = profile.resolution
        self.edge_x = ctk.StringVar(value=str(profile.edge_x))
        self.edge_y = ctk.StringVar(value=str(profile.edge_y))
        style = dict(fg_color=LANGUAGE_BG, button_color=LANGUAGE_BUTTON_BG,
                     button_hover_color=LANGUAGE_HOVER, text_color=TEXT,
                     dropdown_fg_color=LANGUAGE_DROPDOWN_BG,
                     dropdown_hover_color=LANGUAGE_DROPDOWN_HOVER, dropdown_text_color=TEXT)
        self.row(0, "preset.name", self.name)
        self.label(1, "label.depth_model")
        self.model_menu = ctk.CTkOptionMenu(self, variable=self.model,
            values=list(DEPTH_MODELS.values()), command=self.choose_model, dynamic_resizing=False, **style)
        self.model_menu.grid(row=1, column=1, padx=18, pady=8, sticky="ew")
        self.label(2, "label.device")
        ctk.CTkOptionMenu(self, variable=self.device, values=list(self.device_names.values()),
            dynamic_resizing=False, **style).grid(row=2, column=1, padx=18, pady=8, sticky="ew")
        self.label(3, "preset.resolution")
        self.res_menu = ctk.CTkComboBox(self, variable=self.resolution,
            border_color=BORDER, **style)
        self.res_menu.grid(row=3, column=1, padx=18, pady=8, sticky="ew")
        self.refresh_resolution()
        self.row(4, "preset.edge_x", self.edge_x)
        self.row(5, "preset.edge_y", self.edge_y)
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=6, column=0, columnspan=2, padx=18, pady=18, sticky="ew")
        for column, (key, command) in enumerate((("preset.save", self.save), ("preset.delete", self.delete), ("preset.cancel", self.destroy))):
            button = ctk.CTkButton(buttons, text=app.tr(key), width=140, command=command,
                fg_color=BUTTON_BG, hover_color=BUTTON_HOVER, text_color=TEXT,
                text_color_disabled=TEXT_DISABLED, border_width=1, border_color=BORDER)
            button.grid(row=0, column=column, padx=4)
            if key == "preset.delete" and not self.editing_name:
                button.configure(state="disabled")

    def label(self, row, key):
        ctk.CTkLabel(self, text=self.app.tr(key)).grid(row=row, column=0, padx=18, pady=8, sticky="w")

    def row(self, row, key, variable):
        self.label(row, key)
        ctk.CTkEntry(self, textvariable=variable, fg_color=INPUT_BG,
            border_color=BORDER).grid(row=row, column=1, padx=18, pady=8, sticky="ew")

    def resolution_value(self):
        if self.model_id == "depthpro":
            return 0
        return 0 if self.resolution.get() == self.model_default_label else int(self.resolution.get())

    def refresh_resolution(self):
        self.model_default_label = self.app.tr("preset.model_default") + f" ({MODEL_STANDARD_RESOLUTIONS[self.model_id]})"
        native = self.model_id == "depthpro"
        self.res_menu.configure(values=[self.model_default_label, "1218", "2048"],
            state="disabled" if native else "normal", text_color=TEXT_DISABLED if native else TEXT)
        self.resolution.set(self.model_default_label if native or self.stored_resolution == 0 else str(self.stored_resolution))

    def choose_model(self, value):
        try:
            self.stored_resolution = self.resolution_value()
        except ValueError:
            self.stored_resolution = self.resolution.get()
        self.model_id = next(key for key, name in DEPTH_MODELS.items() if name == value)
        self.refresh_resolution()

    def settings(self):
        device = next(key for key, name in self.device_names.items() if name == self.device.get())
        preset = InferencePreset(self.model_id, device, int(self.resolution_value()),
                                 int(self.edge_x.get()), int(self.edge_y.get()))
        preset.validate()
        return preset

    def save(self):
        try:
            preset = self.settings()
            name = self.name.get().strip()
            if not name:
                raise ValueError(self.app.tr("preset.name_required"))
        except ValueError as exc:
            messagebox.showerror(self.app.tr("dialog.error_title"), str(exc), parent=self)
            return
        self.app.depth_presets[name] = asdict(preset)
        self.app.apply_profile(preset, name=name)
        self.destroy()

    def delete(self):
        if self.editing_name in self.app.depth_presets:
            del self.app.depth_presets[self.editing_name]
            self.app.apply_profile(BUILTIN_PRESETS["standard"], builtin="standard")
        self.destroy()
