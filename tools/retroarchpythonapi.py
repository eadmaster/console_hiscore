
"""Retroarch Python API
This is a Python API for the RetroArch /
libretro Libraries for Console Emulators
Target:
Create an easy to use API to implement it in your own UI
Derived from  https://github.com/merlink01/RetroArchPythonAPI/
added python3 support and made network-based  https://github.com/recalbox/recalbox-os/wiki/RetroArch-Network-Commands-(EN)
"""

import os
import time
import logging
import socket

__version__ = 0.2
__copyright__ = 'GPL V2'

#NETWORK_SLEEP_TIME=0.1


class RetroArchPythonApi(object):

    """Usage:
    from retroarchpythonapi import RetroArchPythonApi
    api = RetroArchPythonApi()
    
    #NOT SUPPORTED: api.start(<Game Path>,<Libretro Plugin Path>)
    api.toggle_pause()
    api.save_state()
    api.load_state()
    api.read_core_ram(0x7df, 4)  # read 4 bytes from address 7df
    api.write_core_ram(0x7df, [0x00, 0x00, 0x00, 0x00])  # write 4 bytes set to 0 from address 7df
    api.reset()
    api.quit()
    
    methods to read current status:
    api.is_paused()
    api.is_running()
    api.is_alive()
    api.get_system_id()
    api.get_content_name()
    api.get_content_crc32_hash()
    """
    

    _socket = None
    _socket_ipaddr = "127.0.0.1"
    _socket_portnum = 55355

    rom_path = None
    _fullscreen = None


    def __init__(self, ipaddr="127.0.0.1", portnum=55355):

        # Logging
        self.logger = logging.getLogger('RetroArchPythonApi')

        # Settings
        self.settings = {}
        # TODO: read retroarch settings

        # Pathes
        self.pathes = {}
        # TODO: self.pathes['settings'] = "$HOME/.config/retroarch.cfg"

        # RetroArch Config File
        #configfile = os.path.join(settings_path, 'retroarch.cfg')
        #self.pathes['configfile'] = configfile
        
        # initialize a socket, think of it as a cable  
        # SOCK_DGRAM specifies that this is UDP
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            #s.bind((ipaddr, portnum))
            #s.setblocking(0)  # set receive non-blocking.
        except socket.error:  
            self.logger.error('failed to create UDP socket with Retroarch')
            logging.exception('')
            sys.exit(1)
        else:
            logging.info('Retroarch UDP socket connected')
        
        # save ipaddr and portnum for later use
        self._socket_ipaddr = ipaddr
        self._socket_portnum = portnum

        self.logger.info('Starting Retroarch Python API (Version:%s)' % __version__)


    def _get_status(self):

        """ checks if Retroarch is alive"""

        try:
            self._socket.sendto(b'GET_STATUS\n', (self._socket_ipaddr, self._socket_portnum))
            response_str, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
            return response_str.rstrip()
        except:
            logging.exception('')
            return ""
            
    def is_alive(self):
        """ returns True if the Retroarch is running and has the network interface active """
        status_str = self._get_status()
        if status_str == "":
            return False
        else:
            return True
    
    def is_running(self):
        """ returns True if the Retroarch has some content loaded (paused or not)"""
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        if splitted_status_str[0].split(b" ")[1] == b'CONTENTLESS':
            return False
        else:
            return True
    
    def is_paused(self):
        """ returns True if the content is paused """
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        if splitted_status_str[0].split(b" ")[1] == b'PAUSED':
            return True
        else:
            return False
        

    def get_system_id(self):
        """ returns current system_id (e.g. 'nes') or the core name (e.g. 'Nestopia') """
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        return splitted_status_str[0].split(b" ")[-1]
        
        
    def get_content_name(self):
        """ returns current content name, from the ROM filename (e.g. 'Super Mario Bros. (W) [!]') """
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        return splitted_status_str[1]
            

    def get_content_crc32_hash(self):
        """ returns current content CRC32 hash as a string """
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        return splitted_status_str[2].split(b"=")[1]
    
    
    def start(self, rom_path, core_path):

        """Start a Game ROM
        This Function needs the Path of the Plugin that could be used
        rom_path: Path to the Game ROM
        plugin_path: Path to the suitable Plugin from libretro
        Returns: True if everything was fine
        Returns: False an Error occured
        """

        rom_path = os.path.expanduser(rom_path)

        if not os.path.isfile(rom_path):
            self.logger.error('Error: Cant Start, Romfile not exist')
            self.logger.error(rom_path)
            return False

        if not os.path.isfile(core_path):
            self.logger.error('Error: Cant Start, Corefile not exist')
            self.logger.error(core_path)
            return False

        if self.is_running():
            self.logger.warning('Error: Cant Start, Rom already running')
            return False

        self.rom_path = rom_path

        self.logger.info('Starting Rom: %s' % rom_path)
        self.logger.info('With Core: %s' % core_path)

        self.logger.error('UNIMPLEMENTED')
        return False


    def quit(self):

        """Exit a running ROM"""

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Quit')

        if self.is_paused():
            self.toggle_pause()
            time.sleep(0.2)

        try:
            self._socket.sendto(b'QUIT\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False

        self.logger.info('Rom Exited Successfull')
        return True


    def toggle_pause(self):

        """Toggle from Pause to Unpause mode
        Returns: The new State: "Pause" or "Unpause" Mode
        Returns: False an Error occured
        """

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Toggle Pause')

        try:
            self._socket.sendto(b'PAUSE_TOGGLE\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        
        time.sleep(0.5)
        
        if self.is_paused():
            return 'paused'
        else:
            return 'unpaused'

            
    def read_core_ram(self, address, length):
        """ read from current core RAM at address length-bytes. Returs an array of bytes. """
        if not self.is_running():
            self.logger.error('Rom is not running')
            return []
                
        self.logger.info('Send: Read core ram')
        
        cmd = b"READ_CORE_RAM " + ("%x" % address).encode() + b" " + ("%x" % length).encode() + b'\n'
        
        try:
            self._socket.sendto(cmd, (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return []
        
        time.sleep(0.1)
        
        answer, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received

        # TODO: split answer by lines
        if answer.startswith(b'READ_CORE_RAM'):
            response_bytes = answer.split()[2:]  # from 'READ_CORE_RAM f E5 C4 09 F0 2A 00 00 31 00 01\n'
            return response_bytes
            
    
    def write_core_ram(self, address, buf):
        """ write into current core RAM from address the array of bytes passed into buf. """
        cmd = b"WRITE_CORE_RAM " + ("%x" % address).encode()
        for b in buf:
            cmd += b" %02x" % b
        cmd += b"\n"
        self.logger.debug('Sending: ' + str(cmd))  # e.g. b"WRITE_CORE_RAM f E5 C4 09 F0 2A 00 00 31 00 01\n"

        try:
            self._socket.sendto(cmd, (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        return True

    
    def toggle_fullscreen(self):

        """Toggle from Window to Fullscreen mode
        Returns: The new State: "Fullscreen" or "Window" Mode
        Returns: False an Error occured
        """

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Fullscreen Toggle')
        
        try:
            self._socket.sendto(b'FULLSCREEN_TOGGLE\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        #time.sleep(0.5)
        # TODO: return current fullscreen status
        return True


    def load_state(self):

        """Load a Savestate
        """

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        try:
            self._socket.sendto(b'LOAD_STATE\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        #time.sleep(0.5)
        return True
        
        
    def save_state(self):

        """Saves the State of the current Rom
        Return None: An Error occured
        """

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Save State')

        try:
            self._socket.sendto(b'SAVE_STATE\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        return True


    def reset(self):

        """Reset a running Rom and start from beginning"""

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Reset')

        if self.is_paused():
            self.toggle_pause()

        try:
            self._socket.sendto(b'RESET\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        #time.sleep(0.5)
        return True


