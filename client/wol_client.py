#!/usr/bin/env python3
# Apollo WakeOnLAN client
# 
# gets a list of mac addresses to send WOL packets to
# by querying a central database via HTTP GET

import struct, socket
from time import sleep
import logging
import configparser
import requests
import json
import argparse

def WakeOnLan(ethernet_address):
# Wake-On-LAN
# Copyright (C) 2002 by Micro Systems Marc Balmer
# Written by Marc Balmer, marc@msys.ch, http://www.msys.ch/
# This code is free software under the GPL

  # Construct a six-byte hardware address

  addr_byte = ethernet_address.split(':')
  hw_addr = struct.pack('BBBBBB', int(addr_byte[0], 16),
    int(addr_byte[1], 16),
    int(addr_byte[2], 16),
    int(addr_byte[3], 16),
    int(addr_byte[4], 16),
    int(addr_byte[5], 16))

  # Build the Wake-On-LAN "Magic Packet"...

  msg = '\xff'.encode('utf-8') * 6 + hw_addr * 16

  # ...and send it to the broadcast address using UDP

  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  s.sendto(msg, ('<broadcast>', 9))
  s.close()

def register(server,port,macaddress,as_node=0):
    registration = requests.post('http://%s:%s/computers/add', json={"name":hostname,"mac":macaddress,"is_wol_node":as_node})


logging.basicConfig(filename='wol_client.log',level=logging.DEBUG,format='%(asctime)s %(message)s')
print("Apollo WakeOnLAN client 0.51 alpha\n\n")

parser = argparse.ArgumentParser()
parser.add_argument("--register","-r",help="aggiungi computer sul server Wake On LAN", dest="register",action="store_true")
args = parser.parse_args()
if args.register:
       logging.debug("Registering to WOL server")
"""
try:
    hostname = socket.gethostbyaddr(socket.gethostname())[1][0]
except Exception, err:
       logging.exception('ERROR: Unable do determine hostname')
       raise
print "Hostname is %s" % hostname
"""
config = configparser.ConfigParser()
# Legge il file INI di configurazione
try:
    config.read('wol_client.ini')
except Exception as err:
    logging.exception('Error opening wol_client.ini')
    raise
try:
    livello_log = 'logging.%s' % config.get('DEFAULT','log_level')
    server_host = config.get('DEFAULT','server_host')
    server_port = config.get('DEFAULT','server_port')
except Exception as err:
    logging.exception('ERROR:Error reading wol_client.ini')
    raise
logging.info('Attempting to contact WOL server at %s:%s' % (server_host,server_port))
try:
    da_risvegliare = requests.get('http://%s:%s/wakeuplist/' % (server_host,server_port)).json()
except Exception as err:
    logging.exception('ERROR:Unable to contact server %s:%s' % (server_host,server_port))
    raise
else:
    logging.debug("Greetings server, who shall I woke up?")
    if type(da_risvegliare) == list:
        logging.debug("Server answered:Thy shall woke up %s" % da_risvegliare)
        for hostname,mac_address in da_risvegliare:
            logging.info("Attempting to awake %s" % hostname)
            WakeOnLan(mac_address) 
            sleep(1)
    else:
        logging.error("ERROR: Problem with wake_list, server answered:%s" % da_risvegliare)
