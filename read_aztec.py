"""Read ticket from LSR110 scanner"""

import binascii
import sys
import zlib
import serial
from time import sleep


PORT = '/dev/tty.usbmodem21143101'
BAUDRATE = 115220

PHONE_ONLY = 0
PAPER_ONLY = 1
PAPER_OPTIMIZED = 2
PHONE_OPTIMIZED = 3


def scanner_read(scanner) -> bytes:
    """Read data from scanner"""
    waiting = scanner.inWaiting()
    if waiting > 0:
        data = scanner.read(waiting)
        return data
    return None

def scanner_write(scanner, data: bytes) -> None:
    scanner.write(data)

def send_command(scanner, command: str) -> bytes:
    """Send command to scanner, return any resulting data"""
    prefix = [0x16, 0x4D, 0x0D]
    data = bytes(prefix) + command.encode()
    scanner_write(scanner, data)
    return scanner_read(scanner)

def send_modify_command(scanner, command: str, parameter=None, permanent: bool = False):
    if permanent:
        terminator = "."
    else:
        terminator = "!"
    if parameter is not None:
        send_command(scanner, command + str(parameter) + terminator)
    else:
        send_command(scanner, command + terminator)


scanner = serial.Serial(port=PORT, baudrate=BAUDRATE)

# configure scanner
send_modify_command(scanner, "AISRDS", 1)
#send_modify_command(scanner, "AISLS1", 0)
#send_modify_command(scanner, "AISLS2", 0)
send_modify_command(scanner, "AISILL", PHONE_OPTIMIZED)
send_modify_command(scanner, "AISOMD1")

decompressor = None

while True:
    print("Waiting for scanner data...")
    sleep(1)
    data = b''
    decompressor = zlib.decompressobj()
    msg = scanner_read(scanner)
    if msg:
        print(f"Received {len(msg)} bytes from scanner: {binascii.hexlify(msg).decode()}")
        if msg.startswith(b'AIS'):
            print("Command ack!")
            data = b''
        else:
            if decompressor is None:
                decompressor = zlib.decompressobj()
            try:
                data += decompressor.decompress(msg)
            except zlib.error as exc:
                print(str(exc))
                sys.exit(-1)
            if decompressor.eof:
                print("Decompressed data:", binascii.hexlify(data).decode())
                print(f"Complete uncompressed message, size = {len(data)}")
                sys.exit(0)
            else:
                print("Buffer now:", binascii.hexlify(data).decode())
