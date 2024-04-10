#!/bin/bash

#parser.add_argument('--frames', dest='frames', type=int, default=1e6, help='number of frames to capture')
#parser.add_argument('--serialport', dest='serialport', default='/dev/ttyACM0', help='serial port device')
#parser.add_argument('--camindex', dest='camindex', help='Camera Index (/dev/videoX)', default=0)
#parser.add_argument('--prefix', dest='prefix', default='', help='prefix filenames with a prefix')
#parser.add_argument('--film', dest='film', choices=['s8','8mm'], help='8mm/s8', default='s8')
#parser.add_argument('--framesto', dest='framesto', required=True, help='Target Directory', default='/mnt/exthd')
#parser.add_argument('--startdia', dest='startdia', type=int, default=62, help='Feed spool starting diameter (mm)')
#parser.add_argument('--enddia', dest='enddia', type=int, default=35, help='Feed spool ending diameter (mm)')
#parser.add_argument('--res', dest='res', choices=['draft','1k', 'hd', 'full'], help="resolution", default='draft')

./opencvcap.py --serialport /dev/ttyACM0 --camindex 0 --film s8 --framesto ~/share/opencvcap0 --startdia 140 --enddia 80 --res draft
