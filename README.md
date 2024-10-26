# Disclaimer

THIS SOFTWARE IS DELIVERED FREE OF CHARGE AND 'AS IS' WITHOUT WARRANTY OF ANY KIND.

Using it in particular can damage your radio device, remember -- you use it at your own risk.

# Info

Tools placed here are designed to work with an alternative nicFW firmware created by Marcus for Tidradio H3.

More information about firmware can be obtained at:
 - https://nicsure.co.uk/
 - https://www.facebook.com/groups/456942886822492

# nicFWutil.py

Basic tool for nicFW settings manipulation:
 - adding/editing/removing single channels
 - importing/exporting channel list to CSV (with fixed width data field support)
 - remote radio keys control
 - dumping EEPROM
 - read Band Plan, Scan Presetes, FM tuner channels

## Usage:

```
--device / -d
      >>> serial device to use, default /dev/ttyUSB0

--channel / -c
      >>> channel number for which the action will be taken

--debug
      >>> enable verbose/debug output

CHANNEL ACTIONS:

  --write / -w 
        >>> creat new channel / overwrite existing one

  --update / -u
        >>> update existing channel

  --remove
        >>> remove channel

  --export-csv / -e
        >>> export full channel list from radio to CSV file

  --fixed-width / -f
        >>> use fixed field width on exported CSV file (see usage examples bellow)

  --import-csv / -i
        >>> import channels from CSV file to radio

CHANNEL MODIFIERS:

  --name / -n          <name>
        >>> set channel name

  --tx / -tx           <frequency>
  --rx / -rx           <frequency>
        >>> set RX/TX frequency in 10Hz units

  --tx-ctcss / -txc    <CTCSS frequency>
  --rx-ctcss / -rxc    <CTCSS frequency>
        >>> set RX/TX ctcss frequency

  --power / -p         <power>
        >>> set TX power, value 0-255

  --modulation / -m    <modulation>
        >>> set modulation (Auto/AM/FM/USB)

  --bandwidth / -b     <bandwidth>
        >>> set bandwidth (Wide/Narrow)

  --groups / -g        <groups>
        >>> set group membership, eg. AB0D, AF, 000A (allowed characters: A-O, a-o, 0)

REMOTE CONTROL:

  --reset / -r
        >>> reset radio, should be used after channel modification

  --flashlight-on  / -f1
  --flashlight-off / -f0
        >>> enable/disable flashlight LED in radio

  --key / -k        <list of keys to send>
        >>> coma separated key sequence to send, see bellow

      AVAILABLE KEYS:

        0 .. 9      - can be provided without coma, eg. 1234 (the same effect as 1,2,3,4)
        blue/menu   - blue menu button / bluetooth enable
        up          - up button
        down        - down button
        red/back    - red back button
        */star      - as * is console special character, must be escaped (\*) or just use 'start' string instead
        #           - # ;)
        ptt         - main PTT button
        ptt2/f1     - f1 ptt2 button
        f2          - f2 flashlight button

READ EEPROM:

  --show-eeprom / -se
        >>> print EEPROM content

  --show-bandplan / -sb
        >>> print Band Plan

  --show-scan-presets / -ssp
        >>> print Scan Presets

  --show-fmtuner / -sf
        >>> print FM tuner channels

```

## Usage examples

### get info about channel

```
./nicFWutil.py -c 12
channel    : CH-012
name       : PMR-12
RX freq    : 44614375
TX freq    : 44614375
RX subtone : 0
TX subtone : 0
TX power   : 127
group      : A000
bandwidth  : Narrow
modulation : FM
```

### create new channel with default configuration

You can use any channel modifiers to replace some/all of default channel values.

```
./nicFWutil.py -c 30 -w
channel    : CH-030
name       : CH-030
RX freq    : 14495000
TX freq    : 14495000
RX subtone : 0
TX subtone : 0
TX power   : 0
group      : 0000
bandwidth  : Narrow
modulation : Auto
```

### update only channel name, and restart radio
Update can be done only on existing channel, at least one channel settings must be specified.
If more than one channel will be modified, -r can be run with last one.

```
./nicFWutil.py -c 30 -u -n "Test Channel" -r
name       : Test Channel
RX freq    : 14495000
TX freq    : 14495000
RX subtone : 0
TX subtone : 0
TX power   : 0
group      : 0000
bandwidth  : Narrow
modulation : Auto
```

### set channel group membership, power and modulation

```
./nicFWutil.py -c 30 -u -g ab -p 128 -m USB
channel    : CH-030
name       : Test Channel
RX freq    : 14495000
TX freq    : 14495000
RX subtone : 0
TX subtone : 0
TX power   : 128
group      : AB
bandwidth  : Narrow
modulation : USB
```

### remove channel number 30
```
./nicFWutil.py -c 30 --remove
Removing channel CH-030
Done.
```

## CSV import/export

- on import all channels that are not defined in CSV file will be removed form radio
- if there are any extra commas in the file, apart from the ones separating the fields, you will encounter an import error (no channels will be sent or changed on the radio)
- on import first line is always skipped (there should be file header with columns description)
  
### exporting full channel list from radio to CSV file

```
./nicFWutil.py --export-csv channels.csv
exporting CH-001...CH-011 (  6)%.
exporting CH-012...CH-022 ( 11)%.
exporting CH-023...CH-033 ( 17)%.
exporting CH-034...CH-044 ( 22)%.
exporting CH-045...CH-055 ( 28)%.
exporting CH-056...CH-066 ( 33)%.
exporting CH-067...CH-077 ( 39)%.
exporting CH-078...CH-088 ( 44)%.
exporting CH-089...CH-099 ( 50)%.
exporting CH-100...CH-110 ( 56)%.
exporting CH-111...CH-121 ( 61)%.
exporting CH-122...CH-132 ( 67)%.
exporting CH-133...CH-143 ( 72)%.
exporting CH-144...CH-154 ( 78)%.
exporting CH-155...CH-165 ( 83)%.
exporting CH-166...CH-176 ( 89)%.
exporting CH-177...CH-187 ( 94)%.
exporting CH-188...CH-198 (100)%.
done
```

standard CSV format file content looks like this:
```
cat channels.csv | head -n 40 | tail -n 10
34,2m 2*,14542500,14542500,0,0,127,CF00,Narrow,FM
35,2m 3*,14552550,14552550,0,0,127,CF00,Narrow,FM
36,2m SR9P Rx,14400000,14400000,0,0,127,CF00,Narrow,FM
37,2m FT8,14417400,14417400,0,0,127,CF00,Narrow,USB
38,2m USB 1,14430000,14430000,0,0,127,CF00,Narrow,USB
39,2m USB 2,14435000,14435000,0,0,127,CF00,Narrow,USB
40,KR pogoda,14495000,14495000,0,0,0,C000,Narrow,FM
41,2m p,14457500,14457500,0,0,127,CF00,Narrow,FM
42,2m APRS,14480000,14480000,0,0,0,C000,Narrow,FM
44,SR9VHF Lubon,14448300,14448300,0,0,0,D000,Narrow,USB
```

### exporting full channel list from radio to CSV file with fixed width field
Fixed width field can be helpful when editing a file with a regular text editor, like vim

```
./nicFWutil.py --export-csv channels.csv --fixed-width
exporting CH-001...CH-011 (  6)%.
exporting CH-012...CH-022 ( 11)%.
exporting CH-023...CH-033 ( 17)%.
exporting CH-034...CH-044 ( 22)%.
exporting CH-045...CH-055 ( 28)%.
exporting CH-056...CH-066 ( 33)%.
exporting CH-067...CH-077 ( 39)%.
exporting CH-078...CH-088 ( 44)%.
exporting CH-089...CH-099 ( 50)%.
exporting CH-100...CH-110 ( 56)%.
exporting CH-111...CH-121 ( 61)%.
exporting CH-122...CH-132 ( 67)%.
exporting CH-133...CH-143 ( 72)%.
exporting CH-144...CH-154 ( 78)%.
exporting CH-155...CH-165 ( 83)%.
exporting CH-166...CH-176 ( 89)%.
exporting CH-177...CH-187 ( 94)%.
exporting CH-188...CH-198 (100)%.
done.
```

fixed width CSV format:
```
cat channels.csv | head -n 40 | tail -n 10
034,2m 2*       , 14542500, 14542500,    0,    0,127,CF00,Narrow,FM  
035,2m 3*       , 14552550, 14552550,    0,    0,127,CF00,Narrow,FM  
036,2m SR9P Rx  , 14400000, 14400000,    0,    0,127,CF00,Narrow,FM  
037,2m FT8      , 14417400, 14417400,    0,    0,127,CF00,Narrow,USB 
038,2m USB 1    , 14430000, 14430000,    0,    0,127,CF00,Narrow,USB 
039,2m USB 2    , 14435000, 14435000,    0,    0,127,CF00,Narrow,USB 
040,KR pogoda   , 14495000, 14495000,    0,    0,  0,C000,Narrow,FM  
041,2m p        , 14457500, 14457500,    0,    0,127,CF00,Narrow,FM  
042,2m APRS     , 14480000, 14480000,    0,    0,  0,C000,Narrow,FM  
044,SR9VHF Lubon, 14448300, 14448300,    0,    0,  0,D000,Narrow,USB 
```
you can see right away that it is more pleasant for humans eyes ;)

### importing channels from CSV file to radio

After import radio will be restarted

```
./nicFWutil.py --import-csv channels.csv
importing CH-001...CH-011 (  6)%.
importing CH-012...CH-022 ( 11)%.
importing CH-023...CH-033 ( 17)%.
importing CH-034...CH-044 ( 22)%.
importing CH-045...CH-055 ( 28)%.
importing CH-056...CH-066 ( 33)%.
importing CH-067...CH-077 ( 39)%.
importing CH-078...CH-088 ( 44)%.
importing CH-089...CH-099 ( 50)%.
importing CH-100...CH-110 ( 56)%.
importing CH-111...CH-121 ( 61)%.
importing CH-122...CH-132 ( 67)%.
importing CH-133...CH-143 ( 72)%.
importing CH-144...CH-154 ( 78)%.
importing CH-155...CH-165 ( 83)%.
importing CH-166...CH-176 ( 89)%.
importing CH-177...CH-187 ( 94)%.
importing CH-188...CH-198 (100)%.
done.

```

### sending key sequence to radio
'star' is just for waking up the radio (if there is such need), next 144.950 will be send to set 144.950Mhz frequency -- assuming the radio is in VFO mode
```
./nicFWutil.py -k star,144.950,blue
done.
```

### reading EEPROM

## read EEPROM content

```
./nicFWutil.py -se
000 0x00 | 15 cd 5b 07 15 cd 5b 07 00 00 00 00 01 01 00 00 ff ff ff ff 50 4d 52 2d 30 31 00 00 00 00 00 00
001 0x01 | 18 2d dd 00 18 2d dd 00 00 00 00 00 00 00 00 00 ff ff ff ff 43 48 2d 30 31 37 00 00 00 00 00 00
002 0x02 | 31 8d a8 02 31 8d a8 02 00 00 00 00 7f 01 00 fb ff ff ff ff 50 4d 52 2d 30 31 00 00 00 00 00 00
003 0x03 | 13 92 a8 02 13 92 a8 02 00 00 00 00 7f 01 00 fb ff ff ff ff 50 4d 52 2d 30 32 00 00 00 00 00 00
004 0x04 | f5 96 a8 02 f5 96 a8 02 00 00 00 00 7f 01 00 fb ff ff ff ff 50 4d 52 2d 30 33 00 00 00 00 00 00

[...]

252 0xfc | 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28
253 0xfd | 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28
254 0xfe | 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28
255 0xff | 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28
```

## read Band Plan

```
./nicFWutil.py -sb
Band Plan
Start Frequency End frequency Max Power Modulation   Bandwidth      Tx Allowed Wrap     
       14400000      14600001         0 FM           Wide           Yes        Yes      
       43000000      44000001         0 FM           Wide           Yes        Yes      
       10800000      13800000         0 AM           Narrow         Yes        No       
       66000001      84000000         0 Enforce_None Ignore         No         No       
       44600625      44619376        25 Enforce_FM   Wide           Yes        Yes      
       46255000      46272501         0 Enforce_FM   Wide           No         Yes      
       46755000      46772501         0 Enforce_FM   Wide           No         Yes      
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0         1 Ignore       Wide           No         No       
              0             0         0 Ignore       Ignore         No         No       
              0             0       253 Ignore       Enforce_Narrow No         Yes      
              0             0       254 Ignore       Ignore         Yes        No       
        1800000     130000000       255 Ignore       Ignore         No         No
```

## read Scan Presets

```
./nicFWutil.py -ssp
Scan Presets
Start Frequency End Frequency Squelch Squelch Tail Step  Scan Hold Scan Tail Update Modulation
       10000000      20000000       1            0  1250       200       100     25 USB       
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
              0        125000       2            3  1250         0       100     23 FM        
       10000000      10001250       2            3  1250       200       100     25 USB 
```

## read FM tuner channels

```
./nicFWutil.py -sf
FM Tuner settings
Frequency Band   
        0 Low_VHF
   100000 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 West   
        0 Japan  
        0 World  
    70000 Low_VHF
```

# TODO

 - radio settings support
 - bandplan support
 - bluetooth support
 - ... ?
