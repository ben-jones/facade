#! /usr/bin/python
# Ben Jones
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
import random
import select
import socket
import socks
import string
import sys
import urllib2

#flask stuff
from flask import Flask, request, make_response
app = Flask(__name__)

# local imports
import frame
import urlEncode
import imageEncode
from socks4a.htptProxy import ThreadingSocks4Proxy, ReceiveSocksReq, ForwardSocksReq

#from htpt import frame
#from htpt import urlEncode
#from htpt import imageEncode

#Constants
CLIENT_SOCKS_PORT=8000 # communication b/w Tor and SOCKS server
SERVER_SOCKS_PORT=9150 # communication b/w Tor and SOCKS client
HTPT_CLIENT_SOCKS_PORT=8002   # communication b/w htpt and SOCKS
#HTPT_SERVER_SOCKS_PORT=8003   # communication b/w htpt and SOCKS
TIMEOUT = 0.5 #max number of seconds between calls to read from the server
PAYLOAD_SIZE = 150
ENCODING_SCHEME = 'market'
#Constants just to make this work-> remove
#TODO
TOR_BRIDGE_ADDRESS = "localhost:5000"
TOR_BRIDGE_PASSWORD = "hello"
PASSWORDS = [TOR_BRIDGE_PASSWORD]

# Note: I wrote this hastily, so the function names within our modules
# are likely different

class HTPT():
  def __init__(self):
    self.addressList = []
    self.disassembler = frame.Disassembler(callback)

  def run_client(self):
    # initialize the connection
    self.assembler = frame.Assembler()
    # bind to a local address and wait for Tor to connect
    self.bridgeConnect(TOR_BRIDGE_ADDRESS, TOR_BRIDGE_PASSWORD)
    while 1:
      segment = ''.join([random.choice(string.digits) for i in range(PAYLOAD_SIZE)])
      framed = self.assembler.assemble(segment)
      # encode the data
      encoded = urlEncode.encode(framed, ENCODING_SCHEME)
      # send the data with headless web kit
      request = urllib2.Request(encoded['url'])
      for cookie in encoded['cookie']:
        request.add_header('Cookie:', cookie)
      reader = urllib2.urlopen(request)
      readData = reader.read()
      # if we have received data from the Internet, then send it up to Tor
      decoded = imageEncode.decode(readData, 'png')
      self.disassembler.disassemble(decoded)

  def bridgeConnect(self, address, password):
    """
    Create a connection to a bridge from a client

    Parameters:
    address- the ip address to connect to
    password- the password to send in the payload of the packet
  
    Notes: this function will send a packet to the server via market
    encoding with the password hidden in the payload

    Note: the function will initiate a connection with the bridge by
    sending a market encoded url with a payload of just the connect
    password. After sending the GET request, the function will use the
    returned image (just padding) to initialize the session ID

    Returns: whatever state you need to keep using headless web kit
    """

    data = self.assembler.assemble(password)
    encodedData = urlEncode.encodeAsMarket(data)
    request = urllib2.Request(encodedData['url'])
    for cookie in encodedData['cookie']:
      request.add_header('Cookie:', cookie)
    reader = urllib2.urlopen(request)
    image = reader.read()
    # use the returned image to initialize the session ID
    decodedData = imageEncode.decode(image, 'png')
    self.disassembler.disassemble(decodedData)
    self.assembler.setSessionID(self.disassembler.getSessionID())

  def recvData(self, data):
    """
    Callback function for the dissassemblers
    
    Parameters:
    data- the string of received data to be passed up to Tor
    
    Notes: this functions is used by both the client and server to
    pass data up to Tor

    Returns: nothing

    """
#    print "htpt: {}".format(data)
    # self.torSock.send(data)
    return

@app.route('/')
def processRequest():
  """Process incoming requests from Apache
  
  Structure: this function determines whether data should go through
  to htpt decoding or if it should be passed to the image
  gallery. This is a function due to constraints from flask

  """
  # if we are not in the address list, then this is not an initialized connection
  if request.remote_addr not in addressList:
      # if the address is not in the list and it is not a market
      # request, then it is web gallery traffic
      if not urlEncode.isMarket(request.url):
        sendToImageGallery(request)
        return
      # if this is a market request, then proceed with new session initialization
      else:
        encoded = {'url':request.url, 'cookie':{}}
        decoded = urlEncode.decode(encoded)
        sender, receiver = frame.initServerConnection(decoded, PASSWORDS, callback)
        # if the client sent a bad password, print an error message
        # and return an empty image
        if sender == False:
          print "Bad password entered"
          return sendToImageGallery(request)
        # Note: this will need to change to accomodate multiple client sessions
        htptObject.assembler = sender
        htptObject.disassembler = receiver
        addressList.append(request.remote_addr)
        #send back a blank image with the new session id
        framed = htptObject.assembler.assemble('')
        image = imageEncode.encode(framed, 'png')
        return serveImage(image)
          #TODO
          #setup some way to maintain a single Internet connection per client
  # if this is an initialized client, then receive the data and see
  # if we have anything to send
  else:
    #receive the data
    decoded = urlEncode.decode({'url':request.url, 'cookie':request.cookies})
    htptObject.disassembler.disassemble(decoded)
    segment = ''.join([random.choice(string.digits) for i in range(PAYLOAD_SIZE)])
    framed = htptObject.assembler.assemble(segment)
    # encode the data
    encoded = imageEncode.encode(framed, 'png')
    # send the data with apache
    return serveImage(encoded)

def sendToImageGallery(request):
  image = imageEncode.encode('', 'png')
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response

def serveImage(image):
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response

def callback(data):
  if data == '':
    return
#  else:
#    print "Received: {}".format(data)
  htptObject.recvData(data)
  
if __name__ == '__main__':
  htptObject = HTPT()
  urlEncode.domain = TOR_BRIDGE_ADDRESS
  if str(sys.argv[1]) == "-client":
    htptObject.run_client()
  else:
    addressList = []
    # setup the proxy server
    # bind to a local address and wait for Tor to connect
    # htptObject.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # htptObject.torBinder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # htptObject.torBinder.bind(('localhost', SERVER_SOCKS_PORT))
    # htptObject.torBinder.listen(1)
    # (htptObject.torSock, address) = htptObject.torBinder.accept()
    # htptObject.torSock = socks.socksocket()
    # htptObject.torSock.setproxy(socks.PROXY_TYPE_SOCKS4, "localhost", SERVER_SOCKS_PORT)
    # htptObject.torSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # htptObject.torSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # htptObject.torSock.connect(("localhost", SERVER_SOCKS_PORT))
    app.run(debug=True, use_reloader=False)
