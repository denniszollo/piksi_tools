#This script should coordinate all the stuff that needs to happen to get a pix4d file



from piksi_tools import interpolate_event_positions
from piksi_tools.ardupilot import query_mavlink
from piks_tools.ardupilot import mavlink_decode
import os



def get_args():
  """
  Get and parse arguments.

  """
  import argparse
  parser = argparse.ArgumentParser(description='Mavlink to SBP JSON converter')
  parser.add_argument("dataflashfile",
                      help="the dataflashfile to convert.")
  parser.add_argument('-o', '--outfile',
                      default=["out.csv"],
                      help='specify the name of the file output.')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  filename = args.dataflashfile
  root = os.path.basename(outfile)
  dirname = os.path.dirname(os.path.join(root, 'intermediate'))
  try:
    os.stat(dirname)
  except:
    os.mkdir(dirname)
  outfile = args.outfile[0]
  print "Extracting SBP"
  f = mavlink_decode.extractSBP(filename)
  jsonfilename = os.path.join(basename, filename + '.log.json')
  g = mavlink_decode.rewrite(f, jsonfilename)
  print "Extracting positions at MSG_EXT_EVENTS with debounce"
  pos_trigger_csv_filename = os.path.join(basename, filename + '.event.csv')
  write_positions(jsonfilename, pos_trigger_csv_filename, "MsgBaselineNed", 1000)
  with open(pos_trigger_csv_filename) as pos_trigger_csvfd:
  	pos_trigger_csv = csv.reader(pos_trigger_csvfd)
  	for each in pos_trigger_csv:
  		print each
  print "Interpolating ATT message"
  with DFReader_binary(args.Dataflashfile) as log:
  	msg_dict = query_mavlink_timestamp_list(log, args.timestamps, args.type)
if __name__ == "__main__":
  main()
