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
import bitstring as bs
from sbp.client.loggers.json_logger import JSONLogIterator
from sbp.observation import *

RTCM3PREAMB = 0xD3
PRUNIT_GPS = 299792.458     # one light millisecond (meters)
CLIGHT = 299792458.0        # speed of light (m/s)
FREQ1  = 1.57542e9          # L1/E1  frequency (Hz)
debug = False

crc24qtab =[
  0x000000, 0x864CFB, 0x8AD50D, 0x0C99F6, 0x93E6E1, 0x15AA1A, 0x1933EC, 0x9F7F17,
  0xA18139, 0x27CDC2, 0x2B5434, 0xAD18CF, 0x3267D8, 0xB42B23, 0xB8B2D5, 0x3EFE2E,
  0xC54E89, 0x430272, 0x4F9B84, 0xC9D77F, 0x56A868, 0xD0E493, 0xDC7D65, 0x5A319E,
  0x64CFB0, 0xE2834B, 0xEE1ABD, 0x685646, 0xF72951, 0x7165AA, 0x7DFC5C, 0xFBB0A7,
  0x0CD1E9, 0x8A9D12, 0x8604E4, 0x00481F, 0x9F3708, 0x197BF3, 0x15E205, 0x93AEFE,
  0xAD50D0, 0x2B1C2B, 0x2785DD, 0xA1C926, 0x3EB631, 0xB8FACA, 0xB4633C, 0x322FC7,
  0xC99F60, 0x4FD39B, 0x434A6D, 0xC50696, 0x5A7981, 0xDC357A, 0xD0AC8C, 0x56E077,
  0x681E59, 0xEE52A2, 0xE2CB54, 0x6487AF, 0xFBF8B8, 0x7DB443, 0x712DB5, 0xF7614E,
  0x19A3D2, 0x9FEF29, 0x9376DF, 0x153A24, 0x8A4533, 0x0C09C8, 0x00903E, 0x86DCC5,
  0xB822EB, 0x3E6E10, 0x32F7E6, 0xB4BB1D, 0x2BC40A, 0xAD88F1, 0xA11107, 0x275DFC,
  0xDCED5B, 0x5AA1A0, 0x563856, 0xD074AD, 0x4F0BBA, 0xC94741, 0xC5DEB7, 0x43924C,
  0x7D6C62, 0xFB2099, 0xF7B96F, 0x71F594, 0xEE8A83, 0x68C678, 0x645F8E, 0xE21375,
  0x15723B, 0x933EC0, 0x9FA736, 0x19EBCD, 0x8694DA, 0x00D821, 0x0C41D7, 0x8A0D2C,
  0xB4F302, 0x32BFF9, 0x3E260F, 0xB86AF4, 0x2715E3, 0xA15918, 0xADC0EE, 0x2B8C15,
  0xD03CB2, 0x567049, 0x5AE9BF, 0xDCA544, 0x43DA53, 0xC596A8, 0xC90F5E, 0x4F43A5,
  0x71BD8B, 0xF7F170, 0xFB6886, 0x7D247D, 0xE25B6A, 0x641791, 0x688E67, 0xEEC29C,
  0x3347A4, 0xB50B5F, 0xB992A9, 0x3FDE52, 0xA0A145, 0x26EDBE, 0x2A7448, 0xAC38B3,
  0x92C69D, 0x148A66, 0x181390, 0x9E5F6B, 0x01207C, 0x876C87, 0x8BF571, 0x0DB98A,
  0xF6092D, 0x7045D6, 0x7CDC20, 0xFA90DB, 0x65EFCC, 0xE3A337, 0xEF3AC1, 0x69763A,
  0x578814, 0xD1C4EF, 0xDD5D19, 0x5B11E2, 0xC46EF5, 0x42220E, 0x4EBBF8, 0xC8F703,
  0x3F964D, 0xB9DAB6, 0xB54340, 0x330FBB, 0xAC70AC, 0x2A3C57, 0x26A5A1, 0xA0E95A,
  0x9E1774, 0x185B8F, 0x14C279, 0x928E82, 0x0DF195, 0x8BBD6E, 0x872498, 0x016863,
  0xFAD8C4, 0x7C943F, 0x700DC9, 0xF64132, 0x693E25, 0xEF72DE, 0xE3EB28, 0x65A7D3,
  0x5B59FD, 0xDD1506, 0xD18CF0, 0x57C00B, 0xC8BF1C, 0x4EF3E7, 0x426A11, 0xC426EA,
  0x2AE476, 0xACA88D, 0xA0317B, 0x267D80, 0xB90297, 0x3F4E6C, 0x33D79A, 0xB59B61,
  0x8B654F, 0x0D29B4, 0x01B042, 0x87FCB9, 0x1883AE, 0x9ECF55, 0x9256A3, 0x141A58,
  0xEFAAFF, 0x69E604, 0x657FF2, 0xE33309, 0x7C4C1E, 0xFA00E5, 0xF69913, 0x70D5E8,
  0x4E2BC6, 0xC8673D, 0xC4FECB, 0x42B230, 0xDDCD27, 0x5B81DC, 0x57182A, 0xD154D1,
  0x26359F, 0xA07964, 0xACE092, 0x2AAC69, 0xB5D37E, 0x339F85, 0x3F0673, 0xB94A88,
  0x87B4A6, 0x01F85D, 0x0D61AB, 0x8B2D50, 0x145247, 0x921EBC, 0x9E874A, 0x18CBB1,
  0xE37B16, 0x6537ED, 0x69AE1B, 0xEFE2E0, 0x709DF7, 0xF6D10C, 0xFA48FA, 0x7C0401,
  0x42FA2F, 0xC4B6D4, 0xC82F22, 0x4E63D9, 0xD11CCE, 0x575035, 0x5BC9C3, 0xDD8538]

def crc24q(s, crc=0):
  """CRC32 implementation acording to CCITT standards.

  """
  for ch in s:
    crc = ((crc<<8)&0xFFFFFF) ^ crc24qtab[((crc>>16)&0xFF) ^ (ord(ch)&0xFF) ]
    crc &= 0xFFFFFF
  return crc

def phase_minus_pr(obs):
    amb = int(obs.P / 100.0 / PRUNIT_GPS) # light seconds
    pr = int((obs.P / 100.0 - amb * PRUNIT_GPS) / 0.02)
    prc = pr * 0.02 + amb * PRUNIT_GPS
    if debug:
      print "prc (reconstructed pseudorange) is {0} meters".format(prc)
    carrier = float(obs.L.i) \
              + float(obs.L.f) / (1<<8)
    if debug:
      print "carrier is {0} cycles".format(carrier)
    # carrier is in units of cycles,  pr is in units of meters
    # we return # of cycles
    return carrier - prc / (CLIGHT / FREQ1)

def write_int(stream, len, data):
  integer = int(data)
  stream.append(bs.Bits(int=data, length=len))

def write_uint(stream, len, data):
  integer = int(data)
  stream.append(bs.Bits(uint=data, length=len))

def to_lock_time(time):
  if (time < 24):
    return time;
  if (time < 72):
    return (time + 24) / 2;
  if (time < 168):
    return (time + 120) / 4;
  if (time < 360):
    return (time + 408) / 8;
  if (time < 744):
    return (time + 1176) / 16;
  if (time < 937):
    return (time + 3096) / 32;
  return 127;

def sid_to_dict_key(sid):
  return sid.sat

class Nav_Measurement_RTCM(object):
  def __init__(self, packed_obs_content, state_dict):
    self.obs = packed_obs_content
    self.sat = self.obs.sid.sat
    self.amb = int(self.obs.P / 100.0 / PRUNIT_GPS)
    self.pr = int((self.obs.P / 100.0 - self.amb * PRUNIT_GPS) / 0.02)
    cp_minus_pr = (phase_minus_pr(self.obs) + \
                  state_dict[sid_to_dict_key(self.obs.sid)].phase_offset) * \
                  (CLIGHT/ FREQ1)
    #If the phaserange and pseudorange have diverged close to the limits of the
    #data field (20 bits) then we modify the carrier phase by an integer amount
    #to bring it back into range an reset the phase lock time to zero to reset
    #the integer ambiguity.
    #The spec suggests adjusting by 1500 cycles we calculate the range to be
    #+/- 1379 cycles. Limit to just 1000 as that should still be plenty.
    if abs(cp_minus_pr) > (1500 * (CLIGHT / FREQ1)):
      print "out of range cp minus pr {0} > {1}".format(abs(cp_minus_pr), 1500 * CLIGHT / FREQ1)
      print "phase offset is {0}, pr is {1}, amb is {2}, sid {3}".format(state_dict[sid_to_dict_key(self.obs.sid)].phase_offset ,
                                                              self.pr, self.amb, self.sat)
    self.cmc = int(cp_minus_pr / 0.0005)
    self.lock = to_lock_time(state_dict[sid_to_dict_key(self.obs.sid)].lock_time)
    self.cnr = self.obs.cn0
  def __repr__(self):
    return ("<satid> {0} <amb> {1} <pr> {2} <carrier minus "
            "code> {3} <clock> {4} <cnr> {5}").format(self.sat, self.amb,
              self.pr, self.cmc, self.lock, self.cnr)


class RTCM_msg(object):
  def __init__(self):
    self.buff = bs.BitStream()
    self.payload = bs.BitStream()
    self.len = False
    pass

  def _encode_preamble(self, len):
    self.len = len
    write_uint(self.buff, 8, RTCM3PREAMB)
    write_uint(self.buff, 6, 0x00)
    write_uint(self.buff, 10, len)

  def encode_header(self):
    raise "uimplemented"

  def generate_payload(self):
    raise  "unimplemneted"

  def _add_payload(self):
    self.buff.append(self.payload)

  def _set_crc(self):
    write_uint(self.buff, 3, crc24q(self.payload))

  def _frame_msg(self):
    self._encode_preamble(len(self.payload))
    assert len(self.payload) == self.len
    self.encode_header()
    self._add_payload()
    self._set_crc()

  def to_binary(self):
    self._frame_msg()
    return self.buff

debug = False


class RTCM_1002(RTCM_msg):
  def __init__(self, observation_header, observation_array, state_dict):
    super(RTCM_1002, self).__init__()
    self.obs_header = observation_header
    self.obs = observation_array
    self.state_dict = state_dict

  def encode_header(self):
    write_uint(self.buff, 12, 1002)             # message no
    write_uint(self.buff, 12, 1002)       # ref station id
    epoch = self.obs_header.t.tow
    print epoch
    write_uint(self.buff, 30, self.obs_header.t.tow)  # gps epoch time
    write_uint(self.buff, 1 , 0) # synchronous gnss flag
    if debug:
      print "num sats is {0}".format(len(self.obs))
    write_uint(self.buff, 5 , len(self.obs))  # no of satellites
    write_uint(self.buff, 1, 0)         # smoothing indicator */
    write_uint(self.buff, 3, 0)          # /* smoothing interval */
    if debug:
      print "length of preamble plus header is {0}".format(len(self.buff))

  def generate_payload(self):
    for each in self.obs:
      navrtcm = Nav_Measurement_RTCM(each, self.state_dict)
    write_uint(self.payload, 74*len(self.obs), 10)

class ObsState(object):

  def __init__(self, wn, tow, obs):
    self.phase_offset = 0
    self.earliest_lock_wn = 0
    self.earliest_lock_tow = 0
    self.most_recent_lock_indicator = 0
    self.lock_time = 0
    self.set_state(wn, tow, obs)

  def set_state(self, wn, tow, obs):
    self.earliest_lock_wn = wn
    self.earliest_lock_tow = tow
    self.most_recent_lock_indicator = obs.lock
    self.phase_offset = - int(phase_minus_pr(obs)) # cycles
    self.lock_time = 0


  def update(self, wn, tow, obs):
    if(self.most_recent_lock_indicator == obs.lock and wn == self.earliest_lock_wn \
      and (abs(phase_minus_pr(obs) + self.phase_offset)) < 1500):
      self.lock_time = tow - self.earliest_lock_tow
    else:
      print "resetting state for sat {0}".format(obs.sid.sat)
      print "old lock indicator {0} new lock indicator {1} p-pr {2}, po {3}".format(
             self.most_recent_lock_indicator, obs.lock, phase_minus_pr(obs) + self.phase_offset, self.phase_offset)
      self.set_state(wn, tow, obs)

class Sbp2RtcmConverter(object):
  def __init__(self):
    self.state_dict = {} # SID indexed dictionary with state about the SID

  def update_state_dict(self):
    # first make sure a dict is there for each SID, if it's not there, initialize it
    for each in self.obs:
      key = sid_to_dict_key(each.sid)
      if not key in self.state_dict:
        print "wasn't there, making again"
        self.state_dict[key] = ObsState(self.header.t.wn,
                                             self.header.t.tow, each)
      else:
        print "updating {0} with range {1}".format(each.sid.sat, each.P)
        self.state_dict[key].update(self.header.t.wn,
                                            self.header.t.tow, each)

  def obs_callback(self, msg, outfile):
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
    elif (self.header.t.tow == msg.header.t.tow and
    (self.header.n_obs & 0x0F) + 1 == counter):
      for each in msg.obs:
        self.obs.append(each)
      self.header = msg.header
      output = True
    else:
      output = False
    if output and (counter+1) == num_obs:
      self.update_state_dict()
      rtcm_msg = RTCM_1002(self.header, self.obs, self.state_dict)
      rtcm_msg.generate_payload()
      binary = rtcm_msg.to_binary()
      outfile.write(binary.tobytes())

  def eph_callback(self, msg):
    print "eph callback"

def get_args():
  import argparse
  parser = argparse.ArgumentParser(description="SBPJson to RTCM converter")
  parser.add_argument("file",
                      help="specify the SBP Json file to convert to RTCMV3.")
  parser.add_argument("outfile",
                      help="specify the name for the RTCMV3 outputfile.")
  return parser.parse_args()


def wrapper(filename, outfilename):
  # First, we start up an SBP driver reading from STDInput
  conv = Sbp2RtcmConverter()
  first=True
  conv = Sbp2RtcmConverter()
  with JSONLogIterator(filename) as log:
    with open(outfilename, "w+") as outfile:
      mylog = log.next()
      while True:
        try:
          (msg, data) = mylog.next()
          if first:
            print data
            firsttimestamp = data['timestamp']
            first = False
          if type(msg) == MsgObs:
            conv.obs_callback(msg, outfile)
        except StopIteration:
          break


def main():
  args = get_args()
  wrapper(args.file, args.outfile)


if __name__ == "__main__":
  main()
