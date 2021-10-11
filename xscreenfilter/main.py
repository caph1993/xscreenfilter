'''
xscreenfilter - Manage screen brightness and temperature through python

Author: Carlos Pinzón «caph1993@gmail.com»
Date: 2021


Documentation for xlib and randr is scarse. These were my sources:
    Ref 1 (stc.c)
        https://flak.tedunangst.com/post/sct-set-color-temperature
    Ref 2 (Xlib example).
        https://stackoverflow.com/questions/8705814
    For self exploring:
        d = dpy.Display()
        print(d.display_extension_methods.keys())

'''
try:
    import Xlib
except ImportError:
    print('Error:\n  import Xlib failed\n')
    print('Suggestions for fixing the problem:')
    print('  pip3 install xlib')
    print('OR')
    print('  sudo apt install python3-xlib')
    exit(1)

import sys, json, time
from .xscreenfilter import xset, xget

# User functions
VERSION = '0.1.6'
USAGE = f'xscreenfilter v{VERSION}\n' + """
Arguments:
    d - demo:
        run a small demo of different combinations
        of brightnesses and temperatures.
    
    s - screen [screen_name]:
        Apply the effects only to a specific screen.
        All available screens are affected if unspecified.
    
    l - list:
        list all available screens and their current values.
        JSON format is used for software compatibility.
        
    b - brightness [+num | -num | num] :
        Increase, decrease or set software brightness.
        100 is the maximum and the default.
        50 is comfortable.
        0 is the completely dark. Use responsibly.
    
    t - temperature [+num | -num | num] :
        Increase, decrease or set software temperature.
        100 is the maximum and the default.
        50 is comfortable and redish/yellowish.
        0 is very redish.
    
    c - combined [+num | -num | num] :
        applies the same change to brightness and temperature

    r - restore
        same as --combined 100. Removes all screen filters
    
    h - help:
        print this message
    
    v - version:
        print version
    

Usgae examples:
    python3 -m xscreenfilter --list
    python3 -m xscreenfilter --demo
    python3 -m xscreenfilter --temperature -10
    python3 -m xscreenfilter --brightness -5 --temperature +10 --screen eDP-1
    python3 -m xscreenfilter -t 50 -b -10 -l
    python3 -m xscreenfilter --restore
    python3 -m xscreenfilter -c +10
""".strip()


def main():
    run(sys.argv[1:])


def run(args):
    a = d = l = b = ib = t = it = name = None
    try:
        assert args, 'No arguments provided'
        args_iter = iter(args)
        for a in args_iter:
            if a == '--list' or a == '-l':
                l = True
            elif a == '--demo' or a == '-d':
                d = True
            elif a == '--brightness' or a == '-b':
                b, ib = parse_num(next(args_iter))
            elif a == '--temperature' or a == '-t':
                t, it = parse_num(next(args_iter))
            elif a == '--combined' or a == '-c':
                b, ib = t, it = parse_num(next(args_iter))
            elif a == '--restore' or a == '-r':
                b = t = 100
            elif a == '--screen' or a == '-s':
                name = next(args_iter)
            elif a == '--help' or a == '-h':
                return print(USAGE)
            elif a == '--version' or a == '-v':
                return print(VERSION)
            else:
                raise Exception(f'argument {a} not understood')
    except Exception as e:
        print(USAGE)
        print('------\nError parsing arguments:')
        if isinstance(e, StopIteration):
            print(f'  Expected argument after {a}')
        else:
            print(f'  {e}')
        return
    if d:
        xdemo()
    if any(x != None for x in [b, ib, t, it]):
        xset(abs_brightness=b, abs_temperature=t, delta_brightness=ib,
             delta_temperature=it, name=name)
    if l:
        print(json.dumps(xget(), indent='  '))
    return


def parse_num(s):
    sign = int(s.startswith('+')) - int(s.startswith('-'))
    value = float(s[abs(sign):])
    return (value, None) if sign == 0 else (None, sign * value)


def xdemo():
    print('Running demo...')
    for db, dt in [(20, 20), (-10, 0), (0, -12), (10, 0), (0, 12)]:
        for i in range(5):
            start = time.time()
            xset(delta_brightness=db, delta_temperature=dt)
            time.sleep(max(0, 0.05 - (time.time() - start)))
    return


if __name__ == '__main__':
    main()
