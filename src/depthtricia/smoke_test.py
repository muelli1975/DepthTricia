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
        from .runtime import prepare_imports
        from .gui_check import check
        gui_report = check(app_dir)
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
        # Real shipped checkpoints, float ramps, landscape and portrait.
        from dataclasses import replace
        from .stereo_backend import StereoSession
        stereo = StereoSession(config, torch.device('cpu'))
        backshift_checks = []
        try:
            with torch.inference_mode():
                for height, width, depth_h, depth_w in ((128, 320, 140, 350), (256, 128, 280, 140)):
                    ramp = torch.linspace(.2, .8, width).reshape(1, 1, 1, width).expand(1, 3, height, width).contiguous()
                    endpoint_separations = []
                    for endpoint in (0., 1.):
                        depth = torch.full((1, 1, depth_h, depth_w), endpoint)
                        stereo.config = config
                        base_left, base_right = stereo._infer_pair(ramp, depth)
                        stereo.config = replace(config, window_back_permille=10)
                        left, right = stereo._infer_pair(ramp, depth)
                        center = (..., slice(height//3, 2*height//3), slice(width//4, 3*width//4))
                        slope = .6 / (width - 1)
                        added = float(((left - right - base_left + base_right)[center] / slope).median())
                        if abs(added - width * .01) > .5:
                            raise RuntimeError(f'Scene setback has wrong direction or amount: {added}')
                        if left[..., -1].min() < .01 or right[..., 0].min() < .01:
                            raise RuntimeError('Scene setback left black output borders')
                        endpoint_separations.append(float(((left - right)[center] / slope).median()))
                        backshift_checks.append(dict(width=width, endpoint=endpoint, added_px=added, expected_added_px=width * .01))
                    if abs(endpoint_separations[0] - endpoint_separations[1] - width * .015) > .5:
                        raise RuntimeError('Scene setback changed the deviation span')
        finally:
            stereo.close()
        return dict(torch=torch.__version__, cuda_runtime=torch.version.cuda,
            inference_device="cpu", gui=True, presets=True, preset_model_device=True, gui_layout=gui_report, da3_configuration=True,
            da3_parameters=da3_parameters, depthpro_import=True, depthpro_weights=True, da2_inference=True,
            stereo_inpainting=True, outputs=True, depth_png=True, original_size=True,
            model_filename=True, metadata=True, cache=True, offline=True,
            window_backshift=True, backshift_checks=backshift_checks)
    finally:
        socket.socket.connect, socket.create_connection = original_connect, original_create

