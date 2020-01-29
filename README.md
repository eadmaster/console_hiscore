This project aims to bring hiscore saving support for emulators of old videogames consoles (just like the [MAME hiscore plugin](https://highscore.mameworld.info)).

Currently we have:
 - MAME `console_hiscore` plugin forked from the [official one](https://github.com/mamedev/mame/tree/master/plugins/hiscore) with support for cart and cdrom images;
 - `console_hiscore.dat` file with some code entries ([contributions are welcomed](https://github.com/eadmaster/console_hiscore/wiki/Games-that-need-hiscore-codes));
 - a [Retroarch hiscore companion script](tools/retroarch_hiscore_companion.py) that loads/saves hiscores via [network commands](https://docs.libretro.com/development/retroarch/network-control-interface/).
 - a [python script](tools/state2hi.py) to extract hiscore data from emulator savestates.
 
Check the wiki for more details.
