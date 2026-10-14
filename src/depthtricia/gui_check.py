"""Exercise the real GUI without importing a model or downloading anything."""
from dataclasses import asdict
from pathlib import Path
import tempfile


def check(app_dir: Path, *, screenshot_dir: Path | None = None):
    import customtkinter as ctk
    from .config import BUILTIN_PRESETS
    from .gui import DepthTriciaApp
    from .settings import load_settings
    report = []
    for locale in ('de', 'en'):
        with tempfile.TemporaryDirectory(prefix='depthtricia-gui-') as folder:
            settings = Path(folder) / 'settings.json'
            settings.write_text('{"language": "' + locale + '"}')
            app = DepthTriciaApp(app_dir, settings_path=settings)
            try:
                app.update()
                app._set_processing_controls(True)
                for widget in (app.preset_menu, app.original_size_check, app.save_depth_map_check):
                    assert widget.cget('state') == 'disabled', 'Processing controls are not locked'
                from .theme import TEXT_DISABLED, CHECKBOX_DISABLED
                assert app.preset_menu.cget('text_color_disabled') == TEXT_DISABLED
                assert app.language_menu.cget('text_color_disabled') == TEXT_DISABLED
                assert app.original_size_check.cget('fg_color') == CHECKBOX_DISABLED
                assert app.save_depth_map_check.cget('fg_color') == CHECKBOX_DISABLED
                app._set_processing_controls(False)
                for key, profile in BUILTIN_PRESETS.items():
                    label = next(label for label, entry in app.preset_choices.items() if entry == ('builtin', key))
                    app._choose_preset(label)
                    assert app.current_profile() == profile
                    assert f'{profile.edge_x}/{profile.edge_y}' in app.preset_info.cget('text')
                app._choose_preset(next(label for label, entry in app.preset_choices.items() if entry == ('builtin', 'standard')))
                assert app.model_id == 'da3' and app.device_id == 'auto'
                app.edit_presets(create=True)
                app.update()
                dialog = app.preset_dialog
                for model, value in [('da2', 518), ('da3', 504), ('depthpro', 1536)]:
                    from .model_catalog import DEPTH_MODELS
                    dialog.choose_model(DEPTH_MODELS[model])
                    assert f'({value})' in dialog.model_default_label
                    if model != 'depthpro':
                        dialog.resolution.set(dialog.model_default_label)
                        assert dialog.settings().resolution == 0
                assert dialog.res_menu.cget('state') == 'disabled'
                dialog.choose_model(DEPTH_MODELS['da3'])
                dialog.resolution.set('1344')
                own_name = 'Standard' + ' very long custom preset name' * 4
                dialog.name.set(own_name)
                dialog.save()
                assert app.active_preset == own_name and app.depth_preset.resolution == 1344
                assert app.preset_menu.cget('width') == 220
                app.original_size.set(True)
                app.save_depth_map.set(True)
                app._save_paths()
                saved = load_settings(settings)
                assert saved['original_size'] and saved['save_depth_map']
                assert saved['depth_presets'][own_name] == asdict(app.current_profile())
                for scale, geometry in ((1.0, '1280x880'), (1.0, '1100x700'), (1.25, '1280x880'), (1.5, '1280x880')):
                    ctk.set_widget_scaling(scale)
                    ctk.set_window_scaling(scale)
                    app.geometry(geometry)
                    settled = ctk.BooleanVar(value=False)
                    app.after(1200, lambda: settled.set(True))
                    app.wait_variable(settled)
                    app.update()
                    expected = [round(int(value) * scale) for value in geometry.split('x')]
                    assert [app.winfo_width(), app.winfo_height()] == expected, 'Window resize did not settle'
                    assert app.preset_info.winfo_rootx() + app.preset_info.winfo_width() <= app.language_menu.winfo_rootx(), 'Header overlaps language menu'
                    assert '\n' not in app.preset_info.cget('text'), 'Preset settings must stay on one line'
                    assert app.preset_info.winfo_rooty() == app.preset_menu.winfo_rooty(), 'Preset settings are not level with the menu'
                    assert app.original_size_check.winfo_rootx() == app.save_depth_map_check.winfo_rootx(), 'Output options must align on the left'
                    assert app.original_size_check.winfo_rooty() + app.original_size_check.winfo_height() < app.save_depth_map_check.winfo_rooty(), 'Output options must be stacked'
                    for widget in (app.preset_menu, app.language_menu, app.original_size_check, app.save_depth_map_check, app.defaults_button, app.clear_temp_button):
                        assert widget.winfo_rootx() >= app.winfo_rootx(), 'Control clipped on the left'
                        assert widget.winfo_rootx() + widget.winfo_width() <= app.winfo_rootx() + app.winfo_width(), 'Control clipped on the right'
                    if geometry == '1280x880':
                        assert not app.main_scrollbar.winfo_ismapped(), 'Default window must not need scrolling'
                        assert app.main_area.winfo_reqheight() <= app.main_canvas.winfo_height(), 'Default window clips its cards'
                        top = app.main_canvas.winfo_rooty()
                        bottom = top + app.main_canvas.winfo_height()
                        def check_bounds(parent):
                            for widget in parent.winfo_children():
                                if widget.__class__.__name__.startswith('CTk') and widget.winfo_ismapped():
                                    assert widget.winfo_rooty() >= top, 'Control clipped above the viewport'
                                    assert widget.winfo_rooty() + widget.winfo_height() <= bottom, 'Control clipped below the viewport'
                                check_bounds(widget)
                        check_bounds(app.main_area)
                        if screenshot_dir is not None and scale == 1.0:
                            from PIL import ImageGrab
                            screenshot_dir.mkdir(parents=True, exist_ok=True)
                            app.attributes('-topmost', True)
                            app.lift()
                            visible = ctk.BooleanVar(value=False)
                            app.after(200, lambda: visible.set(True))
                            app.wait_variable(visible)
                            app.update()
                            ImageGrab.grab(bbox=(app.winfo_rootx(), app.winfo_rooty(),
                                app.winfo_rootx() + app.winfo_width(), app.winfo_rooty() + app.winfo_height())
                            ).save(screenshot_dir / f'depthtricia-{locale}.png')
                            app.attributes('-topmost', False)
                    if app.main_area.winfo_height() > app.main_canvas.winfo_height():
                        assert app.main_scrollbar.winfo_ismapped(), 'Small window cannot reach all controls'
                    report.append(dict(locale=locale, scale=scale, geometry=geometry,
                        window=[app.winfo_width(), app.winfo_height()], content_height=app.main_area.winfo_height(),
                        viewport_height=app.main_canvas.winfo_height()))
            finally:
                for callback in app.tk.call('after', 'info'):
                    app.after_cancel(callback)
                app.destroy()
                ctk.set_widget_scaling(1.0)
                ctk.set_window_scaling(1.0)
    return report
