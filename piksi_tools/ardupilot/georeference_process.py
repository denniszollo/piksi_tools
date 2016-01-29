#This script should coordinate all the stuff that needs to happen to get a pix4d file



from piksi_tools import interpolate_event_positions
from piksi_tools.ardupilot import query_mavlink
from piksi_tools.ardupilot import mavlink_decode
from pymavlink.DFReader import DFReader_binary
from swiftnav.coord_system import wgsecef2llh_
import csv
import os
from math import sin,cos,tan, atan, asin, pi


def rpy_opk(phi, theta, psi):
  #normal a/c rotation matrix to take a body coordinate and rotate into navigation coordinates
  # we do roll (phi) first
  # pitch (theta) second
  # heading (psi) last
  # see here for info: https://s3.amazonaws.com/mics.pix4d.com/KB/documents/baheimesoeepe.pdf
  #c11 = cos(psi) * cos(theta)
  c12 = cos(psi) * sin(theta) * sin(phi) - sin(psi) * cos(phi)
  #c13 = cos(psi) * sin(theta) * cos(phi) + sin(psi) * sin(phi)
  #c21 = sin(psi) * cos(theta)
  c22 = sin(psi) * sin(theta) * sin(phi) + cos(psi) * cos(phi)
  #c23 = sin(psi) * sin(theta) * cos(phi) + cos(psi) * sin(phi)
  c31 = -sin(theta)
  c32 = cos(theta) * sin(phi)
  c33 = cos(theta) * cos(phi)

  omega = atan(c31/c33)
  phi = asin(-c32)
  kappa = atan(c12/c22)

  return (omega, phi, kappa)


def get_args():
  """
  Get and parse arguments.

  """
  import argparse
  parser = argparse.ArgumentParser(description='Mavlink to SBP JSON converter')
  parser.add_argument("dataflashfile",
                      help="the dataflashfile to convert.")
  parser.add_argument('-o', '--outfile', type=str,
                      default="out.csv",
                      help='specify the name of the file output.')
  parser.add_argument('-i', '--imagenum',
                      default=0, type=int,
                      help='specify the name of the first iamage.')
  parser.add_argument('-b', '--base_posn_ecef', nargs=3, type=float)
  parser.add_argument('-d', '--debounce', type=float, default=500,
                      help='specify the time in milliseconds for debounce')
  args = parser.parse_args()
  return args

def main():
  image_prefix = "DSC"
  image_extension = "JPG"
  file_io = False
  args = get_args()
  filename = args.dataflashfile
  outfile = args.outfile
  print "Writing output to {0}".format(outfile)
  image_num = args.imagenum
  dirname = 'intermediate'
  try:
    os.stat(dirname)
  except:
    os.mkdir(dirname)
  jsonfilename = os.path.join(dirname, filename + '.log.json')
  if not os.path.isfile(jsonfilename):
    print "Extracting SBP"
    f = mavlink_decode.extractSBP(filename)
    g = mavlink_decode.rewrite(f, jsonfilename)
  print "Extracting positions at MSG_EXT_EVENTS with debounce"
  pos_trigger_csv_filename = os.path.join(dirname, filename + '.event.csv')
  if args.base_posn_ecef:
    X = args.base_posn_ecef[0]
    Y = args.base_posn_ecef[1]
    Z = args.base_posn_ecef[2]
    message_type, msg_tow, msg_horizontal,\
    msg_vertical, msg_depth, msg_flag, \
    msg_sats, numofmsg = interpolate_event_positions.collect_positions(jsonfilename, "MsgPosECEF", args.debounce)
  else:
    message_type, msg_tow, msg_horizontal,\
    msg_vertical, msg_depth, msg_flag, \
    msg_sats, numofmsg = interpolate_event_positions.collect_positions(jsonfilename, "MsgPosLLH", args.debounce, lambda x: x.flags>=1)
    print "Interpolating ATT message"
  log = DFReader_binary(filename)
  msg_list = query_mavlink.query_mavlink_timestamp_list(log, msg_tow, 'ATT')
  omega_list = []
  phi_list = []
  kappa_list = []
  for each in msg_list:
    (omega, phi, kappa) = rpy_opk(each['Roll']  * pi / 180.0,
                                  each['Pitch'] * pi / 180.0,
                                  each['Yaw']   * pi / 180.0)
    omega_list.append(omega * 180/pi); phi_list.append(phi*180/pi); kappa_list.append(kappa*180/pi)

  lat_list = []
  lon_list = []
  ht_list = []
  image_list = []
  for x, y, z in zip(msg_horizontal, msg_vertical, msg_depth):
    if args.base_posn_ecef:
      ECEFx = X + x/1000
      ECEFy = Y + y/1000
      ECEFz = Z + z/1000
      out = wgsecef2llh_(ECEFx, ECEFy, ECEFz)
      lat_list.append(out[0] * 180/pi)
      lon_list.append(out[1] * 180/pi)
      ht_list.append(out[2])
    else :
      lat_list.append(x)
      lon_list.append(y)
      ht_list.append(z)
    image = image_prefix + "{:0>5}".format(image_num) + "." + image_extension
    image_list.append(image)
    image_num += 1
  with open(outfile, 'wb') as f:
    writer = csv.writer(f)
    for val in zip(image_list, lat_list, lon_list, ht_list, omega_list, phi_list, kappa_list):
      writer.writerow(val)

if __name__ == "__main__":
  main()
