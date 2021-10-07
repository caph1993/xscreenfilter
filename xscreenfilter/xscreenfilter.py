from Xlib import display as dpy
from Xlib.ext import randr


# Randr functions

def get_outputs(disp=None): # based on refs 1 and 2
    disp = disp or dpy.Display()
    screen = disp.get_default_screen()
    info = disp.screen(screen)
    window = info.root
    res = randr.get_screen_resources(window)
    outputs = {}
    for output in res.outputs:
        params = disp.xrandr_get_output_info(output, res.config_timestamp)
        if params.crtc:
            outputs[params.name] = get_output(disp, params.crtc)
    return outputs


MAX = 65535.0  # grabbed from ref 1


def get_output(d: dpy.Display, crtc):
    cg = d.xrandr_get_crtc_gamma(crtc)
    # Ugly fix: after october 2021, cg.blue and cg.green are empty :(
    # probably a bug in the Xlib library for Python
    print(cg.red[-10:])
    print(cg.blue[-10:])
    print(cg.green[-10:])
    alt = 1.0
    alt = raw_red = cg.red[-1] / MAX if cg.red else alt
    alt = raw_blue = cg.blue[-1] / MAX if cg.blue else alt
    alt = raw_green = cg.green[-1] / MAX if cg.green else alt
    gamma = (
        round(raw_red, 3),
        round(raw_green, 3),
        round(raw_blue, 3),
    )
    return dict(crtc=crtc, gamma=gamma)



def ugly_randr_patch(d):
    # Ugly fix: after october 2021, the red, blue and green arguments where removed
    # it is a bug actually, because if they are not provided, the initializer of
    # SetCrtcGamma will complain

    from Xlib.ext.randr import SetCrtcGamma, extname

    def patched_set_crtc_gamma(self, crtc, size, **kwargs):
        return SetCrtcGamma(display=self.display,
                            opcode=self.display.get_extension_major(extname),
                            crtc=crtc, size=size, **kwargs)

    del d.display_extension_methods['xrandr_set_crtc_gamma']
    d.extension_add_method('display', 'xrandr_set_crtc_gamma',
                           patched_set_crtc_gamma)
    return


def set_gamma(d: dpy.Display, output, gamma):
    crtc = output['crtc']
    n = d.xrandr_get_crtc_gamma_size(crtc).size
    data = [[int(MAX * i * v / (n - 1)) for i in range(n)] for v in gamma]
    rgb = {'red': data[0], 'green': data[1], 'blue': data[2]}
    try:
        d.xrandr_set_crtc_gamma(crtc, n, **rgb)
        use_patch = False
    except:
        use_patch = True
    if use_patch:
        ugly_randr_patch(d)
        d.xrandr_set_crtc_gamma(crtc, n, **rgb)
    output.update(**get_output(d, crtc))
    return


# RGB vs brightness-temperature functions

RGB = [
    [1.000,  0.323,  0.000],
    [1.000,  0.423,  0.086],
    [1.000,  0.543,  0.166],
    [1.000,  0.643,  0.288],
    [1.000,  0.719,  0.428],
    [1.000,  0.779,  0.546],
    [1.000,  0.828,  0.648],
    [1.000,  0.868,  0.736],
    [1.000,  0.901,  0.814],
    [1.000,  0.938,  0.881],
    [1.000,  0.971,  0.943],
    [1.000,  1.000,  1.000],
]


def params_to_rgb(brightness, temperature):
    n = len(RGB)
    i = min(int(temperature*(n-1)), n-2)
    disp = temperature*(n-1)-i
    rgb = [RGB[i][c]*(1-disp) + RGB[i+1][c]*disp for c in range(3)]
    rgb = [round(v*brightness,3) for v in rgb]
    return rgb


def rgb_to_params(red, green, blue):
    rgb = [red, green, blue]
    b = max(max(rgb), 1e-5)
    rgb = [v/b for v in rgb]
    def dist2(t):
        rgbt = params_to_rgb(1, t)
        return sum((b-a)**2 for a,b in zip(rgb, rgbt))
    tlo, thi, n = 0, 1, 10
    for repeat in range(3):
        trange = [tlo+(thi-tlo)*i/n for i in range(n+1)]
        tlo, thi = sorted(sorted(trange, key=dist2)[:2])
    b = round(b, 3)
    t = round((tlo+thi)/2, 3)
    return b, t
    

def get_params(disp, name):
    outs = get_outputs(disp)
    if name is None:
        outs = outs.values()
    else:
        outs = [v for k,v in outs.items() if k==name]
        assert outs, f'Screen "{name}" not found'
    return [(out, rgb_to_params(*out['gamma'])) for out in outs]


# User functions


def xset(
        abs_brightness=None, abs_temperature=None,
        delta_brightness=None, delta_temperature=None,
        name=None):
    disp = dpy.Display()
    ifnone = lambda val, alt: alt if val is None else val
    for out, (b, t) in get_params(disp, name):
        b = ifnone(abs_brightness, b*100)/100
        t = ifnone(abs_temperature, t*100)/100
        b += ifnone(delta_brightness, 0)/100
        t += ifnone(delta_temperature, 0)/100
        b = max(0, min(1, b))
        t = max(0, min(1, t))
        set_gamma(disp, out, params_to_rgb(b, t))
    return 


def xget():
    outs = get_outputs()
    for out in outs.values():
        b, t = rgb_to_params(*out['gamma'])
        out['brightness'] = b
        out['temperature'] = t
    return outs

