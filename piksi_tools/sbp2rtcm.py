#!/usr/bin/env python
# Copyright (C) 2015 Swift Navigation Inc.
# Contact: Dennis Zollo <dzollo@swift-nav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import sys
from bitstream import BitStream
from sbp.client.loggers.json_logger import JSONLogIterator
from sbp.observation import *

RTCM3PREAMB = 0xD3
PRUNIT_GPS = 299792.458

def write_uint(stream, len, data):
  integer = int(data)
  if integer < 0:
      error = "negative integers cannot be encoded"
      raise ValueError(error)
  bools = []
  i = 0
  while i < len:
      bools.append(integer & 1)
      integer = integer >> 1
      i+=1
  bools.reverse()
  stream.write(bools, bool)

def write_sint(stream, len, data):
  integer = int(data)
  if integer < 0:
      error = "negative integers cannot be encoded"
      raise ValueError(error)
  bools = []
  i = 0
  while i < len:
      bools.append(integer & 1)
      integer = integer >> 1
      i+=1
  bools.reverse()
  stream.write(bools, bool)


class Nav_Measurement_RTCM(object):
  def __init__(self, packed_obs_content):
    self.obs = packed_obs_content
    self.sat = self.obs.sid.sat
    self.amb = int(self.obs.P / 100.0 / PRUNIT_GPS)
    self.pr = (self.obs.P / 100.0 - self.amb * PRUNIT_GPS) / 0.02
    print self.pr
    self.cmc = 0
    self.lock = 0
    self.cnr = 0
  def __repr__(self):
    return ("<satid> {0} <amb> {1} <pr> {2} <carrier minus "
            "code> {3} <clock> {4} <cnr> {5}").format(self.sat, self.amb,
              self.pr, self.cmc, self.lock, self.cnr)


class RTCM_msg(object):
  def __init__(self):
    self.buff = BitStream()
    self.payload = BitStream()
    pass
  def encode_preamble(self, len):
    write_uint(self.buff, 8, RTCM3PREAMB)
    write_uint(self.buff, 6, 0x00)
    write_uint(self.buff, 10, len)
  def encode_header(self):
    pass
  def generate_payload(self):
    pass

  def set_crc(self):
    pass
  def to_binary(self):
    pass

debug = True


class RTCM_1002(RTCM_msg):
  def __init__(self, observation_header, observation_array):
    super(RTCM_1002, self).__init__()
    self.obs_header = observation_header
    self.obs = observation_array

  def encode_header(self):
    write_uint(self.buff, 12, 1002)             # message no
    write_uint(self.buff, 12, 1002)       # ref station id
    epoch = self.obs_header.t.tow
    print epoch
    write_uint(self.buff, 30, self.obs_header.t.tow)  # gps epoch time
    self.buff.write(False, bool) # synchronous gnss flag
    if debug:
      print "num sats is {0}".format(len(self.obs))
    write_uint(self.buff, 5 , len(self.obs))  # no of satellites
    self.buff.write(False, bool)         # smoothing indicator */
    write_uint(self.buff, 3, 0)          # /* smoothing interval */
    if debug:
      print "length of preamble plus header is {0}".format(len(self.buff))
  def generate_payload(self):
    for each in self.obs:
      navrtcm = Nav_Measurement_RTCM(each)
      print navrtcm
  def frame_msg(self):
    if debug:
      print "length is {0}".format(len(self.payload))
    self.encode_preamble(len(self.payload))
    self.encode_header()
    print self.buff

  def to_binary(self):
    self.frame_msg()
    return self.buff



class Sbp2RtcmConverter(object):
  def __init__(self):
    self.locks = {} # SID indexed dictionary with the last lock time
    self.last_header_tow = 0
    self.last_counter = 0

  def obs_callback(self, msg):
    if(msg.sender == 0):
      return
    num_obs = msg.header.n_obs >> 4
    counter = msg.header.n_obs & ((1 << 4) - 1)
    # if the counter is 0, we reset everything
    if counter == 0:
      self.obs = msg.obs
      self.header = msg.header
      output = True
    # if the time of week is the same from the last header and we didn't skip a packet, update our obs
    #    previous header tow   current tow           previous counter + 1            current counter
    elif self.header.t.tow == msg.header.t.tow and (self.header.n_obs & 0x0F) + 1 == counter:
      for each in msg.obs:
        self.obs.append(each)
      self.header = msg.header
      output = True
    else:
      print "looks like we dropped a packet"
      output = False
    if output and (counter+1) == num_obs:
      print "trying to send these obs"
      print self.obs
      rtcm_msg = RTCM_1002(self.header, self.obs)
      rtcm_msg.generate_payload()
      binary = rtcm_msg.to_binary()

  def eph_callback(self, msg):
    print "eph callback"



def get_args():
  import argparse
  parser = argparse.ArgumentParser(description="SBPJson to RTCM converter")
  parser.add_argument("file",
                      help="specify the SBP Json file to convert to RTCMV3.")
  return parser.parse_args()


def main():
  # First, we start up an SBP driver reading from STDInput
  converter = Sbp2RtcmConverter()
  first=True
  args = get_args()
  conv = Sbp2RtcmConverter()
  with JSONLogIterator(args.file) as log:
    mylog = log.next()
    while True:
      try:
        (msg, data) = mylog.next()
        if first:
          print data
          firsttimestamp = data['timestamp']
          first = False
        if type(msg) == MsgObs:
          conv.obs_callback(msg)
      except StopIteration:
        break




if __name__ == "__main__":
  main()
