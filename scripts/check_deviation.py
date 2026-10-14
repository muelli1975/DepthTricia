"""CPU calibration of the actual stereo/inpainting renderer, before JPEG.

Requires prepared runtime and the two local stereo/inpainting checkpoints.
Flat depth endpoints isolate geometry; this is not a photo-quality benchmark.
"""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def check(threads=None):
    import torch
    from depthtricia.config import ProcessingConfig
    from depthtricia.downloads import verify_model
    from depthtricia.model_catalog import FILES
    from depthtricia.stereo_backend import StereoSession
    from depthtricia.stereo_geometry import iw3_parameters
    if threads is not None:
        torch.set_num_threads(threads)
    for key in ("warp", "inpaint"):
        verify_model(ROOT / "models", FILES[key])
    session = StereoSession(ProcessingConfig(ROOT, device="cpu"), torch.device("cpu"))
    results = []
    try:
        with torch.inference_mode():
            for label, width, height, depth_h, depth_w in (
                ("landscape", 1024, 256, 308, 1218),
                ("portrait", 256, 512, 1218, 602),
            ):
                image = torch.linspace(.1, .9, width)[None, None, None, :].expand(1, 3, height, width).contiguous()
                strength, convergence = iw3_parameters(width, (depth_h, depth_w), 15, 100)
                endpoints = []
                for z in (0., 1.):
                    depth = torch.full((1, 1, depth_h, depth_w), z)
                    left, right = session.model.infer(image, depth, divergence=strength,
                        convergence=convergence, synthetic_view="both", inner_dilation=0,
                        outer_dilation=0, max_width=None, enable_amp=False)
                    difference = (right - left)[0, 0, height//3:2*height//3, width//4:3*width//4]
                    endpoints.append(float((difference / (.8 / (width - 1))).median()))
                span = abs(endpoints[0] - endpoints[1])
                results.append(dict(case=label, width=width, target_permille=15,
                    target_px=width * .015, measured_span_px=span,
                    measured_span_permille=span / width * 1000))
    finally:
        session.close()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, help="Explicit CPU thread count for a reproducible test host")
    check(parser.parse_args().threads)
