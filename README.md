This project aims to bring hiscore saving support for emulators of old videogames consoles (just like the [MAME hiscore plugin](https://highscore.mameworld.info)).

Currently we have:
 - MAME `console_hiscore` plugin forked from the [official one](https://github.com/mamedev/mame/tree/master/plugins/hiscore) with support for cart and cdrom images;
 - `console_hiscore.dat` file with some code entries (contributions are welcomed since i am very slow at finding ram addresses, just send me a pull request);
 - a [crappy python script](tools/state2hi.py) to extract hiscore data from emulator savestates (currently supports only: Nestopia, GENPLUS-GX, still WIP)
 
Check the wiki for more details.
