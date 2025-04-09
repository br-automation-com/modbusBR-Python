from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from threading import Timer
from modbusTCPBRMDinfo import MasterBRMDinfo
from modbusTCPBRBCinfo import MasterBRBCinfo
import struct
import time
import asyncio

# ------------------------------------------------------------------------------------------------------
class OnException(Exception):
    def __init__(self, id=None, message=None):
        self.id = id
        self.message = message

# ------------------------------------------------------------------------------------------------------
class MasterBRBC:
    # Public constants for exception
    excWatchdog = 1
    excTimeout = 2
    excConnection = 3
    excDevice = 4
    excBUSY = 6
    excNoModule = 10
    excNoDigInData = 11
    excNoDigOutData = 12
    excNoAnaInData = 13
    excNoAnaOutData = 14
    excWrongRegData = 15
    excDataSize = 16
    excDataEmptyAnswer = 17
    excDataRange = 20
    excWrongEthernetFormat = 30
    excUnhandled = 40

    def __init__(self, debug=0):
        self.client = None

        # Initialize variables for refresh task and error counters
        self._refresh_interval = 1000
        self._refresh_task = None
        self._connected = False
        self._debug = debug

        # Initialize buffers and lengths for digital and analog inputs/outputs
        self.dig_in_buffer = []
        self.dig_in_length = 0
        self.dig_out_buffer = []
        self.dig_out_length = 0
        self.ana_in_buffer = []
        self.ana_in_length = 0
        self.ana_out_buffer = []
        self.ana_out_length = 0

        # Initialize BCinfo and MDinfo attributes
        self.BCinfo = None
        self.MDinfo = []

    @property
    def Connected(self):
        return self._connected

    def Connect(self, ip, port):
        try:
            self.client = ModbusTcpClient(host=ip, port=port, reconnect_delay=5, retries=3, timeout=5)
            self.client.connect()
            while self.client.connected is False:
                time.sleep(1)

            self._connected = self.client.connected
            print("Connected to Modbus server")

        except Exception as error:
            self._connected = False
            if self.client:
                self.client.close()
                self.client = None
                self.BCinfo = None

            raise OnException(error)        

        # Disable boundary check
        response = self.client.write_register(address=0x1182, value=0xC0)
        if response.isError():
            if self._debug > 0:
                print("Wait for server to be ready...")
            time.sleep(5)
            self.SyncWriteRegisters(0x1182, 0xC0)

        self.BCinfo = MasterBRBCinfo(self)
        self.MasterMDinfo()

        self.dig_in_length = self.BCinfo.process_digital_inp_cnt * 8
        self.dig_in_buffer = [False] * self.dig_in_length
        self.dig_out_length = self.BCinfo.process_digital_out_cnt * 8
        self.dig_out_buffer = [False] * self.dig_out_length
        self.ana_in_length = self.BCinfo.process_analog_inp_cnt
        self.ana_in_buffer = [0] * self.ana_in_length
        self.ana_out_length = self.BCinfo.process_analog_out_cnt * 8
        self.ana_out_buffer = [0] * self.ana_out_length

        # Start the asynchronous timer
        self._refresh_task = asyncio.create_task(self._RefreshTimer(self._refresh_interval/1000, self._RefreshTimer_Elapsed))
        if self._debug > 1:
            print("Refresh timer started")

    async def Disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.BCinfo = None
        else:
            return
        
        self._connected = False
        if self._refresh_task:
            self._refresh_task.cancel()

            # Wait for the task to finish
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                if self._debug > 1:
                    print("Refresh timer stopped")

        if self._debug > 0:
            print("Disconnected from Modbus server")                    

    def MasterMDinfo(self):
        self.MDinfo = []
        try:
            while True:
                MDinfo_tmp = MasterBRMDinfo(self, len(self.MDinfo))
                if MDinfo_tmp.status != 0:
                    self.MDinfo.append(MDinfo_tmp)
                    if self._debug > 1:
                        print("Found module:", MDinfo_tmp.name)   
                else:
                    break
        except Exception as error:
            raise OnException(error)

    def ReadDigitalInputs(self, module_nr, size, offset=0):
        data = [False] * size

        if self._ValidateData(module_nr, size):
            if self.MDinfo[module_nr].digital_in_index != 0xFFFF:
                if size <= len(self.dig_in_buffer) - (self.MDinfo[module_nr].digital_in_index * 8 + offset):
                    response = self.client.read_discrete_inputs(address=self.MDinfo[module_nr].digital_in_index * 8 + offset, count=size)
                    if not response.isError():
                        data = response.bits[:size]
                    else:
                        raise OnException(self.excDataEmptyAnswer)
                    return data
                else:
                    raise OnException(self.excDataSize)
            #else:
                #raise OnException(self.excNoDigInData)
        return None

    def WriteDigitalOutputs(self, module_nr, values, offset=0):
        if self._ValidateData(module_nr, len(values)):
            if self.MDinfo[module_nr].digital_out_index != 0xFFFF:
                if len(values) <= len(self.dig_out_buffer) - (self.MDinfo[module_nr].digital_out_index * 8 + offset):
                    self.client.write_coils(address=self.MDinfo[module_nr].digital_out_index * 8 + offset, values=values)
                    return True
                else:
                    raise OnException(self.excDataSize)
            else:
                raise OnException(self.excNoDigOutData)
        return False

    def ReadAnalogInputs(self, module_nr, size, offset=0):
        data = [0] * size

        if self._ValidateData(module_nr, size):
            if self.MDinfo[module_nr].analog_in_index != 0xFFFF:
                if size <= len(self.ana_in_buffer) - (self.MDinfo[module_nr].analog_in_index // 2 + offset):
                    response = self.client.read_input_registers(address=self.MDinfo[module_nr].analog_in_index // 2 + offset, count=size)
                    if not response.isError():
                        data = response.registers
                    else:
                        raise OnException(self.excDataEmptyAnswer)
                    return data
                else:
                    raise OnException(self.excDataSize)
            else:
                raise OnException(self.excNoAnaInData)
        return None

    def WriteAnalogOutputs(self, module_nr, values, offset=0):
        # Ensure values is an array
        if not isinstance(values, list):
            values = [values]
        if self._ValidateData(module_nr, len(values)):
            if self.MDinfo[module_nr].analog_out_index != 0xFFFF:
                if len(values) <= len(self.ana_out_buffer) - (self.MDinfo[module_nr].analog_out_index // 2 + offset):
                    self.client.write_registers(address=self.MDinfo[module_nr].analog_out_index // 2 + offset, values=values)
                    return True
                else:
                    raise OnException(self.excDataSize)
            else:
                raise OnException(self.excNoAnaOutData)
        return False

    def _ValidateData(self, module_nr, size):
        if not self._connected:
            raise OnException(self.excConnection)
        if module_nr > len(self.MDinfo) - 1:
            raise OnException(self.excNoModule)
        if size == 0:
            raise OnException(self.excDataSize)
        return True

    def _SyncReadWord(self, adr):
        if self._connected:
            response = self.client.read_input_registers(address=adr, count=1)
            if not response.isError():
                return response.registers[0]
            else:
                raise OnException(response.exception_code, 'error reading word')
        return 0xFFFF
   
    def _SyncReadRegisters(self, adr, cnt):
        if self._connected:
            response = self.client.read_input_registers(address=adr, count=cnt)
            if not response.isError():
                return response.registers
            else:
                raise OnException(response.exception_code, 'error reading to register')
        return 0xFFFF

    def _SyncWriteRegisters(self, adr, values):
        # Ensure values is an array
        #if not isinstance(values, list):
         #   values = [values]
        if self._connected:
            if isinstance(values, list):
                response = self.client.write_registers(address=adr, values=values)
            else:
                response = self.client.write_register(address=adr, value=values)
            if not response.isError():
                return response.registers
            else:
                raise OnException(response.exception_code, 'error writing to register')
        
        return 0xFFFF

    def _Bit2Byte(self, values):
        data = bytearray(len(values) // 8 + (1 if len(values) % 8 > 0 else 0))
        for x in range(len(data)):
            for y in 8:
                data[x] |= (values[x * 8 + y] << y)
                if x * 8 + y + 1 == len(values):
                    break
        return data

    def _Byte2Word(self, byte1, byte2):
        return struct.unpack('>h', bytes([byte2, byte1]))[0]

    def _Byte2Long(self, byte1, byte2, byte3, byte4):
        return struct.unpack('>i', bytes([byte4, byte3, byte2, byte1]))[0]

    def _ByteArray2WordArray(self, values):
        result = [0] * (len(values) // 2)
        for x in range(0, len(values), 2):
            result[x // 2] = self._Byte2Word(values[x], values[x + 1])
        return result

    def _WordArray2WordByte(self, values):
        byte_array = bytearray()
        for word in values:
            byte_array.extend(struct.pack('>H', word))  # '>H' ensures big-endian 16-bit unsigned integers
        return byte_array

    async def _RefreshTimer(self, interval, callback):
        while True:
            await asyncio.sleep(interval)  # Wait for the specified interval
            await callback()  # Call the asynchronous callback function

    async def _RefreshTimer_Elapsed(self):
        try:
            if self._connected:
                self._SyncReadRegisters(0x1042, 1)

            if self._debug > 1:
                print("Refresh timer called")

        except Exception as error:
            raise error


