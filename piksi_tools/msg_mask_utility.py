from sbp import *




from sbp.navigation import SBP_MSG_BASELINE_NED, MsgBaselineNED, SBP_MSG_GPS_TIME, SBP_MSG_VEL_NED, SBP_MSG_POS_LLH, SBP_MSG_DOPS
from sbp.observation import SBP_MSG_OBS, SBP_MSG_BASE_POS, SBP_MSG_EPHEMERIS
from sbp.tracking import SBP_MSG_TRACKING_STATE
from sbp.piksi import SBP_MSG_IAR_STATE
from sbp.system import SBP_MSG_HEARTBEAT
from sbp.settings import SBP_MSG_SETTINGS
msg_list1 = [
SBP_MSG_BASELINE_NED,
SBP_MSG_GPS_TIME,
SBP_MSG_VEL_NED,
SBP_MSG_POS_LLH,
SBP_MSG_DOPS,
SBP_MSG_TRACKING_STATE,
SBP_MSG_IAR_STATE,
SBP_MSG_HEARTBEAT
]
msg_list2 = [SBP_MSG_SETTINGS, SBP_MSG_EPHEMERIS, SBP_MSG_BASE_POS, SBP_MSG_OBS]

mask = 0
for each in msg_list2:
  mask = mask|each


print mask
