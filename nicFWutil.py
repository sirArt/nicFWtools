#!/usr/bin/env python3
import serial
import sys
import argparse
from time import sleep

DEFAULT_DEVICE = "/dev/ttyUSB0"
DEFAULT_SERIAL_TIMEOUT = 1
DEFAULT_KEY_PUSH_TIME = 0.33        # time to sleep after each key send/release action

# nicFW commands
CMD_START_REMOTE_SESSION    = b'\x4A' # w/  Ack
CMD_END_REMOTE_SESSION      = b'\x4B' # w/  Ack
CMD_READ_CHANNEL            = b'\x30' # w/  Ack
CMD_WRITE_CHANNEL           = b'\x31' # w/  Ack
CMD_READ_BATTERY_ADC        = b'\x32' # w/  Ack
CMD_DISABLE_RADIO           = b'\x45' # w/  Ack
CMD_ENABLE_RADIO            = b'\x46' # w/  Ack
CMD_FLASHLIGHT_ON           = b'\x47' # w/o Ack
CMD_FLASHLIGHT_OFF          = b'\x48' # w/o Ack
CMD_RESET_RADIO             = b'\x49' # w/o Ack

# dict for storing single channel data
channel = {
    "number": 0,
    "name" : "",
    "rx_f": 0,
    "tx_f": 0,
    "rx_subtone" : 0,
    "tx_subtone" : 0,
    "tx_power" : 0,
    "groups_str" : "0000",
    "modulation" : "",
    "bandwidth" : "",
    "is_empty" : True
}

# args
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device", help="serial device to communicate with radio (default /dev/ttyUSB0)")
parser.add_argument("-c", "--channel", type=int, help="channel number to edit/update/remove")
parser.add_argument("-n", "--name", help="channel name")
parser.add_argument("-tx", "--tx", type=int, help="TX frequency")
parser.add_argument("-rx", "--rx", type=int, help="RX frequency")
parser.add_argument("-txc", "--tx-ctcss", type=int, help="TX CTCSS tone")
parser.add_argument("-rxc", "--rx-ctcss", type=int, help="RX CTCSS tone")
parser.add_argument("-p", "--power", type=int, help="TX power")
parser.add_argument("-m", "--modulation", help="modulation")
parser.add_argument("-b", "--bandwidth", help="bandwidth")
parser.add_argument("-g", "--groups", help="groups to add channel to (eg. ABCD, A00F)")
parser.add_argument("-r", "--reset", action='store_true', help="reset radio")
parser.add_argument("--remove", action='store_true', help="remove channel")
parser.add_argument("-u", "--update", action='store_true', help="update existing channel")
parser.add_argument("-w", "--write", action='store_true', help="create new channel/overwrite existing one")
parser.add_argument("-f1", "--flashlight-on", action='store_true', help="turn flashlight ON")
parser.add_argument("-f0", "--flashlight-off", action='store_true', help="turn flashlight OFF")
parser.add_argument("-k", "--key", help="send KEY(s) sequence to radio")
parser.add_argument("-e", "--export-csv", help="export channels to CSV file")
parser.add_argument("-f", "--fixed-width", action='store_true', help="use fixed width data when exporting CSV")
parser.add_argument("-i", "--import-csv", help="import channels from CSV file")
parser.add_argument("--debug", action='store_true', help="enable debug messages")
args = parser.parse_args()

debug = args.debug

# check for no args
if not any(vars(args).values()):
    parser.print_help()
    sys.exit(2)

# count specified channel actions
action_count = 0
for i in (args.write, args.update, args.remove):
    if i == True:
        action_count += 1

# count specified modifiers
modifiers_count = 0
for i in (args.name, args.power, args.tx_ctcss, args.rx_ctcss, args.rx, args.tx, args.modulation, args.bandwidth, args.groups):
    if i != None:
        modifiers_count += 1

# check for multiple channel actions at once
if action_count > 1:
    print("[ERR] choose only one action from [write/update/remove].")
    sys.exit(2)

# check if modifiers is used with remove channel action
if args.remove != False and modifiers_count > 0:
    print("[ERR] channel modifiers can't be used with channel remove action.")
    sys.exit(2)

# check if at least one modifier is used with update channel action
if args.update != False and modifiers_count == 0:
    print("[ERR] Update channel action need at least one channel modifier.")
    sys.exit(2)

# check for modifiers used without proper channel action
if modifiers_count > 0 and args.update == False and args.write == False:
    print("[ERR] channel modifiers used without channel action.")
    sys.exit(2)

# check for channel modifiers used with import/export action
if modifiers_count > 0 and (args.export_csv != None or args.import_csv != None):
    print("[ERR] channel modifiers used without import/export action.")
    sys.exit(2)

# check for using fixed width data without export action
if args.fixed_width != False and args.export_csv == None:
    print("[ERR] fixed width data  modifier used without export action.")
    sys.exit(2)

# check for using import and export action at once
if args.import_csv != None and args.export_csv != None:
    print("[ERR] import and export action used at once.")
    sys.exit(2)

# require channel number for channel actions
if args.channel == None:
    if args.write != False or args.update != False or args.remove != False:
        print("[ERR] channel number has been not specified.");
        exit (2)
 
# if device is not specified, use default one
device = args.device
if device is None:
    device = DEFAULT_DEVICE

if debug:
    print("[DBG] Using '{}' device...".format(device))

# Try to open serial device
try:
    port = serial.Serial(device, baudrate=38400, timeout=DEFAULT_SERIAL_TIMEOUT)
except serial.serialutil.SerialException:
    print("[ERR] problem occured when trying to open '{}' device".format(args.device))
    sys.exit(2)


def write_cmd(cmd, check_ack=False):
    port.write(cmd)
    if check_ack == True:
        ack = port.read(1)
        if ack != cmd:
            print("[ERR] Unable to communicate with nicFW -- there was no valid ACK for {} command ({} recaived).".format(cmd,ack))
            sys.exit(2)

def disable_radio():
    write_cmd(CMD_DISABLE_RADIO, check_ack=True)

def enable_radio():
    write_cmd(CMD_ENABLE_RADIO, check_ack=True)

def reset_radio():
    write_cmd(CMD_RESET_RADIO)

def enable_remote():
    write_cmd(CMD_START_REMOTE_SESSION)

def disable_remote():
    write_cmd(CMD_END_REMOTE_SESSION)

# calculate checksum of bytearray
def calc_checksum(bytes):

    checksum = 0

    for b in bytes:
        checksum += b

    return (checksum % 256).to_bytes(1);

exit_info = None
def exit(err_code):
    if exit_info != None:
        print(exit_info)
    sys.exit(err_code)

# convert variable to int
# - if variable is str check if contains only digits
def conv2int(desc, var):

    if isinstance(var, str):
        if var.isnumeric() == False:
            print("[ERR] {} must contain only digits, but additional characters in '{}' has been found.".format(desc,var))
            exit(2)
        return int(var)

    else:
        return var

# check if channel numer is in range
def check_channel_number(channel_number):

    number = conv2int ("Channel number", channel_number)

    if number < 1 or number > 198:
        print("[ERR] wrong channel number '{}' -- should be in the range from 1 to 198.".format(channel_number))
        exit(2)

    return number

# validate group names
def check_groups(groups_str):

    groupsUP = ""

    for group in groups_str:

        group = group.upper()
        groupsUP += group

        if (ord(group) < 65 or ord(group)>79) and group != '0': # 0 for allowing eg. 000A to assing only 4th group
            print("[ERR] group should be letter betwen A-O (or 0 for group) but '{}' has been found".format(group))
            sys.exit(1)

    if len(groups_str)>4:
        print ("[ERR] you can assign up to 4 groups only.")
        exit(2)

    return groupsUP

# validade channel name
# TODO any forbidden characters in name?
def check_name(name):

    name_len = len(name)

    if name_len > 12:
        print("[WARN] name has been trimmed to 12 characters.")
        name = name[:12]
    # fill name to 12 bytes
    if name_len < 12:
        for i in range(12-name_len):
            name += '\0' # fill up with \0s

    return name

# validate frequency
def check_frequency(frequency):

    number = conv2int ("Frequency", frequency)

    if number < 1800000 or number > 130000000:
        print("[ERR] Frequency should be in the range from 1800000 to 130000000.")
        exit(2)

    return number

# check subtone
# TODO add supporot for DCS
def check_subtone(subtone):

    number = conv2int ("Subtone", subtone)

    if (number < 670 or number > 2541) and number != 0:
        print("[ERR] Subtone should be in the range from 670 to 2541 range (or 0 to disable).")
        exit(2)

    return number

def check_power(power):

    number = conv2int ("Power", power)

    if number < 0 or number > 255:
        print("[ERR] Power should be in the range from 0 to 255.")
        exit(2)

    return number

def check_bandwidth(bandwidth):

    if bandwidth.upper() in [ 'WIDE', 'NARROW' ]:
       return bandwidth

    else:
        print("[ERR] Bandwidth should be in [ 'Wide', 'Narrow' ], but '{}' found".format(bandwidth))
        exit(2)

    return bandwidth

def check_modulation(modulation):

    if modulation.upper() in [ 'AUTO', 'FM', 'AM', 'USB' ]:
       return modulation

    else:
        print("[ERR] Modulation should be in [ 'Auto', 'FM', 'AM', 'USB' ], but '{}' found".format(modulation))
        exit(2)

    return modulation

# convert group letter (A-O) to number (1-15)
def group_a2i(group):

    if ord(group) < 65 or ord(group)>79:
        return 0

    else:
        return ord(group.upper())-64

# convert group string to group bytes[2]
def group_s2b(groups_str):

    for i in range(0,4-len(groups_str)):
        groups_str += '@' # fill up undefined groups

    groups_arr = bytearray(2)
    groups_arr[0] |= group_a2i(groups_str[0])
    groups_arr[0] |= group_a2i(groups_str[1]) << 4 
    groups_arr[1] |= group_a2i(groups_str[2])
    groups_arr[1] |= group_a2i(groups_str[3]) << 4 

    return groups_arr

# convert array[4] of group numbers to array[4]/string of letters
def group_an2s(group_arr):

    str = ""

    for group in group_arr:
        if group > 0 and group<=15:
            str += chr(group+64)
        else:
            str += '0'

    return str

# convert group bytes[2] to array[4] of group numbers
def group_b2an(group_bytes):

    group_array = bytearray(4)

    group_array[0] = group_bytes[0] & 0b00001111;
    group_array[1] = group_bytes[0] >> 4;
    group_array[2] = group_bytes[1] & 0b00001111;
    group_array[3] = group_bytes[1] >> 4;

    return group_array

# DEBUG groups
#ga = group_s2b("A0C@")
#gs = group_an2s(group_b2an(ga))
#print("{} : {}".format(ga,gs))
#sys.exit(1)

# print channel data
def print_channel():

    print ("{:10s} : CH-{:03d}".format("channel", channel['number']))
    print ("{:10s} : {}".format("name", channel['name']))
    print ("{:10s} : {}".format("RX freq", channel['rx_f']))
    print ("{:10s} : {}".format("TX freq", channel['tx_f']))
    print ("{:10s} : {}".format("RX subtone", channel['rx_subtone']))
    print ("{:10s} : {}".format("TX subtone", channel['tx_subtone']))
    print ("{:10s} : {}".format("TX power", channel['tx_power']))
    print ("{:10s} : {}".format("group", channel['groups_str'])) # group_an2s(group_array')
    print ("{:10s} : {}".format("bandwidth", channel['bandwidth']))
    print ("{:10s} : {}".format("modulation", channel['modulation']))


# decode channel data received from radio
def decode_channel_data(data):

    global channel

    group_array = bytearray(4)

    channel['rx_f']         = int.from_bytes(data[0:4], 'little')
    channel['tx_f']         = int.from_bytes(data[4:8], 'little')
    channel['rx_subtone']   = int.from_bytes(data[8:10], 'little')
    channel['tx_subtone']   = int.from_bytes(data[10:12], 'little')
    channel['tx_power']     = data[12]
#    group_bytes = int.from_bytes(data[13:14], 'little')
#    mod_bw = int.from_bytes(data[15:16], 'little')
#    reserved = int.from_bytes(data[16:20], 'little')
    channel['name']         = data[20:32].decode('utf-8', 'replace')

    channel['groups_str'] = group_an2s(group_b2an([data[13],data[14]]))

    if data[15] & 0b00000001:
        bandwidth = "Narrow"
    else:
        bandwidth = "Wide"
    
    channel['bandwidth'] = bandwidth

    match (data[15] >> 1) & 0b00000011:
        case 0:
            modulation = "Auto"
        case 1:
            modulation = "FM"
        case 2:
            modulation = "AM"
        case 3:
            modulation = "USB"

    channel['modulation'] = modulation


def encode_channel_data():

    global channel

    mod_bw = bytearray(2)
    reserved = [ 255, 255, 255, 255]

    mod = 0
    match channel['modulation'].upper():
        case "AUTO":
            mod = 0
        case "FM":
            mod = 1
        case "AM":
            mod = 2
        case "USB":
            mod = 3
        case _:
            print("[ERR] Wrong modulation value ({}).".format(channel['modulation']))
            sys.exit(2)

    bw = 0
    match channel['bandwidth'].upper():
        case "WIDE":
            bw = 0
        case "NARROW":
            bw = 1
        case _:
            print("[ERR] Wrong bandwidth value ({}).".format(bw))
            sys.exit(2)
 
    mod_bw = (mod<<1) | bw  
    mod_bw |= 0b11111000 # add reserved bits as 1
        
    data = bytearray()
    data.extend(channel['rx_f'].to_bytes(4, byteorder='little'))
    data.extend(channel['tx_f'].to_bytes(4, byteorder='little'))
    data.extend(channel['rx_subtone'].to_bytes(2, byteorder='little'))
    data.extend(channel['tx_subtone'].to_bytes(2, byteorder='little'))
    data.append(channel['tx_power'])
    data.extend(group_s2b(channel['groups_str']))
    data.append(mod_bw)
    data.extend(reserved)
    data.extend(channel['name'].encode())

    data_len = len(data)
    if data_len != 32:
        print("[ERR] encoded data has wrong size ({} but should be {} bytes), something went terribly wrong.".format(data_len,32))
        sys.exit(2)

    return data


# read channel bytes from radio
def get_channel(channel_number):

    global channel

    disable_radio()

    port.write(CMD_READ_CHANNEL)
    port.write([channel_number+1])
    ack = port.read(1)
#    if ack != CMD_READ_CHANNEL:
#        print("[ERR] no Ack.")
#        sys.exit(2)

    data = port.read(32)
    checksum_r = port.read(1)

    enable_radio()

    if debug:
        print("[DBG] received data: {}".format(data));

    if data == b'':
        print("[ERR] received empy channel data!")
        sys.exit(2)

    if checksum_r != calc_checksum(data):
        print ("[ERR] received data checksum mismatch!")
        sys.exit(2)
    else:
        if debug:
            print ("[DBG] received checksum OK")

    # check if channel has only 0xff values (is empty)
    is_empty = True
    for i in data:
        if ( i != 255):
            is_empty = False
            break

    channel['is_empty'] = is_empty
    channel['number'] = channel_number

    # decode channel bytes to channel variables
    if is_empty == False:
        decode_channel_data(data)


# write channel bytes to radio
def write_channel_bytes(channel_number,data_bytes):

    global channel

    checksum = calc_checksum(data_bytes)

    if debug:
        print("[DBG] bytes to write:{} checksum:{}".format(data_bytes,checksum))

    disable_radio()

    port.write(CMD_WRITE_CHANNEL)
    port.write([channel_number+1])
    port.write(data_bytes)
    port.write(checksum)
    ack = port.read(1)

    enable_radio()

    if ack == CMD_WRITE_CHANNEL:
        if debug:
            print("[DBG] write OK")
    else:
        print("[ERR] invalid ACK after write, something went wrong!")
        sys.exit(2)

# prepare channel data for write
def write_channel():

    global channel

    if args.name is not None:
        channel['name'] = check_name(args.name)
    else:
        channel['name'] = check_name(channel['name'])

    if args.rx is not None:
        channel['rx_f'] = check_frequency(args.rx)
    if args.tx is not None:
        channel['tx_f'] = check_frequency(args.tx)
    if args.tx_ctcss is not None:
        channel['tx_subtone'] = check_subtone(args.tx_ctcss)
    if args.rx_ctcss is not None:
        channel['rx_subtone'] = check_subtone(args.rx_ctcss)
    if args.power is not None:
        channel['tx_power'] = check_power(args.power)
    if args.groups is not None:
        channel['groups_str'] = check_groups(args.groups)
    if args.modulation is not None:
        channel['modulation'] = check_modulation(args.modulation)
    if args.bandwidth is not None:
        channel['bandwidth'] = check_bandwidth(args.bandwidth)
    
    print_channel()

    data_w = encode_channel_data()

    write_channel_bytes(channel['number'], data_w)

    # optional radio reset after channel write (only if -r)
    if args.reset:
        disable_remote()
        reset_radio()

    sys.exit(0)

# writes previously generated (file import) ChannelsDict to radio
def write_channels_from_dict(ChannelsDict):

    global channel
   
    # for each channel number in radio...
    for channel_number in range(1,199):

        # show writing progress
        if (channel_number)%11 == 0:
            print("importing CH-{:03d}...CH-{:03d} ({:3.0f})%.".format(channel_number-10,channel_number,channel_number/198*100))

        # check if channel is in dictionary
        if channel_number in ChannelsDict.keys():

            c = ChannelsDict[channel_number]

            channel['name'] = c[0]
            channel['rx_f'] = c[1]
            channel['tx_f'] = c[2]
            channel['rx_subtone'] = c[3]
            channel['tx_subtone'] = c[4]
            channel['tx_power'] = c[5]
            channel['groups_str'] = c[6]
            channel['bandwidth'] = c[7]
            channel['modulation'] = c[8]

            data_w = encode_channel_data()

        # if not -- overwrite channel with 0xff
        else:
            data_w = bytearray([255]*32) # fill up with 0xff

        if debug:
            print("data_w: {}",format(data_w))

        write_channel_bytes(channel_number,data_w)
    
    print ("done.")
    reset_radio()

    sys.exit(0)
            
        
######################################################################################
######################################################################################
# MAIN
######################################################################################
######################################################################################

# check channel number
if args.channel != None:
    channel['number'] = check_channel_number(args.channel)

# write/overwrite channel
if args.write:

    # default values for the newly created channel
    channel['rx_f'] = 14495000
    channel['tx_f'] = 14495000
    channel['rx_subtone'] = 0
    channel['tx_subtone'] = 0
    channel['tx_power'] = 0
    channel['groups_str'] = "0000"
    channel['modulation'] = "Auto"
    channel['bandwidth'] = "Narrow"
    channel['name']= "CH-{:03n}".format(channel['number'])

    write_channel()

    sys.exit()

# remove channel
if args.remove:

    print("Removing channel CH-{:03d}".format(channel['number']))

    data_w = bytearray([255]*32) # fill up with 0xff
    write_channel_bytes(channel['number'], data_w)

    print("Done.")

    sys.exit(0)


# update channel
if args.update:

    get_channel(channel['number'])

    if channel['is_empty'] == False:
        write_channel()
    else:
        print("Channel {} is empty -- cannot perform an UPDATE action!".format(channel['number']))

    sys.exit()

# print info about channel
if args.channel:

    get_channel(channel['number'])

    if channel['is_empty'] == False:
        print_channel()
    else:
        print("Channel {} is empty.".format(channel['number']))

    sys.exit(0);

# turn flashlight on
if args.flashlight_on:
    write_cmd(CMD_FLASHLIGHT_ON)
    sys.exit(0)

# turn flashlight off
if args.flashlight_off:
    write_cmd(CMD_FLASHLIGHT_OFF)
    sys.exit(0)

# reset radio
if args.reset:
    disable_remote()
    reset_radio()
    sys.exit(0)

# export all channels from radio to CSV file
if args.export_csv != None:

    header = ""

    file = args.export_csv

    if args.fixed_width == False:
        line_format = "{:d},{:s},{:d},{:d},{:d},{:d},{:d},{:s},{:s},{:s}\n"
        header += "Channel number,Rx frequency,Tx frequency,Rx subtone,Tx subtone,Tx power,Groups,Bandwidth,Modulation\n"
    else:
        line_format = "{:03d},{:12s},{:9d},{:9d},{:5d},{:5d},{:3d},{:4s},{:6s},{:4s}\n"
        header += "CH#,Name        ,  Rx freq,  Tx freq,RxSub,TxSub,PWR,Grp ,Bwidth,Modulation\n"

    try:
        f = open(file,"w")
    except OSError:
        print("[ERR] Could not open/write file '{}'".format(file))
        sys.exit(2)

    # write file header
    if header != "":
        f.write(header)

    for channel_number in range(1,199):

        get_channel(channel_number)

        # show writing progress
        if (channel_number)%11 == 0:
            print("exporting CH-{:03d}...CH-{:03d} ({:3.0f})%.".format(channel_number-10,channel_number,channel_number/198*100))
 
        # write to file only valid channels       
        if channel['is_empty'] == False:
            f.write(line_format.format(
                channel_number,
                channel['name'].rstrip('\0'),
                channel['rx_f'],
                channel['tx_f'],
                channel['rx_subtone'],
                channel['tx_subtone'],
                channel['tx_power'],
                channel['groups_str'],
                channel['bandwidth'],
                channel['modulation'])
            )

    f.close

    print ("done.")

    sys.exit(0);


# import channels from CSV file
if args.import_csv != None:

    # dictionary where channels data readed from file will be stored
    ChannelsDict = {}
    
    try:
        file = open(args.import_csv, "r")
    except OSError:
        print("[ERR] Could not open/read file '{}'".format(args.import_csv))
        sys.exit(2)
    
    channels = {}

    lcount = 0

    for line in file:

        line = line.rstrip('\n')

        lcount += 1

        # skip first line (header)
        if lcount == 1:
            continue
        
        # split line csv data by ','
        csv_data = line.split(",")

        # check array size
        if len(csv_data) != 10:
            print("[ERR] line {} has incorrect number of fields".format(lcount))
            sys.exit(2)

        # set additional info on check fail
        exit_info = "[ERR] import failed on line {}".format(lcount)

        # check and import channel settings
        channel_number = check_channel_number(csv_data[0].strip(' '))
        name = check_name(csv_data[1].rstrip(' '))
        rx_f = check_frequency(csv_data[2].strip(' '))
        tx_f = check_frequency(csv_data[3].strip(' '))
        rx_subtone = check_subtone(csv_data[4].strip(' '))
        tx_subtone = check_subtone(csv_data[5].strip(' '))
        tx_power = check_power(csv_data[6].strip(' '))
        groups = check_groups(csv_data[7])
        bandwidth = check_bandwidth(csv_data[8].strip(' '))
        modulation = check_modulation(csv_data[9].strip(' '))

        if debug:       
            print ("[DBG] file read: {} {} {} {} {} {} {} {} {} {}".format(channel_number,name,rx_f,tx_f,rx_subtone,tx_subtone,tx_power,groups,bandwidth,modulation))

        # check for duplicates
        if channel_number in ChannelsDict.keys():
            print("[ERR] duplicated channel number: {}".format(channel_number))
            sys.exit(2)

        ChannelsDict[channel_number] = [ name, rx_f, tx_f, rx_subtone, tx_subtone, tx_power, groups, bandwidth, modulation ]

    file.close()
    
    # reset exit_info
    exit_info = None

    write_channels_from_dict(ChannelsDict)

    sys.exit(0)


#####################################
# REMOTE CONTROL
#####################################
# 10 - MENU         0x0A
# 11 - UP           0x0B
# 12 - DOWN         0x0C
# 13 - EXIT V/M     0x0D
# 14 - *            0x0E
# 15 - #            0x0F
# 16 - PTT          0x10
# 17 - FN1/PTT2     0x11
# 18 - FN2/f-light  0x12

if args.key:
#    write_cmd(CMD_START_REMOTE_SESSION)
    keys = args.key.split(",")
    keyArr = []

    # check if string can be converted to float (has only digits separated with optional '.')
    def is_float(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    # isolate numeric keys and put it to keyArr[] array (so 12345 will be [1, 2, 3, 4, 5] and will be send as separate keys
    for key in keys:
        if is_float(key):
            for i in range(0,len(key)):
                keyArr.append(key[i])
        else:
            keyArr.append(key)

    for key in keyArr:
        if key.lower() in [ 'blue', 'menu' ]:
            key = 10
        elif key.lower() == 'up':
            key = 11
        elif key.lower() == 'down':
            key = 12
        elif key.lower() in [ 'red', 'back' ]:
            key = 13
        elif key.lower() in [ '*', 'star', '.' ]:
            key = 14
        elif key.lower() == '#':
            key = 15
        elif key.lower() == 'ptt':
            key = 16
        elif key.lower() in [ 'f1', 'ptt2' ]:
            key = 17
        elif key.lower() == 'f2':
            key = 18
        elif len(key) == 1:
            if ord(key) < ord('0') or ord(key) > ord('9'):
               print("[ERR] Unsupported key: '{}'".format(key))
               sys.exit(2)
        else:
            print("[ERR] Unsupported key: '{}'".format(key))
            sys.exit(2)
        

        port.write([0x80|int(key)])
        sleep(DEFAULT_KEY_PUSH_TIME)
        port.write([0xFF])
        sleep(DEFAULT_KEY_PUSH_TIME)

    print("done.")
#    port.write(CMD_END_REMOTE_SESSION)
    sys.exit(0)

