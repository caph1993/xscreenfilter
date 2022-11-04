
# xscreenfilter

Protect your eyes. Manage your screen brightness and temperature in **linux**.

This script lets you apply screen filters that modify your screens' apparent brightness and [temperature](https://en.wikipedia.org/wiki/Color_temperature).

This script does not change the actual hardware brightness, also called backlight. For backlight, I recommend the `brightnessctl` command.


## Installation

Either [download](https://raw.githubusercontent.com/caph1993/xscreenfilter/master/dist/xscreenfilter) a precompiled binary or compile the `xscreenfilter.c` file by simply running:

```sh
sudo apt install libxrandr-dev libx11-dev
curl https://raw.githubusercontent.com/caph1993/xscreenfilter/master/xscreenfilter.c > xscreenfilter.c
gcc -I/usr/local/include -L/usr/local/lib xscreenfilter.c -o xscreenfilter -lXrandr -lX11
# Optional (clean)
sudo apt remove libxrandr-dev libx11-dev
```

Tested in Linux Mint 21 on October 2022.

## How to use?

Place the file in `~/.local/bin` or `/usr/local/bin`, and add global hotkeys for these two commands:

 - `xscreenfilter -350 -0.05` (darker and warmer, better for the eyes)
 - `xscreenfilter +350 +0.05` (lighter and cooler).


**Command line usage**. Usage by examples:

 - Run `./xscreenfilter 4500 0.9` to set temperature to 4500K and software brightness to 0.9.
 - Run `./xscreenfilter -1500 +0.0` to decrease current temperature by 1500K and maintain brightness at its current level.
 - Run `./xscreenfilter 4500 +0.1` to set temperature to 4500 and increase brightness by 0.1.
 - Run `./xscreenfilter` to set temperature to 6500K and brightness to 1.0 (default values).


## Motivation of this script

 - We spend many hours on the screen.
 - Screens are too bright, even on 1% backlight.
 - `xrandr` supports brightness but not temperature: there is a `--gamma` option but colors look very strange if you use it.
 - `redshift` supports setting both, but not reading, increasing or decreasing. It is meant for automated use only, making things darker at night. In my opinion, it is more practical to let the user change it directly, because if the window is closed during the day or the lights are on during the night, the automated system stops being useful. Furthermore, `redshift` has tons of dependencies and uses your location by default. In my opinion, it is too complex for such a simple task.
 - `sct` is great, it was just missing the ability to increase or decrease.

Credits to:
 - https://flak.tedunangst.com/post/sct-set-color-temperature
 - https://github.com/mgudemann/sct