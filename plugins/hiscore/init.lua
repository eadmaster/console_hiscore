-- hiscore.lua
-- by borgar@borgar.net & eadmaster, WTFPL license
--
-- This uses MAME's built-in Lua scripting to implment
-- high-score saving with hiscore.dat infom just as older
-- builds did in the past.
--
local exports = {}
exports.name = "hiscore"
exports.version = "1.1.0"
exports.description = "Hiscore"
exports.license = "WTFPL license"
exports.author = { name = "borgar@borgar.net & eadmaster" }
local hiscore = exports

local hiscore_plugin_path = ""

function hiscore.set_folder(path)
	hiscore_plugin_path = path
end

function hiscore.startplugin()

	local hiscoredata_path = "hiscore.dat";
	local hiscore_path = "hi";
	local config_path = lfs.env_replace(manager:options().entries.inipath:value():match("[^;]+") .. "/hiscore.ini");

	local current_checksum = 0;
	local default_checksum = 0;

	local config_read = false;
	local scores_have_been_read = false;
	local mem_check_passed = false;
	local found_hiscore_entry = false;
	local timed_save = true;
	local delaytime = 0;

	local positions = {};
	-- Configuration file will be searched in the first path defined
	-- in mame inipath option.
	local function read_config()
	  if config_read then return true end;
	  local file = io.open( config_path, "r" );
	  if file then
		file:close()
		emu.print_verbose( "hiscore: config found" );
		local _conf = {}
		for line in io.lines(config_path) do
		  token, value = string.match(line, '([^ ]+) +([^ ]+)');
		  if token ~= nil and token ~= '' then
			_conf[token] = value;
		  end
		end
		hiscore_path = lfs.env_replace(_conf["hi_path"] or hiscore_path);
		timed_save = _conf["only_save_at_exit"] ~= "1"
		-- hiscoredata_path = _conf["dat_path"]; -- don't know if I should do it, but wathever
		return true
	  end
	  return false
	end

	local function parse_table ( dsting )
	  local _table = {};
	  for line in string.gmatch(dsting, '([^\n]+)') do
		local delay = line:match('^@delay=([.%d]*)')
		if delay and #delay > 0 then
			delaytime = emu.time() + tonumber(delay)
		else
			local cpu, mem;
			local cputag, space, offs, len, chk_st, chk_ed, fill = string.match(line, '^@([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),?(%x?%x?)');
			cpu = manager:machine().devices[cputag];
			if not cpu then
				error(cputag .. " device not found")
			end
			local rgnname, rgntype = space:match("([^/]*)/?([^/]*)")
			if rgntype == "share" then
				mem = manager:machine():memory().shares[rgnname]
			else
				mem = cpu.spaces[space]
			end
			if not mem then
				error(space .. " space not found")
			end
			_table[ #_table + 1 ] = {
				mem = mem,
				addr = tonumber(offs, 16),
				size = tonumber(len, 16),
				c_start = tonumber(chk_st, 16),
				c_end = tonumber(chk_ed, 16),
				fill = tonumber(fill, 16)
			};
		end
	  end
	  return _table;
	end


	local function read_hiscore_dat (hiscoredata_path)
	  -- emu.print_verbose( "hiscore_plugin_path: " .. hiscore_plugin_path );
	  local file = io.open( hiscore_plugin_path .. "/" .. hiscoredata_path, "r" );
	  if file == nil then
		-- file not found
		emu.print_verbose( "hiscore file not found: " .. hiscoredata_path );
		return ""
	  end
	  local rm_match;
	  local rm_match_crc = 0;
	  if emu.softname() ~= "" then
		local soft = emu.softname():match("([^:]*)$")
		rm_match = emu.romname() .. ',' .. soft .. ':';
	  elseif manager:machine().images["cart"] and manager:machine().images["cart"]:filename() ~= nil then
		local basename = string.gsub(manager:machine().images["cart"]:filename(), "(.*/)(.*)", "%2");
		local filename = string.gsub(basename, "(.*)(%..*)", "%1");   -- strip the extension (e.g. ".nes")
		rm_match = emu.romname() .. "," .. filename .. ':';
		rm_match_crc = emu.romname() .. ",crc32=" .. string.format("%x", manager:machine().images["cart"]:crc()) .. ':';
	  elseif manager:machine().images["cdrom"] and manager:machine().images["cdrom"]:filename() ~= nil then
		local basename = string.gsub(manager:machine().images["cdrom"]:filename(), "(.*/)(.*)", "%2");
		local filename = string.gsub(basename, "(.*)(%..*)", "%1");   -- strip the extension (e.g. ".cue")
		rm_match = emu.romname() .. "," .. filename .. ':';
		--rm_match_crc = string.format("%x", manager:machine().images["cdrom"]:crc()) .. ':';  -- always 0 with cdrom media?
	  else
		rm_match = emu.romname() .. ':';
	  end
	  local cluster = "";
	  local current_is_match = false;
	  if file then
		repeat
		  line = file:read("*l");
		  if line then
			-- remove comments
			line = line:gsub( '[ \t\r\n]*;.+$', '' );
			-- handle lines
			if string.find(line, '^@') then -- data line
			  if current_is_match then
				cluster = cluster .. "\n" .. line;
			  end
			elseif string.find(line, rm_match) then --- match this game
			  current_is_match = true;
			elseif line == rm_match_crc then --- match this game crc
			  current_is_match = true;
			elseif string.find(line, '^.+:') then --- some game
			  if current_is_match and string.len(cluster) > 0 then
				break; -- we're done
			  end
			else --- empty line or garbage
			  -- noop
			end
		  end
		until not line;
		file:close();
	  end
	  return cluster;
	end


	local function check_mem ( posdata )
	  if #posdata < 1 then
		return false;
	  end
	  for ri,row in ipairs(posdata) do
		-- must pass mem check
		if row["c_start"] ~= row["mem"]:read_u8(row["addr"]) then
		  return false;
		end
		if row["c_end"] ~= row["mem"]:read_u8(row["addr"]+row["size"]-1) then
		  return false;
		end
	  end
	  return true;
	end


	local function get_file_name ()
	  local r;
	  if emu.softname() ~= "" then
		local soft = emu.softname():match("([^:]*)$")
		r = hiscore_path .. '/' .. emu.romname() .. '/' .. soft .. ".hi";
	  elseif manager:machine().images["cart"] and manager:machine().images["cart"]:filename() ~= nil then
		local basename = string.gsub(manager:machine().images["cart"]:filename(), "(.*/)(.*)", "%2")
		local filename = string.gsub(basename, "(.*)(%..*)", "%1");   -- strip the extension (e.g. ".nes")
		r = hiscore_path .. '/' .. emu.romname() .. '/' .. filename .. ".hi";
	  elseif manager:machine().images["cdrom"] and manager:machine().images["cdrom"]:filename() ~= nil then
		local basename = string.gsub(manager:machine().images["cdrom"]:filename(), "(.*/)(.*)", "%2");
		local filename = string.gsub(basename, "(.*)(%..*)", "%1");   -- strip the media extension (e.g. ".cue")
		r = hiscore_path .. '/' .. emu.romname() .. '/' .. filename .. ".hi";
	  else
		-- arcade games
		r = hiscore_path .. '/' .. emu.romname() .. ".hi";
	  end
	  return r;
	end


	local function write_scores ( posdata )
	  emu.print_verbose("hiscore: write_scores")
	  local output = io.open(get_file_name(), "wb");
	  if not output then
		-- attempt to create the directory, and try again
		lfs.mkdir( hiscore_path );
		lfs.mkdir( hiscore_path .. '/' .. emu.romname() );
		output = io.open(get_file_name(), "wb");
	  end
	  emu.print_verbose("hiscore: write_scores output")
	  if output then
		for ri,row in ipairs(posdata) do
		  t = {};
		  for i=0,row["size"]-1 do
			t[i+1] = row["mem"]:read_u8(row["addr"] + i)
		  end
		  output:write(string.char(table.unpack(t)));
		end
		output:close();
	  end
	  emu.print_verbose("hiscore: write_scores end")
	end


	local function read_scores ( posdata )
	  local input = io.open(get_file_name(), "rb");
	  if input then
		for ri,row in ipairs(posdata) do
		  local str = input:read(row["size"]);
		  for i=0,row["size"]-1 do
			local b = str:sub(i+1,i+1):byte();
			row["mem"]:write_u8( row["addr"] + i, b );
		  end
		end
		input:close();
		return true;
	  end
	  return false;
	end


	local function check_scores ( posdata )
	  local r = 0;
	  for ri,row in ipairs(posdata) do
		for i=0,row["size"]-1 do
			r = r + row["mem"]:read_u8( row["addr"] + i );
		end
	  end
	  return r;
	end


	local function init ()
	  if not scores_have_been_read then
		if (delaytime <= emu.time()) and check_mem( positions ) then
		  default_checksum = check_scores( positions );
		  if read_scores( positions ) then
			emu.print_verbose( "hiscore: scores read OK" );
		  else
			-- likely there simply isn't a .hi file around yet
			emu.print_verbose( "hiscore: scores read FAIL" );
		  end
		  scores_have_been_read = true;
		  current_checksum = check_scores( positions );
		  mem_check_passed = true;
		else
		  -- memory check can fail while the game is still warming up
		  -- TODO: only allow it to fail N many times
		end
	  end
	end


	local last_write_time = -10;
	local function tick ()
	  -- set up scores if they have been
	  init();
	  -- only allow save check to run when
	  if mem_check_passed and timed_save then
		-- The reason for this complicated mess is that
		-- MAME does expose a hook for "exit". Once it does,
		-- this should obviously just be done when the emulator
		-- shuts down (or reboots).
		local checksum = check_scores( positions );
		if checksum ~= current_checksum and checksum ~= default_checksum then
		  -- 5 sec grace time so we don't clobber io and cause
		  -- latency. This would be bad as it would only ever happen
		  -- to players currently reaching a new highscore
		  if emu.time() > last_write_time + 5 then
			write_scores( positions );
			current_checksum = checksum;
			last_write_time = emu.time();
			-- emu.print_verbose( "SAVE SCORES EVENT!", last_write_time );
		  end
		end
	  end
	end

	local function reset()
	  -- the notifier will still be attached even if the running game has no hiscore.dat entry
	  if mem_check_passed and found_hiscore_entry then
		local checksum = check_scores(positions)
		if checksum ~= current_checksum and checksum ~= default_checksum then
		  write_scores(positions)
		end
	  end
	  found_hiscore_entry = false
	  mem_check_passed = false
	  scores_have_been_read = false;
	end

	emu.register_start(function()
		found_hiscore_entry = false
		mem_check_passed = false
		scores_have_been_read = false;
		last_write_time = -10
		emu.print_verbose("Starting " .. emu.gamename())
		config_read = read_config();
		local dat = read_hiscore_dat("hiscore.dat")
		if dat and dat == "" then
			-- nothing found, try in console_hiscore.dat instead
			dat = read_hiscore_dat("console_hiscore.dat")
		end
		if dat and dat ~= "" then
			emu.print_verbose( "hiscore: found hiscore.dat entry for " .. emu.romname() );
			res, positions = pcall(parse_table, dat);
			if not res then
				emu.print_error("hiscore: hiscore.dat parse error " .. positions);
				return;
			end
			for i, row in pairs(positions) do
				if row.fill then
					for i=0,row["size"]-1 do
						row["mem"]:write_u8(row["addr"] + i, row.fill)
					end
				end
			end
			found_hiscore_entry = true
		end
	end)
	emu.register_frame(function()
		if found_hiscore_entry then
			tick()
		end
	end)
	emu.register_stop(function()
		reset()
	end)
	emu.register_prestart(function()
		reset()
	end)
end

return exports
