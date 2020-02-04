#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MEMO: RetroArch >= 1.8.5 is required
# usage: enable `network_cmd_enable` in retroarch, set HISCORE_PATH and HISCORE_DAT_PATH in state2hi.py or the environ

import sys
import os
import logging
import time
from io import BytesIO


HISCORE_PATH_USE_SUBDIRS=False

logging.getLogger().setLevel(logging.DEBUG)

from retroarchpythonapi import RetroArchPythonApi
retroarch = RetroArchPythonApi()

# path where .hi files will be loaded and saved
HISCORE_PATH = retroarch.get_config_param('savefile_directory')  # store hiscores in savefile_directory by default
#HISCORE_PATH = os.path.expanduser("~/.mame/hi")
if("HISCORE_PATH" in os.environ):
    HISCORE_PATH = os.environ['HISCORE_PATH']

hiscore_inited_in_ram = False
prev_content_name = None
hiscore_rows_to_process = []
hiscore_file_bytesio = BytesIO()
hiscore_file_path = ""


while True: 
	# wait for some content to be loaded
	while not (retroarch.is_alive() and retroarch.has_content()):
		time.sleep(5)
	
	curr_content_name = str(retroarch.get_content_name(), 'utf-8')
	if not curr_content_name:
		continue
	
	# detect game change
	if curr_content_name != prev_content_name:
		prev_content_name = curr_content_name
		
		hiscore_inited_in_ram = False
		
		# detect the system from the core name
		system = str(retroarch.get_system_id(), 'utf-8')
		if system == "Nestopia":
			system = "nes"
		elif system == "super_nes":
			system = "snes"
		elif system == "game_boy":
			system = "gameboy"  # TODO: also try "gbcolor"
		elif system == "mega_drive":
			system = "genesis"  # TODO: also try "megadriv", "mastersystem", "gamegear", "segacd"
		# TODO: more systems
		
		logging.debug("game was changed, read hiscore data for " + system + ", " + curr_content_name + "...")
		
		from state2hi import get_hiscore_rows_from_game
		# TODO: remove deps
		hiscore_rows_to_process = get_hiscore_rows_from_game(system, curr_content_name)
		if len(hiscore_rows_to_process)==0:
			logging.error("nothing found in hiscore.dat for current game")
			continue
		
		# try to read the .hi hiscore file
		hiscore_file_data = None
		if HISCORE_PATH_USE_SUBDIRS:
			hiscore_file_path = HISCORE_PATH + "/" + system + "/" + curr_content_name + ".hi"
		else:
			hiscore_file_path = HISCORE_PATH + "/" + curr_content_name + ".hi"
		
		try:
			hiscore_file = open(hiscore_file_path, 'rb')
			hiscore_file_data = hiscore_file.read()
			logging.info("read hiscore file: " + hiscore_file_path + " len: " + str(len(hiscore_file_data)))
			hiscore_file.close()
			hiscore_file_bytesio = BytesIO(hiscore_file_data)  # keep a copy in memory
		except:
			logging.info("hiscore file not found, will be created...")
			#logging.exception("")
	# end if game was changed
	
	curr_hiscore_ram_bytesio = BytesIO()  # read from live memory to here
	for row in hiscore_rows_to_process:
		logging.debug("processing: " + row)
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
		
		response_bytes = retroarch.read_core_ram(address, length)
		#logging.debug(len(response_bytes))
		#logging.debug(int(response_bytes[0], base=16))
		#logging.debug(start_byte)

		# 1st loop: check start_byte and end_byte, if the match the code and an hiscore file was read, init the memory
		if hiscore_file_bytesio.getbuffer().nbytes > 0 and hiscore_inited_in_ram == False and response_bytes and int(response_bytes[0], base=16) == start_byte and int(response_bytes[-1], base=16) == end_byte:
			logging.info("start_byte and end_byte matches, writing into core memory...")
			# write data from hiscore_file_bytesio buffer
			buf = hiscore_file_bytesio.read(length)
			if retroarch.write_core_ram(address, buf) == True:
				# successfull memory write
				curr_hiscore_ram_bytesio.write(buf)
				if row == hiscore_rows_to_process[-1]:
					# TODO: check if all the rows were written
					hiscore_inited_in_ram = True
					retroarch.show_msg("Hiscore loaded")
		elif response_bytes:
			# append read bytes to curr_hiscore_ram_bytesio
			for b in response_bytes:
				curr_hiscore_ram_bytesio.write(bytes([ int(b, base=16) ] ))
	# end for rows
	
	# check if hiscore data is changed
	curr_hiscore_ram_bytesio.flush()
	#print(curr_hiscore_ram_bytesio.getvalue())
	#print(hiscore_file_bytesio.getvalue())
	if curr_hiscore_ram_bytesio.getbuffer().nbytes > 0 and curr_hiscore_ram_bytesio.getvalue() != hiscore_file_bytesio.getvalue():
		# (over-)write to the hiscore file
		if HISCORE_PATH_USE_SUBDIRS and not os.path.exists(HISCORE_PATH + "/" + system):
			os.mkdir(HISCORE_PATH + "/" + system)
		if not os.path.isfile(HISCORE_PATH):
			# show msg only at the 1st save
			retroarch.show_msg("Hiscore file creates")
		hiscore_file = open(hiscore_file_path, 'wb') # write+binary mode
		hiscore_file.write(curr_hiscore_ram_bytesio.getvalue())
		hiscore_file.close()
		hiscore_file_bytesio = curr_hiscore_ram_bytesio  # keep the reference in memory
		logging.info("written hiscore file " + hiscore_file_path)
		#NO? retroarch.show_msg("Hiscore saved")  # too many alerts?
	else:
		logging.debug("hiscore data unchanged in memory, nothing to save")
	
	# sleep to avoid sending too many read/write commands
	time.sleep(5)
# end while retroarch is running

