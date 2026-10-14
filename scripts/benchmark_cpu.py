"""Developer CPU measurement through the unchanged production inference paths.

Workers run sequentially in
separate processes so each stage has its own peak resident-memory reading.
No output-image saving or metadata work is included in the measured times.
"""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def worker(args):
    import numpy as np
    import torch
    from depthtricia.config import DepthPreset, ProcessingConfig
    from depthtricia.depth_backend import DepthSession
    from depthtricia.downloads import verify_model
    from depthtricia.image_input import load_work_image
    from depthtricia.model_catalog import FILES
    from depthtricia.stereo_backend import StereoSession

    # Benchmark host only: match the explicit CPU quota, not an app default.
    torch.set_num_threads(args.threads)
    config = ProcessingConfig(ROOT, model_id=args.model, device='cpu',
                              target_height=args.height, preset=DepthPreset(args.resolution))
    keys = [args.model] if args.worker == 'depth' else ['warp', 'inpaint']
    for key in keys:
        verify_model(config.models_dir, FILES[key])
    rgb = load_work_image(args.input, args.height)
    peak = [None]
    try:
        start = time.perf_counter()
        session = (DepthSession(config, torch.device('cpu')) if args.worker == 'depth'
                   else StereoSession(config, torch.device('cpu')))
        load_seconds = time.perf_counter() - start
        params = sum(p.numel() for p in session.model.parameters())
        timings, inpaint_timings = [], []
        if args.worker == 'stereo':
            depth = np.load(args.depth_cache, allow_pickle=False)
            native_infer = session.model.model.infer
            inpaint_total = [0.0]
            def timed_infer(*positional, **keywords):
                start = time.perf_counter()
                try:
                    return native_infer(*positional, **keywords)
                finally:
                    inpaint_total[0] += time.perf_counter() - start
            session.model.model.infer = timed_infer
        for _ in range(args.runs):
            if args.worker == 'stereo':
                inpaint_total[0] = 0
            start = time.perf_counter()
            if args.worker == 'depth':
                depth = session.infer(rgb)
            else:
                left, right = session.render(rgb, depth)
                del left, right
            timings.append(time.perf_counter() - start)
            if args.worker == 'stereo':
                inpaint_timings.append(inpaint_total[0])
        if args.worker == 'depth':
            np.save(args.depth_cache, depth, allow_pickle=False)
        session.close()
    finally:
        try:
            import resource
            value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            peak[0] = value * (1 if sys.platform == 'darwin' else 1024) / 1_000_000
        except ImportError:
            pass  # Linux/macOS resident-memory reading; timings work on Windows too.
    return dict(stage=args.worker, model=args.model, resolution=args.resolution,
                image_size=[rgb.shape[1], rgb.shape[0]], depth_size=[depth.shape[1], depth.shape[0]],
                parameters=params, load_seconds=load_seconds, seconds=timings,
                median_seconds=statistics.median(timings),
                inpaint_seconds=inpaint_timings,
                inpaint_median_seconds=statistics.median(inpaint_timings) if inpaint_timings else None,
                peak_rss_mb=peak[0], threads=torch.get_num_threads(),
                torch=torch.__version__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--model', choices=['da2', 'da3'], required=True)
    parser.add_argument('--resolution', type=int, default=0)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--threads', type=int, default=8)
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--depth-cache', type=Path)
    parser.add_argument('--worker', choices=['depth', 'stereo'])
    args = parser.parse_args()
    if args.threads < 1 or args.runs < 1:
        parser.error('threads and runs must be positive')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if args.worker:
        result = worker(args)
    else:
        cache = args.report.with_suffix('.npy')
        result = dict(input=str(args.input), stages=[])
        for stage in ('depth', 'stereo'):
            report = args.report.with_name(args.report.stem + '_' + stage + '.json')
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', stage,
                       '--input', str(args.input), '--model', args.model,
                       '--resolution', str(args.resolution), '--height', str(args.height),
                       '--threads', str(args.threads), '--runs', str(args.runs),
                       '--depth-cache', str(cache), '--report', str(report)]
            subprocess.run(command, check=True)
            result['stages'].append(json.loads(report.read_text()))
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
