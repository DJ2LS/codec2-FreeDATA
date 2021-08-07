#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import socketserver
import threading
import logging
import json
import asyncio
import time

import static
import data_handler
import helpers

import sys, os

class CMDTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("Client connected...")    
        
        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + 10
        while socketTimeout > time.time():

            time.sleep(0.01)
            encoding = 'utf-8'
            #data = str(self.request.recv(1024), 'utf-8')

            data = bytes()
            
            # we need to loop through buffer until end of chunk is reached or timeout occured
            while True and socketTimeout > time.time():
                chunk = self.request.recv(1024)  # .strip()
                data += chunk
                if chunk.endswith(b'\n'):
                    break
            data = data[:-1]  # remove b'\n'
            data = str(data, 'utf-8')
            #print(data)
            
            if len(data) > 0:
                socketTimeout = time.time() + static.SOCKET_TIMEOUT
            
            # convert data to json object
            # we need to do some error handling in case of socket timeout

            try:
                received_json = json.loads(data)
                #print(received_json)
            #except:
            #    received_json = ''
            #    print(data)
            #except Exception as e:
            #    #print("Wrong command: " + data)
            #    #print(e)
            #    exc_type, exc_obj, exc_tb = sys.exc_info()
            #    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #    print(exc_type, fname, exc_tb.tb_lineno)
            except json.decoder.JSONDecodeError as e:
                print(e)
                print("#################################")
                print(data)
            # GET COMMANDS
            # "command" : "..."
            
            # SET COMMANDS
            # "command" : "..."
            # "parameter" : " ..."
            
            # DATA COMMANDS
            # "command" : "..."
            # "type" : "..."
            # "dxcallsign" : "..."
            # "data" : "..."
            
            
            try:
                # SOCKETTEST ---------------------------------------------------
                #if data == 'SOCKETTEST':
                #if received_json["command"] == "SOCKETTEST":
                #    #cur_thread = threading.current_thread()
                #    response = bytes("WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC", encoding)
                #    self.request.sendall(response)

                # CQ CQ CQ -----------------------------------------------------
                #if data == 'CQCQCQ':
                if received_json["command"] == "CQCQCQ":
                    socketTimeout = 0
                    #asyncio.run(data_handler.transmit_cq())
                    CQ_THREAD = threading.Thread(target=data_handler.transmit_cq, args=[], name="CQ")
                    CQ_THREAD.start()

                # PING ----------------------------------------------------------
                #if data.startswith('PING:'):
                if received_json["type"] == 'PING' and received_json["command"] == "PING":
                    # send ping frame and wait for ACK
                    print(received_json)
                    dxcallsign = received_json["dxcallsign"]
                    #asyncio.run(data_handler.transmit_ping(dxcallsign))
                    PING_THREAD = threading.Thread(target=data_handler.transmit_ping, args=[dxcallsign], name="CQ")
                    PING_THREAD.start()
                    
                # ARQ CONNECT TO CALLSIGN ----------------------------------------
                #if data.startswith('ARQ:CONNECT:'):
                #if received_json["command"] == "ARQ:CONNECT":
                # 
                #    dxcallsign = received_json["dxcallsign"]
                #    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                #    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)

                #    if static.ARQ_STATE == 'CONNECTED':
                #        # here we could disconnect
                #        pass

                #    if static.TNC_STATE == 'IDLE':

                #        asyncio.run(data_handler.arq_connect())

                # ARQ DISCONNECT FROM CALLSIGN ----------------------------------------
                #if received_json["command"] == "ARQ:DISCONNECT":
                #    asyncio.run(data_handler.arq_disconnect())


                if received_json["type"] == 'ARQ' and received_json["command"] == "OPEN_DATA_CHANNEL": # and static.ARQ_STATE == 'CONNECTED':
                    static.ARQ_READY_FOR_DATA = False
                    static.TNC_STATE = 'BUSY'
                    
                    dxcallsign = received_json["dxcallsign"]
                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
                    
                    asyncio.run(data_handler.arq_open_data_channel())
                    

                if received_json["type"] == 'ARQ' and received_json["command"] == "sendFile":# and static.ARQ_READY_FOR_DATA == True: # and static.ARQ_STATE == 'CONNECTED' :
                    static.TNC_STATE = 'BUSY'
                    
                    #on a new transmission we reset the timer
                    static.ARQ_START_OF_TRANSMISSION = int(time.time())
                    
     
                    dxcallsign = received_json["dxcallsign"]
                    mode = int(received_json["mode"])
                    n_frames = int(received_json["n_frames"])
                    filename = received_json["filename"]
                    filetype = received_json["filetype"]
                    data = received_json["data"]
                    checksum = received_json["checksum"]
                    
                    print(mode)
                    print(n_frames)
                    
                    
                    static.DXCALLSIGN = bytes(dxcallsign, 'utf-8')
                    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
                    
                    dataframe = '{"filename": "'+ filename + '", "filetype" : "' + filetype + '", "data" : "' + data + '", "checksum" : "' + checksum + '"}'
                    #data_out = bytes(received_json["data"], 'utf-8')
                    data_out = bytes(dataframe, 'utf-8')

                   
                    
                    #ARQ_DATA_THREAD = threading.Thread(target=data_handler.arq_transmit, args=[data_out], name="ARQ_DATA")
                    #ARQ_DATA_THREAD.start()
                    
                    ARQ_DATA_THREAD = threading.Thread(target=data_handler.open_dc_and_transmit, args=[data_out, mode, n_frames], name="ARQ_DATA")
                    ARQ_DATA_THREAD.start()
                    # asyncio.run(data_handler.arq_transmit(data_out))

                # SETTINGS AND STATUS ---------------------------------------------
                if received_json["type"] == 'SET' and received_json["command"] == 'MYCALLSIGN':
                    callsign = received_json["parameter"]

                    if bytes(callsign, encoding) == b'':
                        self.request.sendall(b'INVALID CALLSIGN')
                    else:
                        static.MYCALLSIGN = bytes(callsign, encoding)
                        static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
                        logging.info("CMD | MYCALLSIGN: " + str(static.MYCALLSIGN))
          
                if received_json["type"] == 'SET' and received_json["command"] == 'MYGRID':
                    mygrid = received_json["parameter"]

                    if bytes(mygrid, encoding) == b'':
                        self.request.sendall(b'INVALID GRID')
                    else:
                        static.MYGRID = bytes(mygrid, encoding)
                        logging.info("CMD | MYGRID: " + str(static.MYGRID))
                        
                                    
                if received_json["type"] == 'GET' and received_json["command"] == 'STATION_INFO':
                    output = {
                        "COMMAND": "STATION_INFO",
                        "MY_CALLSIGN": str(static.MYCALLSIGN, encoding),
                        "DX_CALLSIGN": str(static.DXCALLSIGN, encoding),
                        "DX_GRID": str(static.DXGRID, encoding),
                        "EOF" : "EOF",  
                    }
                    
                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))

                if received_json["type"] == 'GET' and received_json["command"] == 'TNC_STATE':
                    #print(static.SCATTER)
                    output = {
                        "COMMAND": "TNC_STATE",
                        "PTT_STATE": str(static.PTT_STATE),
                        "CHANNEL_STATE": str(static.CHANNEL_STATE),
                        "TNC_STATE": str(static.TNC_STATE),
                        "ARQ_STATE": str(static.ARQ_STATE),
                        "AUDIO_RMS": str(static.AUDIO_RMS),
                        "BER": str(static.BER),
                        "SNR": str(static.SNR),
                        "FREQUENCY" : str(static.HAMLIB_FREQUENCY),
                        "MODE" : str(static.HAMLIB_MODE),
                        "BANDWITH" : str(static.HAMLIB_BANDWITH),
                        "FFT" : str(static.FFT),
                        "SCATTER" : static.SCATTER,
                        #"RX_BUFFER_LENGTH": str(len(static.RX_BUFFER)),
                        #"TX_N_MAX_RETRIES": str(static.TX_N_MAX_RETRIES),
                        #"ARQ_TX_N_FRAMES_PER_BURST": str(static.ARQ_TX_N_FRAMES_PER_BURST),
                        #"ARQ_TX_N_BURSTS": str(static.ARQ_TX_N_BURSTS),
                        #"ARQ_TX_N_CURRENT_ARQ_FRAME": str(int.from_bytes(bytes(static.ARQ_TX_N_CURRENT_ARQ_FRAME), "big")),
                        #"ARQ_TX_N_TOTAL_ARQ_FRAMES": str(int.from_bytes(bytes(static.ARQ_TX_N_TOTAL_ARQ_FRAMES), "big")),
                        #"ARQ_RX_FRAME_N_BURSTS": str(static.ARQ_RX_FRAME_N_BURSTS),
                        #"ARQ_RX_N_CURRENT_ARQ_FRAME": str(static.ARQ_RX_N_CURRENT_ARQ_FRAME),
                        #"ARQ_N_ARQ_FRAMES_PER_DATA_FRAME": str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME)
                        "EOF" : "EOF",
                    }  
                    
                    
                    jsondata = json.dumps(output)
                    #print(len(jsondata))
                    self.request.sendall(bytes(jsondata, encoding))
                
                if received_json["type"] == 'GET' and received_json["command"] == 'FFT':
                    output = {
                        "FFT" : str(static.FFT)
                    }
                    
                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))
                
                #if received_json["type"] == 'GET' and received_json["command"] == 'SCATTER':
#
#                    print(static.SCATTER)
#                    output = {
#                        "COMMAND" : "SCATTER",
#                        "DATA" : static.SCATTER
#                    }
#                   print(output)
#                   jsondata = json.dumps(output)
#                   self.request.sendall(bytes(jsondata, encoding))   
                                 
                if received_json["type"] == 'GET' and received_json["command"] == 'DATA_STATE':
                    output = {
                        "COMMAND": "DATA_STATE",
                        "RX_BUFFER_LENGTH": str(len(static.RX_BUFFER)),
                        "TX_N_MAX_RETRIES": str(static.TX_N_MAX_RETRIES),
                        "ARQ_TX_N_FRAMES_PER_BURST": str(static.ARQ_TX_N_FRAMES_PER_BURST),
                        "ARQ_TX_N_BURSTS": str(static.ARQ_TX_N_BURSTS),
                        "ARQ_TX_N_CURRENT_ARQ_FRAME": str(int.from_bytes(bytes(static.ARQ_TX_N_CURRENT_ARQ_FRAME), "big")),
                        "ARQ_TX_N_TOTAL_ARQ_FRAMES": str(int.from_bytes(bytes(static.ARQ_TX_N_TOTAL_ARQ_FRAMES), "big")),
                        "ARQ_RX_FRAME_N_BURSTS": str(static.ARQ_RX_FRAME_N_BURSTS),
                        "ARQ_RX_N_CURRENT_ARQ_FRAME": str(static.ARQ_RX_N_CURRENT_ARQ_FRAME),
                        "ARQ_N_ARQ_FRAMES_PER_DATA_FRAME": str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME),
                        "EOF" : "EOF",
                    }
                    
                    jsondata = json.dumps(output)
                    self.request.sendall(bytes(jsondata, encoding))


                if received_json["type"] == 'GET' and received_json["command"] == 'HEARD_STATIONS':
                    # print("HEARD STATIONS COMMAND!")

                    data = {"COMMAND": "HEARD_STATIONS", "STATIONS" : []}
                    for i in range(0, len(static.HEARD_STATIONS)):
                        data["STATIONS"].append({"DXCALLSIGN": str(static.HEARD_STATIONS[i][0], 'utf-8'),"DXGRID": str(static.HEARD_STATIONS[i][1], 'utf-8'), "TIMESTAMP": static.HEARD_STATIONS[i][2], "DATATYPE": static.HEARD_STATIONS[i][3], "SNR": static.HEARD_STATIONS[i][4]})
                    # print(static.HEARD_STATIONS[i][1])
                    
                    
                    #data.append({"EOF" : "EOF"})
                    jsondata = json.dumps(data)
                    self.request.sendall(bytes(jsondata, encoding))



                if received_json["type"] == 'GET' and received_json["command"] == 'RX_BUFFER':
                    data = data.split('GET:RX_BUFFER:')
                    bufferposition = int(data[1]) - 1
                    if bufferposition == -1:
                        if len(static.RX_BUFFER) > 0:
                            self.request.sendall(static.RX_BUFFER[-1])

                    if bufferposition <= len(static.RX_BUFFER) > 0:
                        self.request.sendall(bytes(static.RX_BUFFER[bufferposition]))

                if received_json["type"] == 'SET' and received_json["command"] == 'DEL_RX_BUFFER':
                    static.RX_BUFFER = []
            
            #exception, if JSON cant be decoded
            except Exception as e:
                #print("Wrong command: " + data)
                #print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)                        
        print("Client disconnected...")

def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True  # https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), CMDTCPRequestHandler)
        cmdserver.serve_forever()

    finally:
        cmdserver.server_close()
