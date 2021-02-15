#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""

import socketserver
import argparse
import logging
import threading
import pyaudio

#import tnc
import static
import helpers



       



def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), tnc.CMDTCPRequestHandler)
        cmdserver.serve_forever()
    
    finally:
        cmdserver.server_close()
        
        
def start_data_socket():

    try:
        logging.info("SRV | STARTING TCP/IP DATA ON PORT: " + str(static.PORT + 1))
        socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
        dataserver = socketserver.TCPServer((static.HOST, static.PORT + 1), tnc.DATATCPRequestHandler)
        dataserver.serve_forever()
    
    finally:
        dataserver.server_close()        




p = pyaudio.PyAudio()
devices = []
for x in range(0, p.get_device_count()):
        devices.append(f"{x} - {p.get_device_info_by_index(x)['name']}")
        
for line in devices:
        print(line) 
        
        
        
        

if __name__ == '__main__':

    static.MYCALLSIGN = b'DJ2LS'
    static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)

    static.DXCALLSIGN = b'DH3WO'
    static.DXCALLSIGN_CRC8 =  helpers.get_crc_8(static.DXCALLSIGN)

    print("MYCALLSIGN " + str(static.MYCALLSIGN))
    print("MYCALLSIGN_CRC8 " + str(static.MYCALLSIGN_CRC8))
    
    print("DXCALLSIGN " + str(static.DXCALLSIGN))
    print("DXCALLSIGN_CRC8 " + str(static.DXCALLSIGN_CRC8))



    #--------------------------------------------GET PARAMETER INPUTS  
    parser = argparse.ArgumentParser(description='Simons TEST TNC')
    parser.add_argument('--rx', dest="audio_input_device", default=0, help="sound card for listening.", type=int)
    parser.add_argument('--tx', dest="audio_output_device", default=0, help="sound card for transmitting.", type=int)
    parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int)  
    parser.add_argument('--mode', dest="freedv_data_mode", default=12, help="Set the mode.", type=int)
   
    args = parser.parse_args()
    
    
    
    static.FREEDV_DATA_MODE = args.freedv_data_mode
    static.AUDIO_INPUT_DEVICE = args.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = args.audio_output_device
    static.PORT = args.socket_port
    
    import tnc # we need to wait until we got all parameters from argparse

    #-------------------------------------------- DEFINE LOGGING    
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s', datefmt='%H:%M:%S', level=logging.INFO)

    logging.addLevelName( logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
    logging.addLevelName( logging.INFO, "\033[1;37m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    logging.addLevelName( logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
    logging.addLevelName( logging.ERROR, "\033[1;31m%s\033[1;0m" % "FAILED")
    #logging.addLevelName( logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName( logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))
    
    logging.addLevelName( 25, "\033[1;32m%s\033[1;0m" % "SUCCESS")
    logging.addLevelName( 24, "\033[1;34m%s\033[1;0m" % "DATA")

    
    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    #'DEBUG'   : 37, # white
    #'INFO'    : 36, # cyan
    #'WARNING' : 33, # yellow
    #'ERROR'   : 31, # red
    #'CRITICAL': 41, # white on red bg
    
    
    
    #--------------------------------------------START CMD & DATA SERVER  
  
    cmd_server_thread = threading.Thread(target=start_cmd_socket, name="cmd server")
    cmd_server_thread.start()
  
    data_server_thread = threading.Thread(target=start_data_socket, name="data server")
    data_server_thread.start()
        
  

