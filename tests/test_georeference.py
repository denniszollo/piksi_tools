import piksi_tools.ardupilot.georeference_process as g
import math

def test_rpy_opk():
  #test that 0 is 0
  assert g.rpy_opk(0,0,0) == (0,0,0)
  # test that rotating the aircraft about yaw results in negative roll pitch yaw
  assert g.rpy_opk(0,0,math.pi/2) == (0,0, -math.pi/2)
  print g.rpy_opk(0 ,math.pi/2, 0)
  assert g.rpy_opk(0,math.pi/2,0) == (math.pi/2,0, 0)