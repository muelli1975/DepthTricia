from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image
from depthtricia.config import ProcessingConfig
from depthtricia.renderer import write_outputs
from depthtricia.output_writer import save_sbs_jpeg
from depthtricia.floating_window import apply_floating_window

def test_cross_export_keeps_finished_eyes_and_color(tmp_path):
    left = np.full((32,48,3), [220,30,20], np.uint8)
    right = np.full_like(left, [20,70,210])
    config = ProcessingConfig(tmp_path, gray_anaglyph=True, save_cross=True, float_left_permille=10)
    item = SimpleNamespace(sbs_path=tmp_path/'sbs.jpg', anaglyph_path=tmp_path/'anaglyph.jpg', cross_path=tmp_path/'cross.jpg')
    write_outputs(left, right, item, config, lambda *_:None)
    l,r = apply_floating_window(left,right,10,0,0,0)
    expected = tmp_path/'expected.jpg'
    save_sbs_jpeg(r,l,expected,config.jpeg_quality_sbs)
    assert expected.read_bytes() == item.cross_path.read_bytes()
    assert Image.open(item.cross_path).size == (96,32)
