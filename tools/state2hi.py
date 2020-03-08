#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# usage: state2hi "Super Mario Bros. (World).state"  [nes,smb]

import sys
import os
import logging

DEBUG=True
if DEBUG:
	logging.getLogger().setLevel(logging.DEBUG)
else:
	logging.getLogger().setLevel(logging.INFO)
	
HISCORE_DAT_PATH="/usr/share/games/mame/plugins/console_hiscore/console_hiscore.dat"
if("HISCORE_DAT_PATH" in os.environ):
    HISCORE_DAT_PATH = os.environ['HISCORE_DAT_PATH']

def get_raw_memory_from_statedata(statedata):
	"""
	return a tuple: raw_memory (bytes buffer), candidate systems (list), emulator (str)
	"""
	
	raw_memory = None
	candidate_systems = []
	emulator = None
	
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
		emulator = "nestopia"
		candidate_systems = [ "nes", "famicom", "fds", "nespal" ]
		raw_memory = statedata[0x38:]  # skip 56 bytes header
	# end of Nestopia

	# FCEUx  https://github.com/TASVideos/fceux/blob/master/src/state.cpp
	#elif statedata.startswith(b'FCSX'):
	# MEMO: feat. zlib compression

	# FCEUmm  https://github.com/libretro/libretro-fceumm/blob/master/src/state.c
	elif statedata.startswith(b'FCS'):
		logging.warning("FCEU support is still WIP")
		emulator = "fceu"
		candidate_systems = [ "nes", "famicom", "fds", "nespal" ]
		#raw_memory = statedata[0x5D:]  # 2FIX: sometimes 0x56, 0x57
		raw_memory_start_offset = statedata.find(b"RAM")
		if raw_memory_start_offset == -1:
			logging.error("Invalid FCEU save state")
			return None, None, None
		# else
		raw_memory_start_offset += 8
		raw_memory = statedata[raw_memory_start_offset:]
	# end of FCEU

	# Gambatte  https://github.com/libretro/gambatte-libretro/blob/master/libgambatte/src/statesaver.cpp
	#print(statedata[0:16])
	#print(len(statedata[0:16]))
	#print(len(b'\x00\x01\x00\x00\x00\x61\x00\x00\x00\x01\x00\x62\x00\x00\x00\x01'))
	elif statedata.startswith(b'\x00\x01\x00\x00\x00\x61\x00\x00\x00\x01\x00\x62\x00\x00\x00\x01'):
		logging.warning("Gambatte support is still WIP")
		emulator = "gambatte"
		candidate_systems = [ "gameboy", "gbcolor", "supergb" ]
		# TODO: detect/exclude "gbcolor"?
		raw_memory = statedata  # no header to skip?
		# TODO: test with games different from tetris
	# end of Gambatte

	# Snes9x latest  https://github.com/snes9xgit/snes9x/blob/master/snapshot.cpp
	elif statedata.startswith(b'#!s9xsnp:0011'):
		emulator = "snes9x"
		candidate_systems = [ "snes", "snespal" ]
		raw_memory = statedata[0x10B99:]  # system RAM starts after the "RAM:------:" string

	elif statedata.startswith(b'#!s9xsnp:0010'):
		emulator = "snes9x2018"
		candidate_systems = [ "snes", "snespal" ]
		raw_memory = statedata[0x10B96:]  # system RAM starts after the "RAM:------:" string

	elif statedata.startswith(b'#!s9xsnp:0006'):
		emulator = "snes9x2010"
		candidate_systems = [ "snes", "snespal" ]
		raw_memory = statedata[0x10B89:]  # system RAM starts after the "RAM:------:" string

	# Snes9x2002 / pocketsnes  https://github.com/libretro/snes9x2002/blob/master/src/snapshot.c
	elif statedata.startswith(b'#!snes9x:0001'):
		emulator = "snes9x2002"
		candidate_systems = [ "snes", "snespal" ]
		raw_memory = statedata[0x10C64:]  # system RAM starts after the "RAM:------:" string
	# end of Snes9x

	# TODO: ZSNES https://github.com/ericpearson/zsnes/blob/cport/src/zstate.c
	# elif statedata.startswith(b'#!snes9x:0001'):
	# 	emulator = "zsnes"
	# 	candidate_systems = [ "snes", "snespal" ]
	# 	raw_memory = statedata[0x10C64:]
	# end of Snes9x

	# bsnes  https://github.com/byuu/bsnes/blob/master/bsnes/sfc/system/serialization.cpp
	#elif statedata.startswith(b'42\x53\x54\x31\x0F\x00\x00\x00\x70\x4C\x87\x10\x50\x65\x72\x66\x6F\x72\x6D\x61\x6E\x63\x65'):  # BST1....pL..Performance
	#elif statedata[0x15:0x19] == b'BST1':  # old compressed saves?
	elif statedata.startswith(b'BST1'):
		logging.warning("bsnes support is still WIP")
		emulator = "bsnes"
		candidate_systems = [ "snes", "snespal" ]
		if statedata[0xC:0x17] == b'Performance':
			# old ver.
			raw_memory = statedata[0x21C:]
		elif statedata[0x8:0xA] == b'11':
			# latest ver
			raw_memory = statedata[0x284:]
		# TODO: more versions
		print(statedata[0x8:0xA])
	# end of bsnes

	# Genesis-Plus-GX  https://github.com/ekeeke/Genesis-Plus-GX/blob/master/core/state.c
	elif statedata.startswith(b'GENPLUS-GX'):
		logging.warning("GENPLUS-GX support is still WIP")
		emulator = "genplus"
		candidate_systems = [ "genesis", "megadrij", "megadriv", "sms", "smsj", "smspal", "gamegear", "gamegeaj", "segacd" ]
		raw_memoryswapped = statedata[16:]  # TODO: cut end ram
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
		#GAME_NAME = SYSTEM
		#print("signature: " + str(statedata[0x1C:0x1F]))
		emulator = "mame"
		candidate_systems = [ SYSTEM ]

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
		return None, None, None
		
	# TODO: more cores

	if emulator == None or raw_memory == None:
		return None, None, None
	else:
		return raw_memory, candidate_systems, emulator
# end of get_raw_memory_from_statedata


def get_hiscore_rows_from_game(candidate_systems, GAME_NAME):
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
			for SYSTEM in candidate_systems:
				if line_gamename == SYSTEM + "," + GAME_NAME:
					# read the hiscore rows
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
					# end while (hiscore rows)
				# end if (game matches)
			# end for candidate_systems
		# end if line.endswith(":")
	# end while hiscore_file lines
	return rows
# end of get_hiscore_rows_from_game


if __name__ == '__main__':
	candidate_systems = []
	EMU = ""

	if len(sys.argv) == 2:
		input_state_filepath = sys.argv[1]
	if len(sys.argv) == 3:
		input_state_filepath = sys.argv[2]
		#GAME_NAME = os.path.splitext(os.path.basename(sys.argv[1]))[0]  # get basename without the extension

	# check if system name was passed with softlist syntax
	argv_splitted=input_state_filepath.split(",")
	if len(argv_splitted) >= 2:
		candidate_systems = [ input_state_filepath.split(",")[0] ]
		GAME_NAME = input_state_filepath.split(",")[1]
	else:
		GAME_NAME = os.path.splitext(os.path.basename(input_state_filepath))[0]  # extract the filename, strip the extension

	statedata = open(input_state_filepath, 'rb').read()

	raw_memory, candidate_systems, EMU = get_raw_memory_from_statedata(statedata)

	if not EMU:
		logging.error("emulator not supported")
		sys.exit(1)
		
	logging.info("detected system(s): " + str(candidate_systems))
	logging.info("detected emulator: " + EMU)
	logging.info("detected game: " + GAME_NAME)

	if DEBUG:
		OUTFILE_PATH=GAME_NAME + ".raw"
		outfile = open(OUTFILE_PATH, "wb")
		outfile.write(raw_memory)
	
	hiscore_rows_to_process = get_hiscore_rows_from_game(candidate_systems, GAME_NAME)
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

