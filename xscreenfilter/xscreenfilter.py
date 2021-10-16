from typing import List, Optional, TypedDict, Dict, Tuple
from Xlib import display as dpy
from Xlib.ext import randr
import json
from os.path import expanduser
from .list_monitors import list_monitors

# Types

TupleRGB = Tuple[float, float, float]


class DictRGB(TypedDict):
    red: float
    green: float
    blue: float


class DictOutput(TypedDict):
    name: str
    crtc: int
    gamma: TupleRGB


class DictOutputBT(TypedDict):
    name: str
    crtc: int
    gamma: TupleRGB
    brightness: float
    temperature: float


# October 2021 hotfix: Json cache file


class CacheFile:
    '''
    Format: {"display_name": TupleRGB, "display_name": TupleRGB, ...}
    '''

    filename = expanduser('~/.cache/xscreenfilter.json')

    def load(self, name: str, alternative: float) -> DictRGB:
        if alternative <= 0 or alternative > 1:
            alternative = 1.0
        keys = ['red', 'green', 'blue']
        try:
            with open(self.filename) as f:
                data = json.load(f)
            crtc_data: DictRGB = data[name]
            cgd: DictRGB = {k: crtc_data[k] for k in keys}  # type: ignore
        except:
            # Set red = green = blue = aletrnative
            cgd: DictRGB = {k: alternative for k in keys}  # type: ignore
            gamma = (cgd['red'], cgd['green'], cgd['blue'])
            self.save(name, gamma)
        return cgd

    def save(self, name: str, gamma: TupleRGB):
        try:
            with open(self.filename) as f:
                data = json.load(f)
            data[name] = gamma
        except:
            data = {name: gamma}
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f)
        except:
            pass
        return


# Global variables
disp = dpy.Display()

cache_file = CacheFile()

MAX = 65535.0  # grabbed from ref 1

RGB_temperature = [
    [1.000, 0.323, 0.000],
    [1.000, 0.423, 0.086],
    [1.000, 0.543, 0.166],
    [1.000, 0.643, 0.288],
    [1.000, 0.719, 0.428],
    [1.000, 0.779, 0.546],
    [1.000, 0.828, 0.648],
    [1.000, 0.868, 0.736],
    [1.000, 0.901, 0.814],
    [1.000, 0.938, 0.881],
    [1.000, 0.971, 0.943],
    [1.000, 1.000, 1.000],
]

# Randr functions


def xlib_monitors():  # based on refs 1 and 2
    screen = disp.get_default_screen()
    info = disp.screen(screen)
    window = info.root
    res = randr.get_screen_resources(window)
    outputs: List[Tuple[int, str]] = []
    for output in res.outputs:
        params = disp.xrandr_get_output_info(output, res.config_timestamp)
        outputs.append((params.crtc, params.name))
    return outputs


def get_outputs():
    try:
        outs = list_monitors()  # Hotfix
    except:
        outs = xlib_monitors()
    return {name: get_output(crtc, name) for crtc, name in outs}


def get_output(crtc: int, name: str):
    cgd = _get_output(crtc=crtc)
    values: List[float] = list(cgd.values())  # type: ignore
    if min(values) < 0:
        # Ugly fix: after october 2021, cg.blue and cg.green are empty :(
        # probably a bug in the Xlib library for Python
        cgd = cache_file.load(name, max(values))
    gamma: TupleRGB = (
        round(cgd['red'], 3),
        round(cgd['green'], 3),
        round(cgd['blue'], 3),
    )
    return DictOutput(crtc=crtc, gamma=gamma, name=name)


def _get_output(crtc: int):
    cg = disp.xrandr_get_crtc_gamma(crtc)
    cgd: DictRGB = {
        'red': cg.red[-1] / MAX if cg.red else -1.0,
        'green': cg.green[-1] / MAX if cg.green else -1.0,
        'blue': cg.blue[-1] / MAX if cg.blue else -1.0,
    }
    return cgd


class Ugly_randr_patch():
    # Ugly fix: after october 2021, the red, blue and green arguments where removed
    # it is a bug actually, because if they are not provided, the initializer of
    # SetCrtcGamma will complain

    def __init__(self):
        from Xlib.ext.randr import SetCrtcGamma, extname

        def patched_set_crtc_gamma(self, crtc, size, **kwargs):
            return SetCrtcGamma(
                display=self.display,
                opcode=self.display.get_extension_major(extname), crtc=crtc,
                size=size, **kwargs)

        self.original = disp.display_extension_methods['xrandr_set_crtc_gamma']
        self.patched = patched_set_crtc_gamma

    def __enter__(self):
        del disp.display_extension_methods['xrandr_set_crtc_gamma']
        disp.extension_add_method(
            'display',
            'xrandr_set_crtc_gamma',
            self.patched,
        )

    def __exit__(self, *_):
        del disp.display_extension_methods['xrandr_set_crtc_gamma']
        disp.extension_add_method(
            'display',
            'xrandr_set_crtc_gamma',
            self.original,
        )


def set_gamma(crtc: int, gamma: TupleRGB, name: str):
    n = disp.xrandr_get_crtc_gamma_size(crtc).size
    n = max(n, 2)
    data = [[int(MAX * i * v / (n - 1)) for i in range(n)] for v in gamma]
    rgb = {'red': data[0], 'green': data[1], 'blue': data[2]}
    try:
        disp.xrandr_set_crtc_gamma(crtc, n, **rgb)
        use_patch = False
    except:
        use_patch = True
    if use_patch:
        with Ugly_randr_patch():
            disp.xrandr_set_crtc_gamma(crtc, n, **rgb)
    cache_file.save(name, gamma)
    get_output(crtc, name)
    return


# RGB vs brightness-temperature functions


def params_to_rgb(brightness: float, temperature: float) -> TupleRGB:
    RGB = RGB_temperature
    n = len(RGB)
    i = min(int(temperature * (n - 1)), n - 2)
    x = temperature * (n - 1) - i
    rgb = [RGB[i][c] * (1 - x) + RGB[i + 1][c] * x for c in range(3)]
    rgb = tuple([round(v * brightness, 3) for v in rgb])
    return rgb  # type:ignore


def rgb_to_params(red: float, green: float, blue: float):
    rgb = [red, green, blue]
    b = max(max(rgb), 1e-5)
    rgb = [v / b for v in rgb]

    def dist2(t):
        rgbt = params_to_rgb(1, t)
        return sum((b - a)**2 for a, b in zip(rgb, rgbt))

    tlo, thi, n = 0, 1, 10
    for repeat in range(3):
        trange = [tlo + (thi - tlo) * i / n for i in range(n + 1)]
        tlo, thi = sorted(sorted(trange, key=dist2)[:2])
    b = round(b, 3)
    t = round((tlo + thi) / 2, 3)
    return b, t


def get_params(name: Optional[str]):
    outs = get_outputs()
    if name is None:
        outs = outs.values()
    else:
        outs = [v for k, v in outs.items() if k == name]
        assert outs, f'Screen "{name}" not found'
    return [(out, rgb_to_params(*out['gamma'])) for out in outs]


# User functions


def xset(abs_brightness=None, abs_temperature=None, delta_brightness=None,
         delta_temperature=None, name=None):
    ifnone = lambda val, alt: alt if val is None else val
    for out, (b, t) in get_params(name):
        b = ifnone(abs_brightness, b * 100) / 100
        t = ifnone(abs_temperature, t * 100) / 100
        b += ifnone(delta_brightness, 0) / 100
        t += ifnone(delta_temperature, 0) / 100
        b = max(0, min(1, b))
        t = max(0, min(1, t))
        crtc = out['crtc']
        name = out['name']
        set_gamma(crtc, params_to_rgb(b, t), name)
    return


def xget():
    outs = get_outputs()
    outs_cgbt: Dict[str, DictOutputBT] = {}
    for key, out in outs.items():
        b, t = rgb_to_params(*out['gamma'])
        out_cgbt = DictOutputBT(
            **out,
            brightness=b,
            temperature=t,
        )
        outs_cgbt[key] = out_cgbt
    return outs_cgbt
