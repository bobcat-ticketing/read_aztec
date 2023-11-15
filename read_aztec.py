"""Read MTB from LSR110 scanner"""

import argparse
import binascii
import logging
import sys
import time
import zlib

import serial

DEFAULT_PORT = "/dev/tty.usbmodem1143101"
DEFAULT_BAUDRATE = 115220
DEFAULT_OUTPUT = "mtb.bin"

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


def main():
    """Main function"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        metavar="port",
        help="Scanner port",
        default=DEFAULT_PORT,
    )
    parser.add_argument(
        "--output",
        metavar="filename",
        help="Output filename",
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--baudrate",
        metavar="baudrate",
        help="Scanner baudrate",
        type=int,
        default=DEFAULT_BAUDRATE,
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Enable debugging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    scanner = serial.Serial(port=args.port, baudrate=args.baudrate)

    # configure scanner
    send_modify_command(scanner, "AISRDS", 1)
    # send_modify_command(scanner, "AISLS1", 0)
    # send_modify_command(scanner, "AISLS2", 0)
    send_modify_command(scanner, "AISILL", PHONE_OPTIMIZED)
    send_modify_command(scanner, "AISOMD1")

    data = b""
    decompressor = None

    while True:
        logging.debug("Waiting for scanner data...")
        time.sleep(1)
        msg = scanner_read(scanner)
        if msg:
            logging.info(
                "Received %d bytes from scanner: %s",
                len(msg),
                binascii.hexlify(msg).decode(),
            )
            if msg.startswith(b"AIS"):
                logging.debug("Command ack!")
                data = b""
            else:
                if decompressor is None:
                    decompressor = zlib.decompressobj()
                try:
                    data += decompressor.decompress(msg)
                except zlib.error as exc:
                    logging.error("%s", str(exc))
                    sys.exit(-1)
                if decompressor.eof:
                    logging.info(
                        "Decompressed %s bytes of data: %s",
                        len(data),
                        binascii.hexlify(data).decode(),
                    )
                    filename = args.output
                    with open(filename, "wb") as output_file:
                        output_file.write(data)
                    logging.info("Output written to %s", filename)
                    sys.exit(0)
                else:
                    logging.debug("Buffer now: %s", binascii.hexlify(data).decode())


if __name__ == "__main__":
    main()
