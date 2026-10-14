import time
from .anaglyph import make_anaglyph
from .floating_window import apply_floating_window
from .output_writer import save_anaglyph_jpeg, save_sbs_jpeg


def write_outputs(left, right, item, config, progress):
    left, right = apply_floating_window(left, right, config.float_left_permille,
                                      config.float_right_permille, config.float_top_permille,
                                      config.float_bottom_permille)
    progress("save_sbs", 0.60)
    save_sbs_jpeg(left, right, item.sbs_path, config.jpeg_quality_sbs)
    progress("anaglyph", 0.72)
    start = time.perf_counter()
    anaglyph = make_anaglyph(left, right, gray=config.gray_anaglyph)
    seconds = time.perf_counter() - start
    progress("save_anaglyph", 0.90)
    save_anaglyph_jpeg(anaglyph, item.anaglyph_path, config.jpeg_quality_anaglyph)
    return seconds
