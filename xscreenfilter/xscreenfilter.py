from typing import List, TypedDict, Dict, Tuple
from Xlib import display as dpy
from Xlib.ext import randr
import json
from os.path import expanduser
from .list_monitors import list_monitors

# October 2021 hotfix:
cache_file = expanduser('~/.cache/xscreenfilter.json')

GammaRGB = Tuple[float, float, float]


class DictCG(TypedDict):
    crtc: int
    gamma: GammaRGB


class DictCGBT(TypedDict):
    crtc: int
    gamma: Tuple[float, float, float]
    brightness: float
    temperature: float


# Randr functions


def xlib_monitors(disp: dpy.Display = None):  # based on refs 1 and 2
    disp = disp or dpy.Display()
    screen = disp.get_default_screen()
    info = disp.screen(screen)
    window = info.root
    res = randr.get_screen_resources(window)
    outputs: List[Tuple[int, str]] = []
    for output in res.outputs:
        params = disp.xrandr_get_output_info(output, res.config_timestamp)
        outputs.append((params.crtc, params.name))
    return outputs


def get_outputs(disp: dpy.Display = None):
    disp = disp or dpy.Display()
    try:
        outs = list_monitors()  # Hotfix
    except:
        outs = xlib_monitors()
    return {name: get_output(disp, crtc) for crtc, name in outs}


MAX = 65535.0  # grabbed from ref 1


def get_output(d: dpy.Display, crtc: int):
    cg = d.xrandr_get_crtc_gamma(crtc)
    cgd = {
        'red': cg.red[-1] / MAX if cg.red else -1,
        'green': cg.green[-1] / MAX if cg.green else -1,
        'blue': cg.blue[-1] / MAX if cg.blue else -1,
    }
    if min(cgd.values()) < 0:
        # Ugly fix: after october 2021, cg.blue and cg.green are empty :(
        # probably a bug in the Xlib library for Python
        keys = ['red', 'green', 'blue']
        try:
            with open(cache_file) as f:
                data = json.load(f)
            crtc_data = data[str(crtc)]
            cgd = {k: crtc_data[k] for k in keys}
        except:
            alt = max(cgd.values())
            alt = 1 if alt < 0 else alt
            cgd = {k: alt for k in keys}
    gamma = (
        round(cgd['red'], 3),
        round(cgd['green'], 3),
        round(cgd['blue'], 3),
    )
    return DictCG(crtc=crtc, gamma=gamma)


def ugly_randr_patch(disp: dpy.Display):
    # Ugly fix: after october 2021, the red, blue and green arguments where removed
    # it is a bug actually, because if they are not provided, the initializer of
    # SetCrtcGamma will complain

    from Xlib.ext.randr import SetCrtcGamma, extname

    def patched_set_crtc_gamma(self, crtc, size, **kwargs):
        return SetCrtcGamma(display=self.display,
                            opcode=self.display.get_extension_major(extname),
                            crtc=crtc, size=size, **kwargs)

    del disp.display_extension_methods['xrandr_set_crtc_gamma']
    disp.extension_add_method(
        'display',
        'xrandr_set_crtc_gamma',
        patched_set_crtc_gamma,
    )
    return


def set_gamma(disp: dpy.Display, crtc: int, gamma: GammaRGB):
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
        ugly_randr_patch(disp)
        disp.xrandr_set_crtc_gamma(crtc, n, **rgb)
    # Ugly cache fix
    try:
        with open(cache_file) as f:
            data = json.load(f)
        data[str(crtc)] = gamma
    except:
        data = {str(crtc): gamma}
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except:
        pass
    get_output(disp, crtc)
    return


# RGB vs brightness-temperature functions

RGB = [
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


def params_to_rgb(brightness: float, temperature: float) -> GammaRGB:
    n = len(RGB)
    i = min(int(temperature * (n - 1)), n - 2)
    disp = temperature * (n - 1) - i
    rgb = [RGB[i][c] * (1 - disp) + RGB[i + 1][c] * disp for c in range(3)]
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


def get_params(disp: dpy.Display, name: str):
    outs = get_outputs(disp)
    if name is None:
        outs = outs.values()
    else:
        outs = [v for k, v in outs.items() if k == name]
        assert outs, f'Screen "{name}" not found'
    return [(out, rgb_to_params(*out['gamma'])) for out in outs]


# User functions


def xset(abs_brightness=None, abs_temperature=None, delta_brightness=None,
         delta_temperature=None, name=None):
    disp = dpy.Display()
    ifnone = lambda val, alt: alt if val is None else val
    for out, (b, t) in get_params(disp, name):
        b = ifnone(abs_brightness, b * 100) / 100
        t = ifnone(abs_temperature, t * 100) / 100
        b += ifnone(delta_brightness, 0) / 100
        t += ifnone(delta_temperature, 0) / 100
        b = max(0, min(1, b))
        t = max(0, min(1, t))
        crtc = out['crtc']
        set_gamma(disp, crtc, params_to_rgb(b, t))
    return


def xget():
    outs = get_outputs()
    outs_cgbt: Dict[str, DictCGBT] = {}
    for key, out in outs.items():
        b, t = rgb_to_params(*out['gamma'])
        out_cgbt = DictCGBT(
            **out,
            brightness=b,
            temperature=t,
        )
        outs_cgbt[key] = out_cgbt
    return outs_cgbt
