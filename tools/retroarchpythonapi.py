
"""Retroarch Python API
This is a Python API for the RetroArch /
libretro Libraries for Console Emulators

Derived and mostly compatible with  https://github.com/merlink01/RetroArchPythonAPI/
added python3 support and made network-based by eadmaster
"""

import os
import time
import logging
import socket

__version__ = 0.3
__copyright__ = 'GPL V2'



class RetroArchPythonApi(object):

    """Usage:
    from retroarchpythonapi import RetroArchPythonApi
    api = RetroArchPythonApi()
    
    api.toggle_pause()
    api.save_state()
    api.load_state()
    api.read_core_ram(0x7df, 4)  # read 4 bytes from address 7df
    api.write_core_ram(0x7df, [0x00, 0x00, 0x00, 0x00])  # write 4 bytes set to 0 from address 7df
    api.reset()
    api.quit()
    
    methods to read current status:
    api.is_alive()  # true if is responding to network commands
    api.has_content()  # true if has some content loaded
    api.is_paused() # true if has some content loaded and it IS paused
    api.is_playing()  # true if has some content loaded and it IS NOT paused
    api.get_version()
    api.get_system_id()
    api.get_content_name()
    api.get_content_crc32_hash()
    """

    _socket = None
    _socket_ipaddr = "127.0.0.1"
    _socket_portnum = 55355
    _network_sleep_time = 0.1
    _version = ""

    def __init__(self, ipaddr="127.0.0.1", portnum=55355, network_sleep_time=0.1, check_connection=True):

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
        self._network_sleep_time = network_sleep_time
        
        if not check_connection:
            return
    
        self.logger.info("Checking connection with Retroarch on " + ipaddr + ":" + str(portnum) + "...")
        
        # temp. add socket timeout
        self._socket.settimeout(1)
        
        self._version = self.get_version()
        if not self._version:
            self.logger.warning("Connection timeout: make sure Retroarch is running, has network commands enabled and is connectable (will retry connecting until killed).")
        while not self._version:
            self._version = self.get_version()
            time.sleep(2)

        # remove socket timeout
        self._socket.settimeout(None)
        
        self.logger.info('Retroarch connection checked')
        
        #TODO:if self._version <= b'1.8.4'
        # self.logger.warning('Retroarch v1.8.4 does not support GET_STATUS command')


    def _get_status(self):
        try:
            self._socket.sendto(b'GET_STATUS\n', (self._socket_ipaddr, self._socket_portnum))
            response_str, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
            return response_str.rstrip()
        except:
            logging.exception('')
            return ""


    def has_content(self):
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
            

    def is_playing(self):
        """ returns True if the content is running """
        status_str = self._get_status()
        splitted_status_str = status_str.split(b",")
        if splitted_status_str[0].split(b" ")[1] == b'RUNNING':
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
    
    
    def get_version(self):
        """ returns current Retroarch version (as a string) """
        try:
            self._socket.sendto(b'VERSION\n', (self._socket_ipaddr, self._socket_portnum))
            response_str, addr = self._socket.recvfrom(16)
            return response_str.rstrip()
        except:
            if not self._socket.gettimeout() == 1:
                self.logger.exception("")
            return ""


    def is_alive(self):
        """ returns True if Retroarch is running and connectable """
        self._socket.settimeout(1)  # temp. add socket timeout
        v = self.get_version()
        self._socket.settimeout(None)  # remove socket timeout
        if v:
            return True
        else:
            return False


    def quit(self):
        """Exit a running ROM"""

        if not self.is_running():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Quit')

        if self.is_paused():
            self.toggle_pause()
            time.sleep(self._network_sleep_time)

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
        
        time.sleep(self._network_sleep_time)
        
        if self.is_paused():
            return 'paused'
        else:
            return 'unpaused'

            
    def read_core_ram(self, address, length):
        """ read from current core RAM at address length-bytes. Returs an array of bytes. """
        
        # TODO: check self._version -> "Unsupported command by this Retroarch version"
        
        if not self.has_content():
            self.logger.error('No content loaded')
            return []
                
        self.logger.info('Send: Read core ram')
        
        cmd = b"READ_CORE_RAM " + ("%x" % address).encode() + b" " + ("%x" % length).encode() + b'\n'
        
        try:
            self._socket.sendto(cmd, (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return []
        
        time.sleep(self._network_sleep_time)
        
        answer, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
        # TODO: read by blocks
        
        if answer.startswith(b'READ_CORE_RAM'):
            response_bytes = answer.split()[2:]  # from 'READ_CORE_RAM f E5 C4 09 F0 2A 00 00 31 00 01\n'
            return response_bytes
            
    
    def write_core_ram(self, address, buf):
        """ write into current core RAM from address the array of bytes passed into buf. """
        
        # TODO: check self._version -> "Unsupported command by this Retroarch version"
        
        if not self.has_content():
            self.logger.error('No content loaded')
            return False
            
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
        """ Load currently-selected savestate """

        if not self.has_content():
            self.logger.error('No content loaded')
            return False

        try:
            self._socket.sendto(b'LOAD_STATE\n', (self._socket_ipaddr, self._socket_portnum))
        except:
            self.logger.exception("")
            return False
        # else
        return True
        
        
    def save_state(self):
        """ Saves currently-selected savestate """

        if not self.has_content():
            self.logger.error('No content loaded')
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
        """ Reset a running content """

        if not self.has_content():
            self.logger.error('No content loaded')
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
        return True


