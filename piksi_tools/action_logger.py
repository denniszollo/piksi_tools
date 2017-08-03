#!/usr/bin/env python
import piksi_tools.serial_link as sl
import piksi_tools.diagnostics as ptd
from sbp.client import Handler, Framer, Forwarder
from sbp.logging import *
from sbp.tracking import MsgTrackingState, MsgTrackingStateDepA
from sbp.piksi import SBP_MSG_MASK_SATELLITE, SBP_MSG_RESET, MsgMaskSatellite, MsgReset
from sbp.system import SBP_MSG_HEARTBEAT, MsgStartup, MsgHeartbeat
from sbp.table import dispatch

import time
import sys
import random
import threading
import struct

DEFAULT_POLL_INTERVAL = 300 # Seconds
DEFAULT_MIN_SATS = 5 # min satellites to try and retain

class LoopTimer(object):
  """
  The :class:`LoopTimer` calls a function at a regular interval.
  It is intended to be instantiated from a subclass instance of TestState to call
  TestStateSubclass.action() at a regular interval. The implementation is emulated
  from a simliar instance submitted via stack overflow
  http://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds

  Parameters
  ----------
  interval: int
    number of seconds between calls
  hfunction : handle to function
    function to call periodically
  """
  def __init__(self, interval, hfunction):
    self.interval = interval
    self.hfunction = hfunction
    self.thread = threading.Timer(self.interval, self.handle_function)

  def handle_function(self):
    """
    Handle function is called each time the timer trips.
    It sets up another timer to call itself again in the future.
    """
    self.hfunction()
    self.thread = threading.Timer(self.interval, self.handle_function)
    self.start()

  def start(self):
    """
    Starts the periodic timer thread.
    """
    print "in start"
    self.thread.start()

  def cancel(self):
    """
    Cancels any current timer threads.
    """
    self.thread.cancel()
    self.thread = None

  def reset(self):
    print "in reset"
    self.cancel()
    self.thread = threading.Timer(self.interval, self.handle_function)
    self.start()

class TestState(object):
  """
  Super class for representing state and state-based actions during logging.

  Parameters
  ----------
  handler: sbp.client.handler.Handler
      handler for SBP transfer to/from Piksi.
  filename : string
    File to log to.
  """
  def __init__(self, handler, interval):
    self.init_time = time.time()
    self.handler = handler
    self.timer = LoopTimer(interval, self.action)
    handler.add_callback(self.process_message)
  
  def __enter__(self):
    self.timer.start()
    return self

  def __exit__(self, *args):
    self.timer.cancel()
  
  def process_message(self, msg, **kwargs):
    """
    Stub for processing messages from device. Should be overloaded in sublcass.
    """
    raise NotImplementedError("action not implemented!")

  def action(self):
    """
    Stub for communicating with device. Should be overloaded in subclass.
    """
    raise NotImplementedError("action not implemented!")



class BootloadTestState(TestState):
  """
  Super class for representing state and state-based actions during logging.

  Parameters
  ----------
  handler: sbp.client.handler.Handler
      handler for SBP transfer to/from Piksi.
  filename : string
    File to log to.
  """
  def __init__(self, handler, interval, filename='out.csv'):
    super(BootloadTestState, self).__init__(handler, interval)
    self.state=-1
    self.NUM_STATES = 9
    self.STATE_DESC_DICT = {
     -1: 'initialization of class / invalid',
     0: 'reset commanded',
     1: 'got first valid sbp message',
     2: 'got MsgStartup',
     3: 'got first heartbeat',
     4: 'upgrade actually started',
     5: 'upgrade completed successefully',
     6: 'timed out waiting for upgrade completed',
     7: 'Nap verification failed',
     8: 'Upgrade failed (upgrade_tool return code wrong)'}
    self.filename = filename
    self.file = open(self.filename, 'w')
    self.file.write(','.join([str(self.STATE_DESC_DICT[x]) for x in range(0, self.NUM_STATES)])+ '\n')
    self.file.close()
    self.reset_time = 0
    self.state_dict = None

  def log_state_trans(self):
    self.state_dict[self.state] = time.time() - self.reset_time
    print "state transition to state {0}, after {1} seconds". format(self.state, self.state_dict[self.state])

  def clear_state(self):
    self.state = 0
    self.state_dict={0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}

  def log_state_dict(self):
    self.file = open(self.filename, 'a')
    self.file.write(','.join([str(self.state_dict[x]) for x in range(0, self.NUM_STATES)])+ '\n')
  
  def __enter__(self, *args):
    self.reboot_and_log() 
  
  def __exit__(self, *args):
    self.timer.cancel()
    self.file.close()
 
  def process_message(self, msg, **kwargs):
    """
    Wait for logs, heartbeats, and MsgStartup.
    """
    msg = dispatch(msg)
    if self.state==0:
      self.state = 1
      self.log_state_trans()
    if isinstance(msg, MsgStartup) and self.state < 4:
      print "got startup"
      self.state=2
      self.log_state_trans()
    if isinstance(msg, MsgHeartbeat) and self.state < 4 and self.state_dict[3] == 0:
      print "got heartbeat"
      self.state=3
      self.log_state_trans()
    if isinstance(msg, MsgLog):
      print msg.text
      if msg.text.startswith("Performing"):
        self.state=4
        self.log_state_trans()
      if msg.text.startswith("Upgrade completed successfully. "):
        self.state=5
        self.log_state_trans()
        self.reboot_and_log()
      if msg.text.startswith("NAP Verification"):
        self.state=7
        self.log_state_trans()
        self.reboot_and_log()
      if msg.text.startswith("ERROR: Upgrade was unsuccessful"):
        self.state=8
        self.log_state_trans()
        self.reboot_and_log()
  
  def reboot_and_log(self):
    if self.state_dict:
       self.log_state_dict()
    self.clear_state()
    self.reset_time = time.time()
    self.timer.reset()
    self.handler(MsgReset(flags=0))
    time.sleep(0.25)
    
  def action(self):
    """
    Stub for communicating with device. Should be overloaded in subclass.
    """
    print "Hit restart timer without getting to completion after {0} seconds".format(time.time() - self.reset_time)
    self.state=6
    self.log_state_trans()
    self.reboot_and_log()

class DropSatsState(TestState):
  """
  Subclass of testState that periodically drops a random number of satellite
  above some minimum value

  Parameters
  ----------
  handler: sbp.client.handler.Handler
    handler for SBP transfer to/from Piksi.
  sbpv: (int, int)
    tuple of SBP major/minor version.
  interval : int
    number of seconds between sending mask tracking message
  min sats : int
    number of satellites to never go below
  debug : bool
    Print out extra info?
  """
  def __init__(self, handler, sbpv, interval, min_sats, debug=False):
    super(DropSatsState, self).__init__(handler)
    self.sbpv = sbpv
    self.min_sats = min_sats
    self.debug = debug

    # state encoding
    self.num_tracked_sats = 0
    self.prn_status_dict = {}
    self.channel_status_dict = {}

  def __enter__(self):
    self.timer.start()
    return self

  def __exit__(self, *args):
    self.timer.cancel()

  def process_message(self, msg, **metadata):
    """
    Process SBP messages and encode into state information

    Parameters
    ----------
    msg: sbp object
      not yet dispatched message received by device
    """
    msg = dispatch(msg)
    if isinstance(msg, MsgTrackingState) or isinstance(msg, MsgTrackingStateDepA):
      if self.debug:
        print "currently tracking {0} sats".format(self.num_tracked_sats)
      self.num_tracked_sats = 0
      for channel, track_state in enumerate(msg.states):
        try:
          # MsgTrackingState
          prn = track_state.sid.sat
          if ((track_state.sid.constellation == 0) and (track_state.sid.band == 0)):
            prn += 1
        except AttributeError:
          # MsgTrackingStateDepA
          prn = track_state.prn + 1
        if track_state.state == 1:
          self.num_tracked_sats += 1
          self.prn_status_dict[prn] = channel
          self.channel_status_dict[channel] = prn
        else:
          if self.prn_status_dict.get(prn):
            del self.prn_status_dict[prn]
          if self.channel_status_dict.get(channel):
            del self.channel_status_dict[channel]

  def drop_prns(self, prns):
    """
    Drop Prns via sending MsgMaskSatellite to device

    Parameters
    ----------
    prns : int[]
      list of prns to drop
    """
    FLAGS = 0x02 # Drop from tracking, don't mask acquisition.
    if self.debug:
      print "Dropping the following prns {0}".format(prns)
    for prn in prns:
      if self.sbpv < (0, 49):
        # Use pre SID widening Mask Message - have to pack manually.
        msg = struct.pack('BB', FLAGS, prn-1)
        self.handler.send(SBP_MSG_MASK_SATELLITE, msg)
      else:
        # Use post SID widening Mask Message.
        msg = MsgMaskSatellite(mask=FLAGS, sid=int(prn)-1)
        self.handler(msg)

  def get_num_sats_to_drop(self):
    """
    Return number of satellites to drop.
    Should drop a random number of satellites above self.min_sats
    If we haven't achieved min sats, it drops zero
    """
    max_to_drop = max(0, self.num_tracked_sats-self.min_sats)
    # end points included
    return random.randint(0, max_to_drop)

  def drop_random_number_of_sats(self):
    """
    Perform drop of satellites.
    """
    num_drop = self.get_num_sats_to_drop()
    if num_drop > 0:
      prns_to_drop = random.sample(self.channel_status_dict.values(), num_drop)
      if self.debug:
        print ("satellite drop triggered: "
                "will drop {0} out of {1} sats").format(num_drop,
                                                          self.num_tracked_sats)
      self.drop_prns(prns_to_drop)

  def action(self):
    """
    Overload of superclass' action method.  Drops a random number of sats above
    some minimum value.
    """
    self.drop_random_number_of_sats()

def get_args():
  """
  Get and parse arguments.
  """
  import argparse
  parser = sl.base_cl_options()
  parser.add_argument("-i", "--interval",
                      default=[DEFAULT_POLL_INTERVAL], nargs=1,
                      help="Number of seconds between satellite drop events.")
  parser.add_argument("-m", "--minsats",
                      default=[DEFAULT_MIN_SATS], nargs=1,
                      help="Minimum number of satellites to retain during drop events.")
  parser.add_argument( "--timeout",
                      default=None, 
                      help="timeout.")
  return parser.parse_args()

def main():
  """
  Get configuration, get driver, get logger, and build handler and start it.
  Create relevant TestState object and perform associated actions.
  Modeled after serial_link main function.
  """
  args = get_args()
  port = args.port
  baud = args.baud
  timeout = args.timeout
  log_filename = args.logfilename
  log_dirname = args.log_dirname
  if not log_filename:
    log_filename=sl.logfilename()
  if log_dirname:
    log_filename = os.path.join(log_dirname, log_filename)
  interval = int(args.interval[0])
  minsats = int(args.minsats[0])

  # Driver with context
  with sl.get_driver(args.ftdi, port, baud) as driver:
    # Handler with context
    with Handler(Framer(driver.read, driver.write, args.verbose)) as link:
      # Logger with context
      with sl.get_logger(args.log, log_filename) as logger:
      # print out SBP_MSG_PRINT_DEP messages
        #link.add_callback(sl.log_printer, SBP_MSG_LOG)
        # add logger callback
        Forwarder(link, logger).start()
        try:
          # Get device info
          # add Teststates and associated callbacks
          with BootloadTestState(link, interval) as boot:

            if timeout is not None:
              expire = time.time() + float(args.timeout)

            while True:
              if timeout is None or time.time() < expire:
              # Wait forever until the user presses Ctrl-C
                time.sleep(1)
              else:
                print "Timer expired!"
                break
          if not link.is_alive():
            sys.stderr.write("ERROR: Thread died!")
            sys.exit(1)
        except KeyboardInterrupt:
          # Callbacks call thread.interrupt_main(), which throw a KeyboardInterrupt
          # exception. To get the proper error condition, return exit code
          # of 1. Note that the finally block does get caught since exit
          # itself throws a SystemExit exception.
          sys.exit(1)

if __name__ == "__main__":
  main()
