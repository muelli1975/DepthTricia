"""Complete inference profiles, including migration of pre-release settings."""
from dataclasses import asdict

from .config import BUILTIN_PRESETS, InferencePreset


def restore_presets(settings):
    model = settings.get("model_id", "da3")
    device = settings.get("device", "auto")
    from .model_catalog import DEPTH_MODELS
    model = model if isinstance(model, str) and model in DEPTH_MODELS else "da3"
    device = device if isinstance(device, str) and device in {"auto", "cpu", "cuda"} else "auto"
    own = {}
    raw = settings.get("depth_presets", {})
    for name, values in (raw.items() if isinstance(raw, dict) else []):
        if not isinstance(name, str) or not isinstance(values, dict):
            continue
        try:
            profile = InferencePreset(**{"model_id": model, "device": device, **values})
            profile.validate()
            own[name] = asdict(profile)
        except (TypeError, ValueError):
            continue
    active = settings.get("active_preset", "")
    if isinstance(active, str) and active in own:
        return own, active, None, InferencePreset(**own[active])
    builtin = settings.get("builtin_preset", "standard")
    builtin = builtin if isinstance(builtin, str) and builtin in BUILTIN_PRESETS else "standard"
    profile = BUILTIN_PRESETS[builtin]
    # An old model/device selection must not disappear when profiles gain them.
    if not settings.get("preset_schema") and ("model_id" in settings or "device" in settings):
        legacy = InferencePreset(model, device, profile.resolution, profile.edge_x, profile.edge_y)
        if legacy != profile:
            name = "Previous settings"
            number = 2
            while name in own:
                name = f"Previous settings ({number})"
                number += 1
            own[name] = asdict(legacy)
            return own, name, None, legacy
    return own, "", builtin, profile


def preset_choices(tr, own):
    choices = {tr("preset.default" if key == "standard" else "preset." + key): ("builtin", key)
               for key in BUILTIN_PRESETS}
    for name in own:
        label = name
        while label in choices or label in {tr("preset.create"), tr("preset.edit")}:
            label += tr("preset.own_suffix")
        choices[label] = ("own", name)
    return choices
