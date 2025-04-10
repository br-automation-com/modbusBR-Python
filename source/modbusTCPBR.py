from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException  # Import general Modbus exception
from modbusTCPBRMDinfo import MasterBRMDinfo
from modbusTCPBRBCinfo import MasterBRBCinfo, RefreshTimer
import struct
import time
from typing import Optional, List, Union, Dict, Any, Tuple

# ------------------------------------------------------------------------------------------------------
class OnException(Exception):
    """
    Custom exception class for handling errors in the Modbus communication.

    This exception is raised to provide specific context about Modbus-related
    errors, such as connection issues, timeouts, or invalid data.

    Attributes:
        id (int, optional): An error code associated with the exception.
                             Provides a numerical identifier for the error. Defaults to None.
        message (str, optional): A descriptive error message that explains the
                                 nature of the exception. Defaults to None.
    """

    def __init__(self, id=None, message=None):
        """
        Initializes a new OnException instance.

        Args:
            id (int, optional): The error code.
            message (str, optional): The error message.
        """
        self.id = id
        self.message = message


# ------------------------------------------------------------------------------------------------------
class MasterBRBC:
    """
    Main class for managing Modbus TCP communication with a BR controller.

    This class provides methods for establishing a connection with a Modbus TCP
    server, reading and writing digital and analog inputs/outputs, and retrieving
    information about connected modules. It encapsulates the Modbus communication
    logic and simplifies interaction with the BR controller.

    Attributes:
        client (ModbusTcpClient, optional): The Modbus TCP client instance used
                                         for communication. Initialized in Connect().
        _connected (bool): A flag indicating whether the client is currently
                          connected to the Modbus server.
        _debug (int): The debug level for controlling the verbosity of log messages.
                      0: No debug output, higher values increase verbosity.
        BCinfo (MasterBRBCinfo, optional): An instance of MasterBRBCinfo containing
                                         information about the Bus Controller.
                                         Initialized in Connect().
        MDinfo (list): A list of MasterBRMDinfo instances, where each instance
                       represents a connected module.
    
    Exception Codes:
        These public constants define specific error conditions that can occur
        during Modbus communication. They are used as 'id' values when raising
        the OnException to provide detailed error information.
    """

    # Public constants for exception codes
    excWatchdog = 1  # Watchdog timeout
    excTimeout = 2  # Communication timeout
    excConnection = 3  # Connection error
    excDevice = 4  # Device error
    excBUSY = 6  # Device is busy
    excNoModule = 10  # Module not found
    excNoDigInData = 11  # No digital input data available
    excNoDigOutData = 12  # No digital output data available
    excNoAnaInData = 13  # No analog input data available
    excNoAnaOutData = 14  # No analog output data available
    excWrongRegData = 15  # Wrong register data format
    excDataSize = 16  # Invalid data size
    excDataEmptyAnswer = 17  # Empty response from the server
    excDataRange = 20  # Data out of range
    excWrongEthernetFormat = 30  # Invalid Ethernet format
    excUnhandled = 40  # Unhandled exception

    def __init__(self, debug=0):
        """
        Initializes the MasterBRBC instance.

        Sets up the Modbus client, connection status, debug level, and initializes
        buffers for digital and analog I/O data.

        Args:
            debug (int, optional): The debug level for logging.
                                 Defaults to 0 (no debug output).
        """
        self.client = None  # ModbusTcpClient instance

        # Initialize connection status and debug level
        self._connected = False
        self._debug = debug

        # Initialize I/O buffers and their lengths
        self.dig_in_buffer = []  # Buffer for digital input values (list of bool)
        self.dig_in_length = 0  # Length of the digital input buffer
        self.dig_out_buffer = []  # Buffer for digital output values (list of bool)
        self.dig_out_length = 0  # Length of the digital output buffer
        self.ana_in_buffer = []  # Buffer for analog input values (list of int)
        self.ana_in_length = 0  # Length of the analog input buffer
        self.ana_out_buffer = []  # Buffer for analog output values (list of int)
        self.ana_out_length = 0  # Length of the analog output buffer

        # Initialize Bus Controller and Module Info
        self.BCinfo = None  # Bus Controller information (MasterBRBCinfo instance)
        self.MDinfo = []  # List of Module information (list of MasterBRMDinfo instances)

    def __del__(self):
        """
        Destructor for the MasterBRBC class.

        Closes the Modbus connection (if open) and releases resources.
        This ensures proper cleanup when a MasterBRBC object is no longer needed.
        """
        if self.client:
            self.client.close()  # Ensure the Modbus connection is closed

        self.BCinfo = None  # Release Bus Controller information
        self.MDinfo = None  # Release Module information

    @property
    def Connected(self):
        """
        Property to check the connection status.

        Returns:
            bool: True if the client is connected to the Modbus server, False otherwise.
        """
        return self._connected

    def Connect(self, ip: str, port: int, timeout: int = 10) -> None:
        """
        Connects to the Modbus TCP server with timeout.
        
        Args:
            ip: The IP address of the server.
            port: The port number.
            timeout: Connection timeout in seconds.
        """
        try:
            self.client = ModbusTcpClient(
                host=ip, port=port, reconnect_delay=5, retries=3, timeout=timeout
            )
            # Connect with timeout
            self.client.connect()
            
            # Wait for connection with timeout
            start_time = time.time()
            while not self.client.connected:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Connection timed out")
                time.sleep(0.5)  # Check more frequently

            self._connected = self.client.connected  # Update connection status
            self._debug_message(0, "Connected to Modbus server")

        except ModbusIOException as e:
            # Catch Modbus connection exceptions specifically
            self._connected = False
            if self.client:
                self.client.close()
                self.client = None
                self.BCinfo = None
            raise OnException(self.excConnection, f"Modbus connection error: {e}")
        except Exception as error:
            # Catch any other exceptions
            self._connected = False
            if self.client:
                self.client.close()
                self.client = None
                self.BCinfo = None
            raise OnException(self.excUnhandled, f"Unhandled connection error: {error}")

        # Disable boundary check on the Modbus server
        try:
            response = self.client.write_register(address=0x1182, value=0xC0)
            if response.isError():
                self._debug_message(0, "Wait for server to be ready...")
                time.sleep(5)
                self._SyncWriteRegisters(0x1182, 0xC0)  # Retry if initial write fails
        except ModbusIOException as e:
            raise OnException(self.excDevice, f"Error disabling boundary check: {e}")

        # Initialize Bus Controller and Module information
        self.BCinfo = MasterBRBCinfo(self)
        self.MasterMDinfo()

        # Initialize I/O buffers based on Bus Controller configuration
        self.dig_in_length = self.BCinfo.process_digital_inp_cnt * 8
        self.dig_in_buffer = [False] * self.dig_in_length
        self.dig_out_length = self.BCinfo.process_digital_out_cnt * 8
        self.dig_out_buffer = [False] * self.dig_out_length
        self.ana_in_length = self.BCinfo.process_analog_inp_cnt
        self.ana_in_buffer = [0] * self.ana_in_length
        self.ana_out_length = self.BCinfo.process_analog_out_cnt * 8
        self.ana_out_buffer = [0] * self.ana_out_length

    def Disconnect(self):
        """
        Disconnects from the Modbus TCP server.

        Closes the Modbus connection, stops the refresh timer (if applicable),
        and releases Bus Controller and Module information.
        """
        if self.client:
            self.client.close()  # Close the Modbus connection
            self.client = None
        else:
            return  # Exit if no client is connected

        self._connected = False  # Update connection status
        if self.BCinfo and self.BCinfo.RefreshTimer:
            self.BCinfo.RefreshTimer.stop()  # Stop the refresh timer
        self.BCinfo = None  # Release Bus Controller info
        self.MDinfo = None  # Release Module info

        self._debug_message(1, "Disconnected from Modbus server")

    def MasterMDinfo(self):
        """
        Retrieves and stores information about connected modules.

        This method iterates through the modules connected to the Bus Controller
        and retrieves their information using the MasterBRMDinfo class. It populates
        the MDinfo list with module details.

        Raises:
            OnException: If there is an error retrieving module information.
        """
        self.MDinfo = []  # Initialize the module info list
        try:
            module_index = 0
            while True:
                MDinfo_tmp = MasterBRMDinfo(self, module_index)  # Get info for the next module
                if MDinfo_tmp.status != 0:
                    self.MDinfo.append(MDinfo_tmp)  # Add module info to the list
                    self._debug_message(1, f"Found module: {MDinfo_tmp.name}")
                    module_index += 1
                else:
                    break  # Exit loop when no more modules are found
        except ModbusIOException as e:
            raise OnException(self.excDevice, f"Error retrieving module info: {e}")
        except Exception as error:
            raise OnException(self.excUnhandled, f"Unhandled error in MasterMDinfo: {error}")

    def ReadDigitalInputs(self, module_nr, size, offset=0):
        """
        Reads digital inputs from a specified module.

        Args:
            module_nr (int): The module number to read from (0-based index).
            size (int): The number of digital inputs to read.
            offset (int, optional): The starting offset within the module's
                                 digital inputs. Defaults to 0.

        Returns:
            list: A list of boolean values representing the digital input states.
                  Returns None if validation fails.

        Raises:
            OnException: If there is a connection error, invalid module number,
                         invalid data size, no digital input data, or an error
                         reading from the server.
        """
        data = [False] * size  # Initialize the data buffer

        if self._ValidateData(module_nr, size):  # Validate input parameters
            if self.MDinfo[module_nr].digital_in_index != 0xFFFF:  # Check if module has digital inputs
                # Check if the requested size is within the bounds of the buffer
                if size <= len(self.dig_in_buffer) - (
                    self.MDinfo[module_nr].digital_in_index * 8 + offset
                ):
                    try:
                        # Read digital inputs from the Modbus server
                        response = self.client.read_discrete_inputs(
                            address=self.MDinfo[module_nr].digital_in_index * 8 + offset,
                            count=size,
                        )
                        if not response.isError():
                            data = response.bits[:size]  # Extract the input values
                        else:
                            raise OnException(
                                self.excDataEmptyAnswer, "Error reading digital inputs"
                            )  # Raise exception if read fails
                        return data
                    except ModbusIOException as e:
                        raise OnException(self.excDevice, f"Modbus error reading digital inputs: {e}")
                    except Exception as e:
                        raise OnException(self.excUnhandled, f"Unhandled error reading digital inputs: {e}")
                else:
                    raise OnException(
                        self.excDataSize, "Invalid digital input data size"
                    )  # Raise exception if data size is invalid
            else:
                raise OnException(
                    self.excNoDigInData, "Module has no digital input data"
                )  # Raise exception if module has no digital inputs
        return None  # Return None if validation fails

    def WriteDigitalOutputs(self, module_nr, values, offset=0):
        """
        Writes digital outputs to a specified module.

        Args:
            module_nr (int): The module number to write to (0-based index).
            values (list): A list of boolean values representing the digital
                           output states to write.
            offset (int, optional): The starting offset within the module's
                                 digital outputs. Defaults to 0.

        Returns:
            bool: True if the write operation was successful, False otherwise.

        Raises:
            OnException: If there is a connection error, invalid module number,
                         invalid data size, or no digital output data.
        """
        if self._ValidateData(module_nr, len(values)):  # Validate input parameters
            if self.MDinfo[module_nr].digital_out_index != 0xFFFF:  # Check if module has digital outputs
                # Check if the number of values to write is within the bounds of the buffer
                if len(values) <= len(self.dig_out_buffer) - (
                    self.MDinfo[module_nr].digital_out_index * 8 + offset
                ):
                    try:
                        self.client.write_coils(
                            address=self.MDinfo[module_nr].digital_out_index * 8 + offset,
                            values=values,
                        )  # Write the output values
                        return True
                    except ModbusIOException as e:
                        raise OnException(self.excDevice, f"Modbus error writing digital outputs: {e}")
                    except Exception as e:
                        raise OnException(self.excUnhandled, f"Unhandled error writing digital outputs: {e}")
                else:
                    raise OnException(
                        self.excDataSize, "Invalid digital output data size"
                    )  # Raise exception if data size is invalid
            else:
                raise OnException(
                    self.excNoDigOutData, "Module has no digital output data"
                )  # Raise exception if module has no digital outputs
        return False  # Return False if validation fails

    def ReadAnalogInputs(self, module_nr, size, offset=0):
        """
        Reads analog inputs from a specified module.

        Args:
            module_nr (int): The module number to read from (0-based index).
            size (int): The number of analog inputs to read.
            offset (int, optional): The starting offset within the module's
                                 analog inputs. Defaults to 0.

        Returns:
            list: A list of integer values representing the analog input values.
                  Returns None if validation fails.

        Raises:
            OnException: If there is a connection error, invalid module number,
                         invalid data size, no analog input data, or an error
                         reading from the server.
        """
        data = [0] * size  # Initialize the data buffer

        if self._ValidateData(module_nr, size):  # Validate input parameters
            if self.MDinfo[module_nr].analog_in_index != 0xFFFF:  # Check if module has analog inputs
                # Check if the requested size is within the bounds of the buffer
                if size <= len(self.ana_in_buffer) - (
                    self.MDinfo[module_nr].analog_in_index // 2 + offset
                ):
                    try:
                        # Read analog inputs from the Modbus server
                        response = self.client.read_input_registers(
                            address=self.MDinfo[module_nr].analog_in_index // 2 + offset,
                            count=size,
                        )
                        if not response.isError():
                            data = response.registers  # Extract the input values
                        else:
                            raise OnException(
                                self.excDataEmptyAnswer, "Error reading analog inputs"
                            )  # Raise exception if read fails
                        return data
                    except ModbusIOException as e:
                        raise OnException(self.excDevice, f"Modbus error reading analog inputs: {e}")
                    except Exception as e:
                        raise OnException(self.excUnhandled, f"Unhandled error reading analog inputs: {e}")
                else:
                    raise OnException(
                        self.excDataSize, "Invalid analog input data size"
                    )  # Raise exception if data size is invalid
            else:
                raise OnException(
                    self.excNoAnaInData, "Module has no analog input data"
                )  # Raise exception if module has no analog inputs
        return None  # Return None if validation fails

    def WriteAnalogOutputs(self, module_nr, values, offset=0):
        """
        Writes analog outputs to a specified module.

        Args:
            module_nr (int): The module number to write to (0-based index).
            values (list or int): The analog output value(s) to write. Can be a
                                 single value or a list of values.
            offset (int, optional): The starting offset within the module's
                                 analog outputs. Defaults to 0.

        Returns:
            bool: True if the write operation was successful, False otherwise.

        Raises:
            OnException: If there is a connection error, invalid module number,
                         invalid data size, or no analog output data.
        """
        # Ensure values is always a list
        if not isinstance(values, list):
            values = [values]

        if self._ValidateData(module_nr, len(values)):  # Validate input parameters
            if self.MDinfo[module_nr].analog_out_index != 0xFFFF:  # Check if module has analog outputs
                # Check if the number of values to write is within the bounds of the buffer
                if len(values) <= len(self.ana_out_buffer) - (
                    self.MDinfo[module_nr].analog_out_index // 2 + offset
                ):
                    try:
                        self.client.write_registers(
                            address=self.MDinfo[module_nr].analog_out_index // 2 + offset,
                            values=values,
                        )  # Write the output values
                        return True
                    except ModbusIOException as e:
                        raise OnException(self.excDevice, f"Modbus error writing analog outputs: {e}")
                    except Exception as e:
                        raise OnException(self.excUnhandled, f"Unhandled error writing analog outputs: {e}")
                else:
                    raise OnException(
                        self.excDataSize, "Invalid analog output data size"
                    )  # Raise exception if data size is invalid
            else:
                raise OnException(
                    self.excNoAnaOutData, "Module has no analog output data"
                )  # Raise exception if module has no analog outputs
        return False  # Return False if validation fails

    def _ValidateData(self, module_nr, size):
        """
        Validates common data access parameters.

        This internal method checks if the connection is active, if the module
        number is valid, and if the data size is greater than zero.

        Args:
            module_nr (int): The module number being accessed.
            size (int): The size of the data being accessed.

        Raises:
            OnException: If any validation check fails.
        """
        if not self._connected:
            raise OnException(self.excConnection, "Not connected to Modbus server")  # Raise exception if not connected
        if module_nr > len(self.MDinfo) - 1:
            raise OnException(self.excNoModule, "Invalid module number")  # Raise exception if module number is invalid
        if size == 0:
            raise OnException(self.excDataSize, "Data size cannot be zero")  # Raise exception if data size is zero
        return True  # Return True if all checks pass

    def _SyncReadWord(self, adr):
        """
        Reads a single 16-bit word (register) from the Modbus server.

        This is an internal method for synchronous reading of a single register.

        Args:
            adr (int): The Modbus address to read from.

        Returns:
            int: The value of the word read from the address.

        Raises:
            OnException: If there is an error reading the word.
        """
        if self._connected:
            try:
                response = self.client.read_input_registers(address=adr, count=1)
                if not response.isError():
                    return response.registers[0]
                else:
                    raise OnException(
                        response.exception_code, "Error reading word from Modbus"
                    )
            except ModbusIOException as e:
                raise OnException(self.excDevice, f"Modbus error during _SyncReadWord: {e}")
            except Exception as e:
                raise OnException(self.excUnhandled, f"Unhandled error in _SyncReadWord: {e}")
        return 0xFFFF  # Return 0xFFFF if not connected

    def _SyncReadRegisters(self, adr, cnt):
        """
        Reads multiple 16-bit registers from the Modbus server.

        This is an internal method for synchronous reading of multiple registers.

        Args:
            adr (int): The starting Modbus address to read from.
            cnt (int): The number of registers to read.

        Returns:
            list: A list of register values.

        Raises:
            OnException: If there is an error reading the registers.
        """
        if self._connected:
            try:
                response = self.client.read_input_registers(address=adr, count=cnt)
                if not response.isError():
                    return response.registers
                else:
                    raise OnException(
                        response.exception_code, "Error reading registers from Modbus"
                    )
            except ModbusIOException as e:
                raise OnException(self.excDevice, f"Modbus error during _SyncReadRegisters: {e}")
            except Exception as e:
                raise OnException(self.excUnhandled, f"Unhandled error in _SyncReadRegisters: {e}")
        return 0xFFFF  # Return 0xFFFF if not connected

    def _SyncWriteRegisters(self, adr, values):
        """
        Writes one or more 16-bit values to the Modbus server.

        This is an internal method for synchronous writing to registers.

        Args:
            adr (int): The starting Modbus address to write to.
            values (list or int): The value(s) to write. Can be a single value
                                 or a list of values.

        Returns:
            list: The written values if successful.

        Raises:
            OnException: If there is an error writing to the registers.
        """
        if self._connected:
            try:
                if isinstance(values, list):
                    response = self.client.write_registers(address=adr, values=values)
                else:
                    response = self.client.write_register(address=adr, value=values)
                if not response.isError():
                    return response.registers
                else:
                    raise OnException(
                        response.exception_code, "Error writing to Modbus register"
                    )
            except ModbusIOException as e:
                raise OnException(self.excDevice, f"Modbus error during _SyncWriteRegisters: {e}")
            except Exception as e:
                raise OnException(self.excUnhandled, f"Unhandled error in _SyncWriteRegisters: {e}")
        return 0xFFFF  # Return 0xFFFF if not connected

    def _Bit2Byte(self, values):
        """
        Converts a list of bits into a byte array.

        Args:
            values (list): A list of bits (0 or 1).

        Returns:
            bytearray: A byte array representation of the bits.
        """
        # Calculate the number of bytes needed to represent the bits
        data = bytearray(len(values) // 8 + (1 if len(values) % 8 > 0 else 0))
        # Iterate through the byte array
        for x in range(len(data)):
            # Iterate through each bit in the byte
            for y in range(8):
                # Set the corresponding bit in the byte
                data[x] |= (values[x * 8 + y] << y)
                # Break if all bits are processed
                if x * 8 + y + 1 == len(values):
                    break
        return data

    def _Byte2Word(self, byte1, byte2):
        """
        Converts two bytes into a signed 16-bit integer (word).

        Args:
            byte1 (int): The first byte.
            byte2 (int): The second byte.

        Returns:
            int: The signed 16-bit integer.
        """
        # Use struct.unpack to convert the two bytes into a signed 16-bit integer
        return struct.unpack(">h", bytes([byte2, byte1]))[0]

    def _Byte2Long(self, byte1, byte2, byte3, byte4):
        """
        Converts four bytes into a signed 32-bit integer (long).

        Args:
            byte1 (int): The first byte.
            byte2 (int): The second byte.
            byte3 (int): The third byte.
            byte4 (int): The fourth byte.

        Returns:
            int: The signed 32-bit integer.
        """
        # Use struct.unpack to convert the four bytes into a signed 32-bit integer
        return struct.unpack(">i", bytes([byte4, byte3, byte2, byte1]))[0]

    def _ByteArray2WordArray(self, values):
        """
        Converts a byte array into an array of 16-bit words.

        Args:
            values (list): A list of bytes.

        Returns:
            list: A list of 16-bit words.
        """
        # Initialize the result array with half the size of the input byte array
        result = [0] * (len(values) // 2)
        # Iterate through the byte array in steps of 2
        for x in range(0, len(values), 2):
            # Convert each pair of bytes into a 16-bit word
            result[x // 2] = self._Byte2Word(values[x], values[x + 1])
        return result

    def _WordArray2WordByte(self, values):
        """
        Converts an array of 16-bit words into a byte array.

        Args:
            values (list): A list of 16-bit words.

        Returns:
            bytearray: A byte array representation of the words.
        """
        # Initialize an empty byte array
        byte_array = bytearray()
        # Iterate through the word array
        for word in values:
            # Pack each word as a big-endian 16-bit unsigned integer and append to the byte array
            byte_array.extend(struct.pack(">H", word))
        return byte_array

    def _debug_message(self, debug_level, message):
        """
        Prints a debug message with a timestamp if the debug level is sufficient.

        Args:
            debug_level (int): The level of the debug message.
            message (str): The debug message to print.
        """
        # Check if the current debug level is sufficient to print the message
        if self._debug >= debug_level:
            # Generate a timestamp in the format YYYY-MM-DD HH:MM:SS
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Print the debug message with the timestamp
            print(f"[{timestamp}] {message}")