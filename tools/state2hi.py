#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# usage: state2hi "Super Mario Bros. (World).state"  [nes,smb]

import sys
import os
import logging

logging.getLogger().setLevel(logging.DEBUG)

HISCORE_DAT_PATH="/usr/share/games/mame/plugins/console_hiscore/console_hiscore.dat"
if("HISCORE_DAT_PATH" in os.environ):
    HISCORE_DAT_PATH = os.environ['HISCORE_DAT_PATH']

def get_raw_memory_from_statedata(statedata):
	raw_memory = None
	SYSTEM = None
	EMU = None
	
	# switch on file header

	# compressed savestate detection
	if statedata.startswith(b'PK'):
		# inmemory zip file extraction
		from zipfile import ZipFile
		from io import BytesIO
		zipdata = BytesIO()
		zipdata.write(statedata)
		input_zip_file = ZipFile(zipdata)
		if(len(input_zip_file.filelist)>1):
			logging.warning("more than 1 file in the compressed archive, using the 1st only: ")
		statefile = input_zip_file.open(input_zip_file.filelist[0])
		statedata = statefile.read()
	# end if

	# Nestopia
	# MEMO: savestates are swappable between retroarch and vanilla Nestopia (just rename *.state -> *.nst)
	if statedata[0:3] == b'NST':
		SYSTEM = "nes"
		EMU = "nestopia"
		raw_memory = statedata[0x38:]  # skip 56 bytes header
	# end of Nestopia

	# FCEUx  https://github.com/TASVideos/fceux/blob/master/src/state.cpp
	#elif statedata.startswith(b'FCSX'):
	# MEMO: feat. zlib compression

	# FCEUmm  https://github.com/libretro/libretro-fceumm/blob/master/src/state.c
	elif statedata.startswith(b'FCS\xFF'):
		logging.warning("FCEU support is still WIP")
		SYSTEM = "nes"
		EMU = "fceu"
		raw_memory = statedata[0x5D:]  # 2FIX: sometimes 0x56, 0x57
	# end of FCEU

	# Gambatte  https://github.com/libretro/gambatte-libretro/blob/master/libgambatte/src/statesaver.cpp
	#print(statedata[0:16])
	#print(len(statedata[0:16]))
	#print(len(b'\x00\x01\x00\x00\x00\x61\x00\x00\x00\x01\x00\x62\x00\x00\x00\x01'))
	elif statedata.startswith(b'\x00\x01\x00\x00\x00\x61\x00\x00\x00\x01\x00\x62\x00\x00\x00\x01'):
		logging.warning("Gambatte support is still WIP")
		SYSTEM = "gameboy"
		EMU = "gambatte"
		# TODO: "gbcolor"
		raw_memory = statedata  # no header to skip?
		# TODO: test with games different from tetris
	# end of Gambatte

	# Snes9x latest  https://github.com/snes9xgit/snes9x/blob/master/snapshot.cpp
	elif statedata.startswith(b'#!s9xsnp:0011'):
		SYSTEM = "snes"
		EMU = "snes9x"
		raw_memory = statedata[0x10B99:]  # system RAM starts after the "RAM:------:" string

	elif statedata.startswith(b'#!s9xsnp:0010'):
		# UNTESTED
		SYSTEM = "snes"
		EMU = "snes9x2018"
		raw_memory = statedata[0x10B96:]  # system RAM starts after the "RAM:------:" string

	elif statedata.startswith(b'#!s9xsnp:0006'):
		# UNTESTED
		SYSTEM = "snes"
		EMU = "snes9x2010"
		raw_memory = statedata[0x10B89:]  # system RAM starts after the "RAM:------:" string

	# Snes9x2002 / pocketsnes  https://github.com/libretro/snes9x2002/blob/master/src/snapshot.c
	elif statedata.startswith(b'#!snes9x:0001'):
		SYSTEM = "snes"
		EMU = "snes9x2002"
		raw_memory = statedata[0x10C64:]  # system RAM starts after the "RAM:------:" string
	# end of Snes9x

	# TODO: ZSNES https://github.com/ericpearson/zsnes/blob/cport/src/zstate.c
	# elif statedata.startswith(b'#!snes9x:0001'):
	# 	SYSTEM = "snes"
	# 	EMU = "zsnes"
	# 	raw_memory = statedata[0x10C64:]
	# end of Snes9x

	# bsnes  https://github.com/byuu/bsnes/blob/master/bsnes/sfc/system/serialization.cpp
	elif statedata.startswith(b'42\x53\x54\x31\x0F\x00\x00\x00\x70\x4C\x87\x10\x50\x65\x72\x66\x6F\x72\x6D\x61\x6E\x63\x65'):  # BST1....pL..Performance
	#elif statedata[0x15:0x19] == b'BST1':  # old compressed saves?
	#elif statedata.startswith(b'BST1'):
		logging.warning("bsnes support is still WIP")
		SYSTEM = "snes"
		EMU = "bsnes"
		raw_memory = statedata[0x21C:]
	# end of bsnes

	# Genesis-Plus-GX  https://github.com/ekeeke/Genesis-Plus-GX/blob/master/core/state.c
	elif statedata.startswith(b'GENPLUS-GX'):
		logging.warning("GENPLUS-GX support is still WIP")
		raw_memoryswapped = statedata[16:]  # TODO: cut end ram
		SYSTEM = "genesis"
		EMU = "genplus"
		# TODO: detect sms+gamegear
		#if SYSTEM in ["sms", "gamegear"]:
		#	raw_memory = statedata[16:0x200F]
		
		# 16-bit swapping  https://stackoverflow.com/questions/36096292/efficient-way-to-swap-bytes-in-python
		raw_memory = bytearray()
		for i in range(0, len(raw_memoryswapped), 2):
			raw_memory.append(raw_memoryswapped[i+1])
			raw_memory.append(raw_memoryswapped[i])
	# end of Genesis-Plus-GX 

	# TODO: MAME https://github.com/mamedev/mame/blob/master/src/emu/save.cpp
	elif statedata.startswith(b'MAMESAVE'):
		#print("format ver: " + str(statedata[8]))
		#print("flags: " + str(statedata[9])) # TODO: parse
		#print("game name: " + str(statedata[0x0A:0x1B], 'utf-8'))
		SYSTEM = (statedata[0x0A:0x1B]).decode().replace('\x00', '')
		GAME_NAME = SYSTEM
		#print("signature: " + str(statedata[0x1C:0x1F]))

		savegamedata_compressed = statedata[0x20:]
		# MEMO: Data is always written as native-endian.

		import zlib
		raw_memoryswapped = zlib.decompress(savegamedata_compressed)
		
		# flip data  https://stackoverflow.com/questions/14543065/byte-reverse-ab-cd-to-cd-ab-with-python
		#raw_memory = bytearray(raw_memory_flipped)
		#raw_memory.reverse()
		
		#def swap16(x):
		#	return int.from_bytes(x.to_bytes(2, byteorder='little'), byteorder='big', signed=False)
			
		#def swap32(x):
		#	return int.from_bytes(x.to_bytes(4, byteorder='little'), byteorder='big', signed=False)
		
		# inplace 16bit swapping  https://stackoverflow.com/questions/36096292/efficient-way-to-swap-bytes-in-python
		# raw_memory = bytearray()
		# for i in range(0, len(raw_memoryswapped), 2):
			# raw_memory.append(raw_memoryswapped[i+1])
			# raw_memory.append(raw_memoryswapped[i])
		
		#print("savegamedata decompressed size: " + str(len(savegamedata)))

		#OUTFILE_PATH=GAME_NAME + ".sta.raw"
		#outfile = open(OUTFILE_PATH, "wb")
		#outfile.write(raw_memoryswapped)
		#sys.exit(1)

		# TODO: need to extract system memory+addresses:  
		# "the emulator takes a snapshot of the current configuration of all the memory addresses currently in use by the game. This snapshot is unique and loading it back up is just a matter of forcing the memory back to those addresses." https://www.reddit.com/r/emulation/comments/34pk7q/how_do_save_states_work/
		# https://wiki.mamedev.org/index.php/Save_State_Fundamentals
		# TODO: raw_memory = raw_memory[???]
		logging.error("MAME is unsupported, please check the mame_mkhiscoredebugscript.py")
		return None
		
	# TODO: more cores

	if raw_memory == None:
		logging.error("emulator not supported")
		return None
	else:
		return raw_memory, SYSTEM, EMU
# end of get_raw_memory_from_statedata


def get_hiscore_rows_from_game(SYSTEM, GAME_NAME):
	hiscore_file = open(HISCORE_DAT_PATH)
	rows = []
	while(True):
		line = hiscore_file.readline()
		if not line:
			# EOF
			break 
		elif line.strip() == "":
			# line was empty
			continue
				 
		line = line.strip()
		if line.startswith(";"):
			continue
		if line.endswith(":"):
			# check if game matches
			line_gamename = line.split(':')[0]
			if not line_gamename == SYSTEM + "," + GAME_NAME:
				continue
			# else reads the hiscore rows
			while(True):
				line = hiscore_file.readline()
				if line.strip() == "":
					# end of codes
					break
				if not line.startswith("@"):
					# comments?
					continue
				# else
				rows.append(line.strip())
			# end while
		# end if
	# end while
	return rows
# end of get_hiscore_rows_from_game


if __name__ == '__main__':
	SYSTEM = ""
	EMU = ""

	if len(sys.argv) > 2:  # TODO: check if invoked from shell -> > 3
		GAME_NAME = sys.argv[2]
		#GAME_NAME = os.path.splitext(os.path.basename(sys.argv[1]))[0]  # get basename without the extension

		# check if system name was passed with softlist syntax
		argv2_splitted=sys.argv[2].split(",")
		if len(argv2_splitted) >= 2:
			SYSTEM = sys.argv[2].split(",")[0]
			GAME_NAME = sys.argv[2].split(",")[1]

	statedata = open(sys.argv[1], 'rb').read()

	raw_memory, SYSTEM, EMU = get_raw_memory_from_statedata(statedata)

	logging.info("detected system: " + SYSTEM)
	logging.info("detected emulator: " + EMU)
	logging.info("detected game: " + GAME_NAME)

	#OUTFILE_PATH=GAME_NAME + ".raw"
	#outfile = open(OUTFILE_PATH, "wb")
	#outfile.write(raw_memory)
	
	hiscore_rows_to_process = get_hiscore_rows_from_game(SYSTEM, GAME_NAME)
	if len(hiscore_rows_to_process)==0:
		logging.error("nothing found in hiscore.dat for current game")
		sys.exit(1)
	# else

	OUTPUT_PATH="./"
	OUTFILE_PATH = OUTPUT_PATH + GAME_NAME +".hi"
	#if SYSTEM == GAME_NAME:
	#	# MAME hiscores
	#	OUTFILE_PATH = OUTPUT_PATH + SYSTEM + ".hi"

	outfile = open(OUTFILE_PATH, "wb")

	logging.info(OUTFILE_PATH + " created")

	for row in hiscore_rows_to_process:
		splitted_row = row.split(",")
		cputag = splitted_row[0].split(":")[1]
		addresspace = splitted_row[1]
		if not addresspace=="program":
			logging.error("unsupported: " + addresspace)
			sys.exit(1)
		address = int(splitted_row[2], base=16)
		length = int(splitted_row[3], base=16)
		start_byte = int(splitted_row[4], base=16)
		end_byte = int(splitted_row[5], base=16)

		if EMU=="genplus":
			# fix genesis address
			if address > 0xff0000:
				address -= 0xff0000
			# TODO: byte swap
		elif EMU=="gambatte":
			address -= 0x7728
			
		#print(address)
		outfile.write(raw_memory[address:address+length])
	# end for

