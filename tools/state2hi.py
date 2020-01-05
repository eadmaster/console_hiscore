#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# usage: state2hi "Super Mario Bros. (World).state"  [nes,smb]

import sys
import os

HISCORE_PATH="/usr/share/games/mame/plugins/console_hiscore/console_hiscore.dat"

GAME_NAME = os.path.splitext(os.path.basename(sys.argv[1]))[0]  # get basename without the extension

if len(sys.argv) > 2:  # TODO: check if invoked from shell -> > 3
	GAME_NAME = sys.argv[2]

	# check if system name was passed with softlist syntax
	argv2_splitted=sys.argv[2].split(",")
	if len(argv2_splitted) >= 2:
		SYSTEM = sys.argv[2].split(",")[0]
		GAME_NAME = sys.argv[2].split(",")[1]


statedata = open(sys.argv[1], 'rb').read()

# Nestopia
# MEMO: savestates are swappable between retroarch and vanilla Nestopia (just rename *.state -> *.nst)
if statedata[0:3] == b'NST':
	print("Nestopia state detected")
	SYSTEM = "nes"
	raw_memory = statedata[56:]  # skip 56 bytes header
# end of Nestopia

# Snes9x
elif statedata[0:9] == b'#!s9xsnp:':
	SYSTEM = "smc"
	raw_memory = statedata[68505:]  # v. 2002 / pocketsnes https://github.com/libretro/snes9x2002/blob/master/src/snapshot.c
# end of Snes9x

#elif statedata[0:3] == b'BST':
# TODO: bsnes

# Genesis-Plus-GX  https://github.com/ekeeke/Genesis-Plus-GX/blob/master/core/state.c
elif statedata[0:10] == b'GENPLUS-GX':
	print("GENPLUS-GX state detected")
	raw_memoryswapped = statedata[16:]  # TODO: cut end ram
	SYSTEM = "gen"
	# TODO: detect sms+gamegear
	#if SYSTEM in ["sms", "gamegear"]:
	#	raw_memory = statedata[16:0x200F]
	
	# 16-bit swapping  https://stackoverflow.com/questions/36096292/efficient-way-to-swap-bytes-in-python
	raw_memory = bytearray()
	for i in range(0, len(raw_memoryswapped), 2):
		raw_memory.append(raw_memoryswapped[i+1])
		raw_memory.append(raw_memoryswapped[i])
# end of Genesis-Plus-GX 

# TODO: Gambatte  https://github.com/libretro/gambatte-libretro/blob/master/libgambatte/src/statesaver.cpp
# not doable?

# TODO: MAME
# https://github.com/mamedev/mame/blob/master/src/emu/save.cpp
elif statedata[0:8] == b'MAMESAVE':
	print("MAME state detected")
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
	print("core unsupported")
	sys.exit(1)
	
# TODO: more cores

else:
	print("emulator not supported")
	sys.exit(1)


print("detected system: " + SYSTEM)
print("detected game: " + GAME_NAME)

hiscore_file = open(HISCORE_PATH)
hiscore_rows_to_process = []

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
		if not line_gamename == GAME_NAME + "." + SYSTEM:
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
			hiscore_rows_to_process.append(line.strip())
		# end while
	# end if
# end while

if len(hiscore_rows_to_process)==0:
	print("nothing found in hiscore.dat for current game")
	sys.exit(1)
# else

OUTPUT_PATH="./"
OUTFILE_PATH = OUTPUT_PATH + GAME_NAME + "." + SYSTEM +".hi"
#if SYSTEM == GAME_NAME:
#	# MAME hiscores
#	OUTFILE_PATH = OUTPUT_PATH + SYSTEM + ".hi"

outfile = open(OUTFILE_PATH, "wb")

print(OUTFILE_PATH + " created")

for row in hiscore_rows_to_process:
	splitted_row = row.split(",")
	cputag = splitted_row[0].split(":")[1]
	addresspace = splitted_row[1]
	if not addresspace=="program":
		print("unsupported: " + addresspace)
		sys.exit(1)
	address = int(splitted_row[2], base=16)
	length = int(splitted_row[3], base=16)
	start_byte = int(splitted_row[4], base=16)
	end_byte = int(splitted_row[5], base=16)

	if SYSTEM=="gen":
		# fix genesis address
		if address > 0xff0000:
			address -= 0xff0000
		# TODO: byte swap
		
	#print(address)
	outfile.write(raw_memory[address:address+length])
# end for

	

