from dataclasses import replace

import numpy as np
from PIL import Image
import pytest

from depthtricia.config import ProcessingConfig
from depthtricia.image_input import load_work_image
from depthtricia.naming import build_output_suffix
from depthtricia.output_writer import save_depth_png


def test_original_size_preserves_oriented_dimensions_while_default_limits_height(tmp_path):
    source = tmp_path / 'portrait.jpg'
    exif = Image.Exif()
    exif[274] = 6
    Image.new('RGB', (2300, 400), (50, 90, 130)).save(source, exif=exif)
    assert load_work_image(source, 2160).shape == (2160, 376, 3)
    assert load_work_image(source, 0).shape == (2300, 400, 3)
    assert Image.open(source).size == (2300, 400)


def test_depth_png_retains_resolution_16bit_range_and_leaves_float_cache_unchanged(tmp_path):
    depth = np.array([[0, .0001, .25], [.5, .9999, 1]], dtype=np.float32)
    original = depth.copy()
    output = tmp_path / 'depth_maps/scene_depth.png'
    save_depth_png(depth, output)
    with Image.open(output) as image:
        assert image.size == (3, 2)
        pixels = np.asarray(image)
    assert output.read_bytes()[24:26] == bytes([16, 0])  # PNG IHDR: 16-bit grayscale.
    assert pixels[0, 0] == 0 and pixels[-1, -1] == 65535
    assert np.max(np.abs(pixels.astype(np.float64) / 65535 - depth)) <= .501 / 65535
    assert np.array_equal(depth, original)
    assert not list(output.parent.glob('*.partial.png'))


@pytest.mark.parametrize('model,tag', [('da2', 'DA2Small'), ('da3', 'DA3MonoLarge'), ('depthpro', 'DepthPro')])
def test_optional_output_suffix_includes_model_and_existing_stereo_settings(tmp_path, model, tag):
    config = ProcessingConfig(tmp_path, model_id=model)
    assert build_output_suffix(config) == ''
    config = replace(config, append_settings_to_filename=True, float_left_permille=1.5)
    assert build_output_suffix(config) == '_' + tag + '_d15_w100_o0_fl1p5'
