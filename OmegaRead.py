import pymodbus
import serial
import logging
# from pymodbus.pdu import ModBusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

## Much copied from https://pymodbus.readthedocs.io/en/latest/source/example/synchronous_client.html

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT= 0x1

def run_sync_client():
    client = ModbusClient(method='ascii', port='COM8', stopbits=serial.STOPBITS_TWO, parity=serial.PARITY_NONE, baudrate=57600)

    client.connect()
    client.write_coil(1, True)
    result = client.read_coils(1,1)
    print(result)
    client.close()

    # log.debug("Write to multiple coils and read back- test 1")
    # rq = client.write_coils(1, [True]*8, unit=UNIT)
    # rr = client.read_coils(1, 21, unit=UNIT)
    # assert(not rq.isError())     # test that we are not an error
    # assert(not rr.isError())     # test that we are not an error
    # resp = [True]*21

    # log.debug("Reading Coils")
    # rr = client.read_coils(1, 1, unit=UNIT)
    # log.debug(rr)
    
    # temp = client.read_holding_registers(0x1000,1)

    temp = client.read_input_registers(0x1000,4,unit=UNIT)
    print(temp)
    print(client)


run_sync_client()