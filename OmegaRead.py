import pymodbus
import serial
import logging
# from pymodbus.pdu import ModBusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.client.sync import ModbusRtuFramer

## Much copied from https://pymodbus.readthedocs.io/en/latest/source/example/synchronous_client.html

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT= 1

def run_sync_client():
    # print('hello')
    client = ModbusClient(method='rtu', port='COM8', stopbits=2, parity='N', baudrate=57600, bytesize=8)
    client.connect()
    print(client.is_socket_open())
    print("socket:")
    print(client.is_socket_open())

    temp = client.read_input_registers(0x1000,12,unit=UNIT)
    print(temp.registers)
    client.close()


run_sync_client()