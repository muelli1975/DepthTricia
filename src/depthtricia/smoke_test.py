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
        app = DepthTriciaApp(app_dir)
        try:
            app.update()
            app._set_processing_controls(True)
            for widget in (app.model_menu, app.device_menu, app.preset_button):
                if widget.cget("state") != "disabled":
                    raise RuntimeError("Processing controls are not locked")
            app._set_processing_controls(False)
            app.edit_presets()
            app.update()
            app.preset_dialog.destroy()
        finally:
            app.destroy()
        # Start the GUI before installing the large libraries. Build tests use
        # verified local ZIPs; no online request is permitted in this test.
        from .runtime_install import install_runtime
        install_runtime(app_dir, confirmed=True)
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
                preset=DepthPreset(resolution=392), exiftool_path=app_dir / "tools/exiftool.exe")
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
            stages.clear()
            items = controller.run(source, temporary / "output")
            if items[0].status != "ok" or "inference_skipped" not in stages:
                raise RuntimeError("Packaged depth cache reuse failed")
        return dict(torch=torch.__version__, cuda_runtime=torch.version.cuda,
            inference_device="cpu", gui=True, presets=True, da3_configuration=True,
            da3_parameters=da3_parameters, depthpro_import=True, da2_inference=True,
            stereo_inpainting=True, outputs=True, metadata=True, cache=True, offline=True)
    finally:
        socket.socket.connect, socket.create_connection = original_connect, original_create
