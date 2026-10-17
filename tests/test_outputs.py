from dataclasses import replace

import numpy as np
from PIL import Image
import pytest

from depthtricia.config import ProcessingConfig, DepthPreset
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


@pytest.mark.parametrize('mode', ['RGBA', 'LA', 'palette_index', 'palette_alpha', 'RGB_key', 'L_key'])
def test_transparent_png_uses_white_background_without_changing_source(tmp_path, mode):
    source = tmp_path / 'transparent.png'
    options = {}
    if mode == 'RGBA':
        image = Image.new('RGBA', (3, 1))
        image.putdata([(255, 0, 0, 0), (0, 0, 255, 128), (0, 255, 0, 255)])
        expected = [[255, 255, 255], [127, 127, 255], [0, 255, 0]]
    elif mode == 'LA':
        image = Image.new('LA', (3, 1))
        image.putdata([(0, 0), (0, 128), (80, 255)])
        expected = [[255, 255, 255], [127, 127, 127], [80, 80, 80]]
    elif mode.startswith('palette'):
        image = Image.new('P', (3, 1))
        image.putpalette([255, 0, 0, 0, 0, 255, 0, 255, 0] + [0] * 759)
        image.putdata([0, 1, 2])
        options['transparency'] = 0 if mode == 'palette_index' else bytes([0, 128, 255])
        expected = [[255, 255, 255], [0, 0, 255] if mode == 'palette_index' else [127, 127, 255], [0, 255, 0]]
    elif mode == 'RGB_key':
        image = Image.new('RGB', (2, 1))
        image.putdata([(255, 0, 0), (0, 255, 0)])
        options['transparency'] = (255, 0, 0)
        expected = [[255, 255, 255], [0, 255, 0]]
    else:
        image = Image.new('L', (2, 1))
        image.putdata([0, 80])
        options['transparency'] = 0
        expected = [[255, 255, 255], [80, 80, 80]]
    image.save(source, **options)
    original = source.read_bytes()
    assert np.array_equal(load_work_image(source, 0), [expected])
    assert source.read_bytes() == original


@pytest.mark.parametrize('mode,extension', [('RGB', '.png'), ('L', '.png'), ('RGB', '.jpg')])
def test_opaque_images_retain_previous_pixels(tmp_path, mode, extension):
    source = tmp_path / ('opaque' + extension)
    image = Image.new(mode, (7, 5), (25, 90, 160) if mode == 'RGB' else 75)
    image.save(source)
    with Image.open(source) as saved:
        expected = np.asarray(saved.convert('RGB'))
    assert np.array_equal(load_work_image(source, 0), expected)


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
def test_optional_output_suffix_includes_model_resolution_and_existing_stereo_settings(tmp_path, model, tag):
    config = ProcessingConfig(tmp_path, model_id=model)
    assert build_output_suffix(config) == ''
    config = replace(config, append_settings_to_filename=True, float_left_permille=1.5)
    resolution = 1536 if model == 'depthpro' else 1218
    assert build_output_suffix(config) == f'_{tag}_r{resolution}_d15_w100_o0_fl1p5'


@pytest.mark.parametrize('model,selected,expected', [
    ('da2', 0, 'DA2Small_r518'),
    ('da3', 0, 'DA3MonoLarge_r504'),
    ('da3', 2048, 'DA3MonoLarge_r2048'),
    ('da2', 1344, 'DA2Small_r1344'),
    ('depthpro', 0, 'DepthPro_r1536'),
    ('depthpro', 2048, 'DepthPro_r1536'),
])
def test_settings_filename_uses_selected_or_model_standard_resolution(tmp_path, model, selected, expected):
    config = ProcessingConfig(tmp_path, model_id=model,
        preset=DepthPreset(resolution=selected), append_settings_to_filename=True)
    suffix = build_output_suffix(config)
    for ending in ('sbs.jpg', 'anaglyph.jpg', 'depth.png'):
        assert f'scene{suffix}_{ending}' == f'scene_{expected}_d15_w100_o0_{ending}'
    assert build_output_suffix(replace(config, append_settings_to_filename=False)) == ''
