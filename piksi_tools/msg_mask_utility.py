from sbp import *




from sbp.navigation import SBP_MSG_BASELINE_NED, MsgBaselineNED, SBP_MSG_GPS_TIME, SBP_MSG_VEL_NED, SBP_MSG_POS_LLH, SBP_MSG_DOPS
from sbp.observation import SBP_MSG_OBS, SBP_MSG_BASE_POS, SBP_MSG_EPHEMERIS
from sbp.tracking import SBP_MSG_TRACKING_STATE
from sbp.acquisition import SBP_MSG_ACQ_RESULT
from sbp.piksi import SBP_MSG_IAR_STATE, SBP_MSG_THREAD_STATE, SBP_MSG_UART_STATE
from sbp.system import SBP_MSG_HEARTBEAT
from sbp.settings import SBP_MSG_SETTINGS
from sbp.logging import SBP_MSG_PRINT
from sbp.table import _SBP_TABLE

def MSB( n ):
  ndx = 0
  while ( 1 < n ):
    n = ( n >> 1 )
    ndx += 1

  return ndx


def LSB( n ):
  ndx = 0
  while ( (n & 0x1) != 1):
    n = ( n >> 1 )
    ndx += 1
  return ndx

def PP(mydict, condition):
  for key,value in mydict.iteritems():
      if condition(key):
        print "{:32s}".format(value.__name__) + " : " +  "{0:04X} : {1:016b}".format(key,key)


msg_want={}
msg_dont_want={}

msg_want_list= [
SBP_MSG_BASELINE_NED,
SBP_MSG_GPS_TIME,
SBP_MSG_VEL_NED,
SBP_MSG_POS_LLH,
SBP_MSG_DOPS,
SBP_MSG_OBS
]

msg_exclude_list=[
SBP_MSG_ACQ_RESULT,
SBP_MSG_TRACKING_STATE,
SBP_MSG_THREAD_STATE,
SBP_MSG_UART_STATE
]
msg_list2 = [SBP_MSG_SETTINGS, SBP_MSG_EPHEMERIS, SBP_MSG_BASE_POS, SBP_MSG_OBS]

mask = 0
for each in msg_want_list:
  msb = MSB(each)
  lsb = LSB(each)
  mask |= (1<<msb)
  msg_want[each] = _SBP_TABLE[each]

for each in msg_exclude_list:
  msg_dont_want[each] = _SBP_TABLE[each]

print "\nthe messages we want are:"
PP(msg_want, lambda x : x&0xFFFF)

print "\n the messages we don't want are:"
PP(msg_dont_want, lambda x : x&0xFFFF)

print "integer masks is {0}, hex mask is {1:04X}\nBinary mask is {2:016b}".format(mask,mask,mask)
print "\nthe following messages will be let through with the mask\n"
PP(_SBP_TABLE, lambda x : x&mask)
print "\nthe following messages will be excluded with the mask\n"
PP(_SBP_TABLE, lambda x : not(x&mask))
