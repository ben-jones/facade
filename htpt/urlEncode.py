# Ben Jones
# Georgia Tech Fall 2013
# url-encode.py: collection of functions to hide small chunks of data in urls

import binascii
import re
from base64 import urlsafe_b64encode, urlsafe_b64decode
from random import choice, randint

AVAILABLE_TYPES=['market', 'baidu', 'google', 'b64', 'search']
BYTES_PER_COOKIE=30
LOOKUP_TABLE_IMPORTED = False
LOOKUP_TABLE = ['a', 'an', 'ha', 'hi', 'if', 'ai', 'he', 'BB',
                'it', 'cd', 'co', 'as', 'is', 'am', 'DA', 'EE']
REVERSE_LOOKUP_TABLE = {'a':'0', 'an':'1', 'ha':'2', 'hi':'3',
                        'if':'4', 'ai':'5', 'he':'6', 'BB':'7',
                        'it':'8', 'cd':'9', 'co':'A', 'as':'B',
                        'is':'C', 'am':'D', 'DA':'E', 'EE':'F'}
DICT_FILE = "dictionary.txt"


class UrlEncodeError(Exception):
  pass

def encode(data, encodingType):
  """
  Encode data as a url

  Parameters:
  data - a string holding the data to be encoded
  encodingType - an string indicating what type of expression to hide
  the data in

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies if data was stored in cookies.

  Note: Cookies will be used if more data is sent than the url
  encoding method can support. When this occurs, as many cookies as
  necessary will be used to encode the data. Please be mindful that
  large numbers of cookies will look suspicious

  """

  print data[:4]
  if type(data) is list:
    data = ''.join(data)
  elif type(data) is not str:
    raise(UrlEncodeError("Bad data type: %s. Use string or list" % type(data)))

  if encodingType not in AVAILABLE_TYPES:
      raise(UrlEncodeError("Bad encoding type. Please refer to"
                           "url-encode.AVAILABLE_TYPES for available options"))
  if encodingType == 'market':
    return encodeAsMarket(data)
  elif encodingType == 'search':
    return encodeAsOpenSearch(data)
  elif encodingType == 'baidu':
    return encodeAsBaidu(data)
  elif encodingType == 'google':
    return encodeAsGoogle(data)
  elif encodingType == 'b64':
    return encodeAsB64(data)

def encodeAsCookies(data):
  """Hide data inside a series of cookies"""
  cookies = []
  while data != '':
    if len(data) > BYTES_PER_COOKIE:
      cookies.append(encodeAsCookie(data[:BYTES_PER_COOKIE]))
      data = data[BYTES_PER_COOKIE:]
    else:
      cookies.append(encodeAsCookie(data))
      data = ''
  return cookies

# def encodeAsB64(host, data):
def encodeAsB64(data):
  """
  Hide data inside the Host, path, and query string fields of the URL

  Parameters: data- a string with the data to encode

  Returns: a string of the url

  """
  # randomly take some data off of the end to be inserted into cookies
  print len(data)
  cookieSplit = randint(0, len(data)/2)
  cookieData = data[cookieSplit:]
  cookies = encodeAsCookies(cookieData)
  data = data[:cookieSplit]

  # base 64 encode the data
  encoded = urlsafe_b64encode(data)
  # encoded.replace("=", ".")

  # divide it into path and query string
  split = randint(0, len(encoded)-1)
  path = encoded[:split]
  query = encoded[split:]
  
  # randomly insert /'s into the path
  numSplits = randint(0, 15)
  if numSplits > len(data)/2:
    numSplits = len(data)/5
  # for loc in range(numSplits):
  #   location = randint(1, len(path)-1)
  #   path = path[:location] + "/" + path[:location]
  # # randomly insert ; and = into the query string
  # numSplits = randint(0, 15)
  # if numSplits > len(data)/2:
  #   numSplits = len(data)/8
  # for cap in range(numSplits):
  #   location = randint(0, (len(data)/numSplits))
  #   if cap == numSplits - 1:
  #     query = query[location:] + "=" + query[:location]
  #     break
  #   difference = randint(0, (len(data)/numSplits) -location)
  #   equalPos = cap* len(data)/numSplits
  #   var = equalPos + difference
  #   query = query[:equalPos] + "=" + query[equalPos:var] + ";" + query[var:]

  url = "http://" + domain + "/" + path + "?" + query
  encodedData = {'url':url, 'cookie':cookies}
  return encodedData

def encodeAsCookie(data):
  """
  Hide data inside a cookie

  Parameters: data- a string with fewer than 30 characters to encode

  Returns: a string with the key value pair

  Methods: will hide data in a cookie by storing the first 3-10
  characters of data as a key and the rest of the data as the
  value. All data will base64 encoded before it is placed in the url

  Note: this is intended for communication from the client to the
  server so we are sending back set cookies. If decide to use this for
  server-> client communication, we will need to modify this code
  """
  if len(data) <= 5:
    key = 'keyForPadding' #longer than 10 chars, so no need to escape
    value = data
  elif len(data) < 10 and len(data) > 5:
    keyLen = 3
    key = data[:keyLen]
    value = data[keyLen:]
  else:
    keyLen = randint(3, 10)
    key = data[:keyLen]
    value = data[keyLen:]

  key = urlsafe_b64encode(key)
  key = key.replace('=', '.')
  value = urlsafe_b64encode(value)
  # value = key.replace('=', '+')
  # cookie = key + '=' + value
  return {'key':key, 'value':value}

def decodeAsCookie(key, value):
  """
  Decode data from inside a cookie

  Parameters: cookie- the string of text representing the cookie. This
  will be decoded into data.

  Returns: a string with the hidden data

  Methods: will do take out the key and value, decode them, and
  concatenate them into the original string

  Note: As with the encodeAsCookie function, this function is designed
  to send data from the client to the server and modifications are
  necessary for convincing traffic from server to client
  """
  # pattern = 'Cookie: (?P<key>[a-zA-Z0-9+_\-/]+)=(?P<value>[a-zA-Z0-9+_=\-/]*)'
  # match = re.match(pattern, cookie)
  # print cookie
  
  # key = match.group('key')
  # value = match.group('value')
  # key = cookie.keys()[0]
  # print key
  # key= key[2:]
  # print key
  # value = cookie[key]
  key = key.replace('.', '=')
  key = urlsafe_b64decode(key)
  value = urlsafe_b64decode(value)
  #In this case, the data needed padding because it was too
  #short. Since this key is longer than 10 chars, it cannot occur
  #naturally and does not need to be escaped
  if key == 'keyForPadding':
    key = ''
  data = key + value
  return data

def pickDomain():
  """Pick a random domain from the list"""

  domains = ['live.com', 'microsoft.com', 'baidu.com', 'hao123.com']
  return choice(domains)

def pickRandomHexChar():
  """Pick a random hexadecimal character and return it"""

  characters = ['A','B','C','D','E','F']
  return choice(characters)

def encodeAsMarket(data):
  """
  Hide data inside a url commonly used for email personalization

  Parameters:
  data - the data to encode

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies.

  Note: Cookies will be used to store information if the data is over
  39 characters.

  """
  cookies = []
  if len(data) > 39:
    cookies = encodeAsCookies(data[39:])
    data = data[:39]
  #if needed, pad the data to 80 characters
  hexData = binascii.hexlify(data)
  if len(hexData) < 78:
    padSize = 78-len(hexData)
    padding = []
    for index in range(padSize):
      padding.append(pickRandomHexChar())
    padding = ''.join(padding)
  else:
    padSize = 0
    padding = ''
  #this is a one liner to convert the data length counter (the first 2
  #characters of the hash) from base 16 (hex) to a base 10 integer
  #that I can use
  dataLen = hex(len(hexData))[2:]
  if len(dataLen) == 1:
    dataLen = '0' + dataLen
  urlData = dataLen + hexData + padding
#  domain = pickDomain()
#  domain = "localhost"
  #Note: we cannot use urlparse here because it capitalizes our hex
  #values and we are using uppercase to distinguish padding and
  #actual text
#  url = 'http://' + 'click.' + domain + '?qs=' + urlData
  # url = 'http://' + "localhost:5000/" + '?qs=' + urlData
  url = 'http://' + domain + '/?qs=' + urlData
  encodedData = {'url':url, 'cookie':cookies}
  return encodedData

def isMarket(url):
  """Return true if this url matches the market pattern"""
  pattern = 'http://[a-zA-Z0-9:./]*\?qs=[0-9a-fA-F]{80}'
  matches = re.match(pattern, url)
  if matches != None:
      return True
  return False

def encodeAsBaidu(data):
  """
  Hide data inside the url by a chinese search engine for queries

  Parameters:
  data- the data to encode

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies.

  Note: Cookies will be used to store information if the data is over
  39 characters.

  Example: http://www.baidu.com/s?wd=mao+is+cool&rsv_bp=0&ch=&tn=baidu&bar=&rsv_spt=3&ie=utf-8

  """
  urlData = data
  cookies = []
  # if len(data) > 40:
  #   urlData = data[:40]
  #   cookies = encodeAsCookies(data[40:])
  # words = encodeAsEnglish(urlData)
  words = encodeWithDict(urlData)
  urlData = '+'.join(words)
  #Note: we cannot use urlparse here because it capitalizes our hex
  #values and we are using uppercase to distinguish padding and
  #actual text
  # url = 'http://www.baidu.com/s?wd=' + urlData
  url = 'http://' +domain + '/s?wd=' + urlData
  encodedData = {'url':url, 'cookie':cookies}
  return encodedData

def isBaidu(url):
  """Return True if this url matches the pattern for Baidu searches"""

  #Example: http://www.baidu.com/s?wd=mao+is+cool&rsv_bp=0&ch=&tn=baidu&bar=&rsv_spt=3&ie=utf-8
  pattern = 'http://www.baidu.com/s\?wd=[\S+]+'
  matches = re.match(pattern, url)
  if matches != None:
      return True
  return False

def decodeAsBaidu(url):
  """
  Decode data hidden inside a url format for searches

  Parameters: url- the url to decode

  Returns: a string with the decoded data

  """
  # pattern = 'http://www.baidu.com/s\?wd=(?P<englishText>[a-zA-Z0-9+]+)'
  pattern = 'http://'+ domain + '/s\?wd=(?P<englishText>[\S]+)'
  matches = re.match(pattern, url)
  urlData = matches.group('englishText')
  # print url
  # print urlData
  words = urlData.split('+')
  # data = decodeAsEnglish(words)
  data = decodeWithDict(words)
  # return data
  return ''.join(data)




def isGoogle(url):
  """
  Check if the url is hiding data in a form which resembles Google
  searches

  Parameters: url- the url to check

  Note: since this is regular expression matching, it will not catch
  cases where jibberish is inserted into or appended onto urls. For
  instance, the string ...?q=the+@asdf would pass because the regular
  expression would only match the+a

  """
  pattern = 'http://www.google.com/search\?q=(?P<query>[a-zA-Z0-9+]+)'
  matches = re.match(pattern, url)
  if matches != None:
    return True
  return False

def encodeAsGoogle(data):
  """
  Hide data in a url that fits the form of Google searches

  Parameters: data- the data to hide

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies.

  Note: Cookies will be used to store information if the data is over
  39 characters.

  Example: https://www.google.com/search?q=freedom+is+nice

  """
  #if the data is over 40 chars, then use cookies
  urlData = data
  cookies = []
  if len(data) > 40:
    urlData = data[:40]
    cookies = encodeAsCookies(data[40:])
  words = encodeAsEnglish(urlData)
  urlData = '+'.join(words)
  url = 'http://www.google.com/search?q=' + urlData
  encodedData = {'url':url, 'cookie':cookies}
  return encodedData


def decodeAsGoogle(url):
  """Decode data hidden within a google search query"""
  
  pattern = 'http://www.google.com/search\?q=(?P<englishText>[a-zA-Z0-9+]+)'
  matches = re.match(pattern, url)
  urlData = matches.group('englishText')
  words = urlData.split('+')
  data = decodeAsEnglish(words)
  return data

def encodeAsEnglish(data):
  """Serialize data using english words for symbols"""

  #first, convert the string to a hex representation
  hexString = binascii.hexlify(data)
  #and convert the hex representation into words
  stringy = []
  for char in hexString:
    stringy.append(LOOKUP_TABLE[int(char, 16)])
  return stringy

def decodeAsEnglish(words):
  """Convert data back to hex, then a string from english text"""

  #first convert the english text back to hex
  hexString = []
  for word in words:
    hexString.append(REVERSE_LOOKUP_TABLE[word])
  hexString = ''.join(hexString)
  #and convert the hex back to a string
  data = binascii.unhexlify(hexString)
  return data

def encodeWithDict(data):
  """Convert two byte chunks to english text"""
  # if LOOKUP_TABLE_IMPORTED == False:
  #   importLookupTable(DICT_FILE)
  #   importReverseLookupTable(DICT_FILE)
  #   LOOKUP_TABLE_IMPORTED = True
  data = list(data)
  # if there are an odd number of elements, add -1 onto the end
  if len(data) %2 != 0:
    data.append(chr(255))
  words = []
  for chunkIndex in range(0,len(data), 2):
    chunk = data[chunkIndex:chunkIndex+2]
    index = (ord(chunk[1]) << 8) | ord(chunk[0])
    words.append(LOOKUP_TABLE[index])
  return words

def decodeWithDict(words):
  """Convert english text to two byte chunks"""
  # if LOOKUP_TABLE_IMPORTED == False:
  #   importLookupTable(DICT_FILE)
  #   importReverseLookupTable(DICT_FILE)
  #   LOOKUP_TABLE_IMPORTED = True
  decoded =[]
  for word in words:
    lineNum = REVERSE_LOOKUP_TABLE[word]
    decoded.append(chr(lineNum & 255))
    decoded.append(chr((lineNum & (255 <<8)) >> 8))
  if decoded[-1] == chr(255):
    del decoded[-1]
  return decoded

def decodeAsMarket(url):
  """
  Decode data hidden inside a url format for email personalization

  Parameters: url- the url to decode

  Returns: a string with the decoded data

  """
  pattern = '\?qs=(?P<hash>[0-9a-fA-F]*)'
  matches = re.search(pattern, url)
  data = matches.group('hash')
  # strip any padding
  dataLen = int(data[:2], 16)
  data = data[2:dataLen+2]
  data = binascii.unhexlify(data)
  return data

def decodeWithB64(url, cookies):
  """
  Decode the given data as b64 encoded with path and query string
  stuff added

  """
  url.replace("=", "")
  url.replace(".", "=")
  pattern = 'http://[\S]+/(?P<path>[\S]+)\?(?P<query>[\S]+)'
  matches = re.search(pattern, url)
  path = matches.group('path')
  query = matches.group('query')
  # string out the encoding characters and decode the data
  # path.replace("/", "")
  # query.replace(";", "")
  # query.replace("=", "")
  encoded = []
  for key in cookies.keys():
    value = cookies[key]
    key.replace('.', '=')
    value.replace('.', '=')
    encoded.append(key)
    encoded.append(value)
  encoded = str(''.join(encoded))
  urlPortion = str(path + query)
  data = urlsafe_b64decode(urlPortion) + urlsafe_b64decode(encoded)
  return data

def encodeAsOpenSearch(data):
  """
  Hide data inside URLs using open search specification

  Parameters:
  data- the data to encode

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding a dictionary of cookies

  Example: http://www.baidu.com/s?wd=mao+is+cool&rsv_bp=0&ch=&tn=baidu&bar=&rsv_spt=3&ie=utf-8

  """
  urlData = data
  cookies = []
  words = encodeWithDict(urlData)
  urlData = '+'.join(words)
  #Note: we cannot use urlparse here because it capitalizes our hex
  #values and we are using uppercase to distinguish padding and
  #actual text
  # url = 'http://www.baidu.com/s?wd=' + urlData
  url = 'http://' +domain + '/s?wd=' + urlData
  encodedData = {'url':url, 'cookie':cookies}
  return encodedData

def isOpenSearch(url):
  """Return True if this url matches the pattern for Baidu searches"""

  #Example: http://www.baidu.com/s?wd=mao+is+cool&rsv_bp=0&ch=&tn=baidu&bar=&rsv_spt=3&ie=utf-8
  pattern = 'http://' + domain + '/s\?wd=[A-Za-z0-9\'+]+'
  matches = re.match(pattern, url)
  if matches != None:
      return True
  return False

def decodeAsOpenSearch(url):
  """
  Decode data hidden inside a url format for searches

  Parameters: url- the url to decode

  Returns: a string with the decoded data

  """
  # pattern = 'http://www.baidu.com/s\?wd=(?P<englishText>[a-zA-Z0-9+]+)'
  pattern = 'http://'+ domain + '/s\?wd=(?P<englishText>[\S]+)'
  matches = re.match(pattern, url)
  urlData = matches.group('englishText')
  words = urlData.split('+')
  data = decodeWithDict(words)
  return ''.join(data)

def convertCookieInputToOutput(cookies):
  output = {}
  for entry in cookies:
    output[entry['key']] = entry['value']
  return output

def importLookupTable(filename):
  fileP = open(filename, 'r')
  lines = fileP.readlines()
  for index in range(len(lines)):
    lines[index] = lines[index].strip()
  LOOKUP_TABLE = lines
  return lines

def importReverseLookupTable(filename):
  fileP = open(filename, 'r')
  lines = fileP.readlines()
  table = {}
  for index in range(len(lines)):
    line = lines[index].strip()
    table[line] = index
  REVERSE_LOOKUP_TABLE = table
  return table

def decode(protocolUnit):

  """
  Decode the given data after matching the url hiding format

  Parameters: data- the url and cookies to be decoded in the form of a
  dictionary with the url stored under the key 'url' and an array of 0
  or more cookies stored under 'cookie'

  Returns: the decoded data in the form of a string

  """
  url = protocolUnit['url']
  cookies = protocolUnit['cookie']
  data = []
  if isMarket(url):
    data.append(decodeAsMarket(url))
  elif isOpenSearch(url):
    data.append(decodeAsOpenSearch(url))
  # elif isBaidu(url):
  #   data.append(decodeAsBaidu(url))
  else:
  #   data.append(decodeAsBaidu(url))
# FIX
    # return decodeWithB64(str(url), cookies)
    raise UrlEncodeError("Data does not match a known decodable type")
  # print data
  print data[:4]
  for key in cookies.keys():
    data.append(decodeAsCookie(str(key),str(cookies[key])))
  return ''.join(data)
  # return data

LOOKUP_TABLE = importLookupTable(DICT_FILE)
REVERSE_LOOKUP_TABLE = importReverseLookupTable(DICT_FILE)
