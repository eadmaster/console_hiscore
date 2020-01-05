This project aims to bring hiscore saving support for emulators of old videogames consoles (just like the [MAME hiscore plugin](https://highscore.mameworld.info)).

Currently provides:
 - MAME `console_hiscore` plugin forked from the [official one](https://github.com/mamedev/mame/tree/master/plugins/hiscore) with support for cart images;
 - `console_hiscore.dat` file with some code entries (contributions are welcomed!);
 - a [crappy python script](tools/state2hi.py) to extract hiscore data from emulator savestates (currently supports only: Nestopia, GENPLUS-GX, still WIP)
 
Check the wiki for more details.
