#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# usage: enable `network_cmd_enable` in retroarch, set the HISCORE_DAT_PATH in state2hi.py

HISCORE_PATH="."  # path where .hi files will be loaded and saved

import sys
import os
import logging
import time
from io import BytesIO

logging.getLogger().setLevel(logging.DEBUG)

from retroarchpythonapi import RetroArchPythonApi
retroarch = RetroArchPythonApi()

hiscore_inited_in_ram = False
prev_content_name = None
hiscore_rows_to_process = []
hiscore_file_bytesio = BytesIO()
hiscore_file_path = ""


#print("Waiting for Retroarch connection...")
while retroarch.is_alive(): 
	time.sleep(5)
	
	curr_content_name = str(retroarch.get_content_name(), 'utf-8')
	if not curr_content_name:
		continue
	
	# detect game change
	if curr_content_name != prev_content_name:
		logging.debug("game was changed, read hiscore data again for " + curr_content_name + "...")
		prev_content_name = curr_content_name
		
		hiscore_inited_in_ram = False
		
		# detect the system from the core name
		
		system = str(retroarch.get_system_id(), 'utf-8')
		if system == "Nestopia":
			system = "nes"
		# TODO: more systems
		
		from state2hi import get_hiscore_rows_from_game
		# TODO: remove deps
		hiscore_rows_to_process = get_hiscore_rows_from_game(system, curr_content_name)
		if len(hiscore_rows_to_process)==0:
			logging.error("nothing found in hiscore.dat for current game")
			continue
		
		# try to read the .hi hiscore file
		hiscore_file_data = None
		hiscore_file_path = HISCORE_PATH + "/" + system + "/" + curr_content_name + ".hi"
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
		#logging.debug(response_bytes)
			
		# check start_byte and end_byte, if the match the code and an hiscore file was read, init the memory
		if hiscore_file_bytesio.getbuffer().nbytes > 0 and hiscore_inited_in_ram == False and response_bytes and int(response_bytes[0]) == start_byte and int(response_bytes[-1]) == end_byte:
			logging.info("start_byte and end_byte matches, writing into core memory...")
			# write data from hiscore_file_bytesio buffer
			buf = hiscore_file_bytesio.read(length)
			retroarch.write_core_ram(address, buf)
			if row == hiscore_rows_to_process[-1]:
				# TODO: check if all the rows were written
				hiscore_inited_in_ram = True
		elif response_bytes:
			# append read bytes to curr_hiscore_ram_bytesio
			for b in response_bytes:
				curr_hiscore_ram_bytesio.write(bytes([ int(b, base=16) ] ))
	# end for rows
	
	# check if hiscore data is changed
	curr_hiscore_ram_bytesio.flush()
	if curr_hiscore_ram_bytesio.getbuffer().nbytes > 0 and curr_hiscore_ram_bytesio.getvalue() != hiscore_file_bytesio.getvalue():
		# (over-)write to the hiscore file
		if not os.path.exists(HISCORE_PATH + "/" + system):
			os.mkdir(HISCORE_PATH + "/" + system)
		hiscore_file = open(hiscore_file_path, 'wb') # write+binary mode
		hiscore_file.write(curr_hiscore_ram_bytesio.getvalue())
		hiscore_file.close()
		hiscore_file_bytesio = curr_hiscore_ram_bytesio  # keep the reference in memory
		logging.info("written hiscore file " + hiscore_file_path)
	else:
		logging.debug("hiscore data unchanged in memory, nothing to save")
# end while retroarch is running

