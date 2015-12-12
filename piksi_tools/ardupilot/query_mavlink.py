import datetime as dt
from pymavlink.DFReader import DFReader_binary
from swiftnav.gpstime import datetime2gpst, gpst_components2datetime
TZ_OFFSET = - 8 * 60 * 60
# For an individual timestamp, pull out prior and post messages of a particular type



# For a particular timestamp, Pull out next messages of a particular type surrounding the
# GPStimestamp (precise to nanosecond) passed in
# Return data will be a dictionary that looks like this
# MSG_TYPE: (prior_message1 , post_message1)

def query_mavlink_single_timestamp(log, timestamp, msg_type):
  iter_list = [msg_type]
  if 'GPS' not in iter_list:
    iter_list.append('GPS')
  prior_msg = None
  prior_prior_msg = None
  post_msg = None
  return_dict = {}
  base_time = datetime2gpst(dt.datetime.fromtimestamp(log.clock.timebase)).tow
  while True:
    # we use mavlink's recv_match function to iterate through logs
    # and give us the requested messages
    m = log.recv_match(type=iter_list)
    if m is None:
      print "End of file reached before timestamp found, using prior two messages"
      return (prior_prior_msg, prior_msg)
    if m.get_type() == 'GPS':
      base_time = m.GMS - m.TimeUS/1000.0
    if base_time and m.get_type() == msg_type:
      msg_time = base_time + m.TimeUS/1000.0
      mdict = m.to_dict()
      mdict['msg_time'] = msg_time
      if not prior_msg or msg_time <= int(timestamp):
        prior_prior_msg = prior_msg
        prior_msg = mdict
      else:
        post_msg = mdict
        # once we have a post msg for each msg we care about, we break
        break
  if prior_msg == None or post_msg == None:
      print "got a none at msg_Time {0}".format(msg_time)
  return (prior_msg, post_msg)

def interp(msg_a, msg_b, timestamp):
  interp_msg = {}
  print "first message time {0} and second is {1}. timestamp is {2}".format(
    msg_a['msg_time'], msg_b['msg_time'], timestamp)
  time_diff = msg_b['msg_time'] - msg_a['msg_time']
  t = int(timestamp) - msg_a['msg_time']
  for field in msg_a.iterkeys():
    if type(msg_b[field]) in (float, int):
      slope = (msg_b[field] - msg_a[field])/time_diff
      interp_msg[field] = msg_a[field] + slope * t
    else:
      interp_msg[field] = msg_a[field]
  return interp_msg

def query_mavlink_timestamp_list(log, timestamps, msg_type):
 output_list = []
 for timestamp in timestamps:
    (prior, post) = query_mavlink_single_timestamp(log, timestamp, msg_type)
    #print prior
    #print post
    msg = interp(prior, post, timestamp)
    output_list.append(msg)
 print "output_list is {0}".format(output_list)
 return output_list

def get_args():
  """
  Get and parse arguments.

  """
  import argparse
  parser = argparse.ArgumentParser(description='Mavlink to SBP JSON converter')
  parser.add_argument('-t', '--type', default='ATT',
                      help="the message type to interpolate")
  parser.add_argument('-o', '--output', default='output.csv',
                      help="the output csv file")
  parser.add_argument("-f", "--Dataflashfile",
                      help="the mavlink hdf5")
  parser.add_argument("timestamps", type=float, nargs='+',
                      help="the piksi hdf5")
  args = parser.parse_args()
  return args



def main():
  import csv
  args = get_args()
  log = DFReader_binary(args.Dataflashfile)
  msg_dict = query_mavlink_timestamp_list(log, args.timestamps, args.type)
  print msg_dict
  with open(args.output, 'wb') as output_file:
    dict_writer = csv.DictWriter(output_file, msg_dict[0].keys())
    dict_writer.writeheader()
    dict_writer.writerows(msg_dict)
if __name__ == "__main__":
  main()


