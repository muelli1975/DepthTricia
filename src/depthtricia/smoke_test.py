"""Build verification through the same frozen executable shipped to testers."""
from pathlib import Path
import gc
import socket
import tempfile


def run(app_dir: Path) -> dict:
    def offline(*args, **kwargs):
        raise RuntimeError("Unexpected network connection during packaged smoke test")

    original_connect, original_create = socket.socket.connect, socket.create_connection
    socket.socket.connect, socket.create_connection = offline, offline
    try:
        from PIL import Image, ImageDraw
        from .config import ProcessingConfig, DepthPreset
        from .controller import ProcessingController
        from .gui import DepthTriciaApp
        from .runtime import prepare_imports
        gui_settings = tempfile.TemporaryDirectory(prefix="depthtricia-gui-smoke-")
        app = DepthTriciaApp(app_dir)
        app.settings_path = Path(gui_settings.name) / 'settings.json'
        try:
            app.update()
            app._set_processing_controls(True)
            for widget in (app.model_menu, app.device_menu, app.preset_button,
                           app.original_size_check, app.save_depth_map_check):
                if widget.cget("state") != "disabled":
                    raise RuntimeError("Processing controls are not locked")
            app._set_processing_controls(False)
            app.edit_presets()
            app.update()
            for key, value in [('quick', 0), ('standard', 1218), ('fine', 2048)]:
                app.preset_dialog.load(app.preset_dialog.builtin_labels[key])
                if app.preset_dialog.settings().resolution != value:
                    raise RuntimeError('Built-in depth preset is incorrect')
            for model, value in [('da2', 518), ('da3', 504), ('depthpro', 1536)]:
                from .model_catalog import DEPTH_MODELS
                app._choose_depth_model(DEPTH_MODELS[model])
                if f'({value})' not in app.preset_dialog.model_default_label:
                    raise RuntimeError('Model standard resolution label is incorrect')
                if model != 'depthpro':
                    app.preset_dialog.resolution.set(app.preset_dialog.model_default_label)
                    if app.preset_dialog.settings().resolution != 0:
                        raise RuntimeError('Model standard preset no longer stores zero')
            if app.preset_dialog.res_menu.cget('state') != 'disabled':
                raise RuntimeError('Depth Pro resolution is not fixed')
            app.preset_dialog.destroy()
            app.original_size.set(True)
            app.save_depth_map.set(True)
            app._save_paths()
            from .settings import load_settings
            saved = load_settings(app.settings_path)
            if saved['original_size'] is not True or saved['save_depth_map'] is not True:
                raise RuntimeError('Output checkbox settings were not saved')
            for geometry in ('1280x800', '1100x700'):
                app.geometry(geometry)
                app.update()
                for widget in (app.original_size_check, app.save_depth_map_check):
                    if widget.winfo_rootx() + widget.winfo_width() > app.language_menu.winfo_rootx():
                        raise RuntimeError('Output checkbox overlaps language menu')
        finally:
            app.destroy()
            gui_settings.cleanup()
        # Start the GUI before installing the large libraries. Build tests use
        # verified local ZIPs; no online request is permitted in this test.
        from .runtime_install import install_runtime
        install_runtime(app_dir, confirmed=True)
        from .downloads import verify_model
        from .model_catalog import FILES
        verify_model(app_dir / 'models', FILES['depthpro'])
        import torch
        torch.set_num_threads(min(4, torch.get_num_threads()))  # Test host only.
        prepare_imports(app_dir)
        # Config-selected modules must work in the frozen package too.
        from depth_anything_3.cfg import create_object, load_config
        from depth_anything_3.registry import MODEL_REGISTRY
        from depth_pro.depth_pro import create_model_and_transforms  # noqa: F401
        da3 = create_object(load_config(MODEL_REGISTRY["da3mono-large"]))
        da3_parameters = sum(parameter.numel() for parameter in da3.parameters())
        del da3
        gc.collect()
        with tempfile.TemporaryDirectory(prefix="depthtricia-smoke-") as folder:
            temporary = Path(folder)
            source = temporary / "scene.jpg"
            image = Image.new("RGB", (192, 128), (70, 110, 170))
            ImageDraw.Draw(image).ellipse((40, 20, 150, 118), fill=(220, 80, 50))
            exif = Image.Exif()
            exif[315] = "DepthTricia smoke test"
            image.save(source, exif=exif)
            config = ProcessingConfig(app_dir, model_id="da2", device="cpu",
                preset=DepthPreset(resolution=392), exiftool_path=app_dir / "tools/exiftool.exe",
                target_height=0, save_depth_map=True, append_settings_to_filename=True)
            stages = []
            controller = ProcessingController(config, lambda event: stages.append(event.stage))
            items = controller.run(source, temporary / "output")
            if len(items) != 1 or items[0].status != "ok":
                raise RuntimeError("Packaged CPU conversion failed")
            for path, dimensions in ((items[0].sbs_path, (384, 128)),
                                     (items[0].anaglyph_path, (192, 128))):
                with Image.open(path) as output:
                    if output.size != dimensions or output.getexif().get(315) != exif[315]:
                        raise RuntimeError("Output dimensions or metadata are incorrect")
            from .cache import load_depth
            import json
            import numpy as np
            cache_file = next((temporary / 'output/_temp').glob('*.npy'))
            cache_record = cache_file.with_suffix('.json')
            depth = load_depth(cache_file, cache_record, json.loads(cache_record.read_text())['identity'])
            with Image.open(items[0].depth_png_path) as output:
                if output.size != (depth.shape[1], depth.shape[0]):
                    raise RuntimeError('Depth PNG resolution changed')
                if not np.array_equal(np.asarray(output), np.rint(depth * 65535).astype(np.uint16)):
                    raise RuntimeError('Depth PNG values differ from the used depth cache')
            if '_DA2Small_d15_w100_o0_' not in items[0].sbs_path.name:
                raise RuntimeError('Model missing from settings filename')
            items[0].depth_png_path.unlink()
            stages.clear()
            items = controller.run(source, temporary / "output")
            if items[0].status != "ok" or "inference_skipped" not in stages:
                raise RuntimeError("Packaged depth cache reuse failed")
            if not items[0].depth_png_path.is_file():
                raise RuntimeError('Cached depth PNG was not exported')
        return dict(torch=torch.__version__, cuda_runtime=torch.version.cuda,
            inference_device="cpu", gui=True, presets=True, da3_configuration=True,
            da3_parameters=da3_parameters, depthpro_import=True, depthpro_weights=True, da2_inference=True,
            stereo_inpainting=True, outputs=True, depth_png=True, original_size=True,
            model_filename=True, metadata=True, cache=True, offline=True)
    finally:
        socket.socket.connect, socket.create_connection = original_connect, original_create
