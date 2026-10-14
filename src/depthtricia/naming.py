from __future__ import annotations


def format_number(value: float) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "p")


def build_suffix(
    deviation: float,
    window_position: float,
    window_back: float,
    float_left: float = 0.0,
    float_right: float = 0.0,
    float_top: float = 0.0,
    float_bottom: float = 0.0,
) -> str:
    parts = [
        f"d{format_number(deviation)}",
        f"w{format_number(window_position)}",
        f"o{format_number(window_back)}",
    ]
    for key, value in (
        ("fl", float_left), ("fr", float_right),
        ("ft", float_top), ("fb", float_bottom),
    ):
        if float(value) > 0.0:
            parts.append(f"{key}{format_number(value)}")
    return "_" + "_".join(parts)


def build_output_suffix(config) -> str:
    if not config.append_settings_to_filename:
        return ""
    from .model_catalog import MODEL_FILENAME_TAGS
    return "_" + MODEL_FILENAME_TAGS[config.model_id] + build_suffix(
        config.deviation_permille, config.window_position_percent,
        config.window_back_permille, config.float_left_permille,
        config.float_right_permille, config.float_top_permille,
        config.float_bottom_permille)

