import time
import threading

# ------------------------------------------------------------------------------------------------------
class OnException(Exception):
    """
    Custom exception class for handling errors in the Modbus communication.
    
    This class extends the standard Exception class to provide specific error
    handling for Modbus-related operations.
    
    Attributes:
        id (int): An error code associated with the exception.
        message (str): A descriptive error message that explains the error.
    """
    def __init__(self, id=None, message=None):
        """
        Initialize the OnException instance.
        
        Args:
            id (int, optional): The error code. Defaults to None.
            message (str, optional): The error message. Defaults to None.
        """
        self.id = id
        self.message = message

# ------------------------------------------------------------------------------------------------------
class RefreshTimer:
    """
    Implements a cyclic timer for periodic tasks using threading.Timer.
    
    This class creates a timer that executes a specified function at regular intervals.
    It provides methods to start, stop, and manage the timer's execution.
    """
    def __init__(self, interval, task_function):
        """
        Initialize the RefreshTimer with an interval and task function.

        Args:
            interval (float): Time interval in seconds between task executions.
            task_function (callable): The function to execute cyclically.
        """
        self.interval = interval  # Time between executions in seconds
        self.task_function = task_function  # Function to call periodically
        self._stop_event = threading.Event()  # Event to signal timer stopping

    def _run(self):
        """
        Internal method that runs the task function and schedules the next execution.
        
        This method is called recursively to implement the cyclic behavior.
        It checks the stop event before executing the task and scheduling the next run.
        """
        if not self._stop_event.is_set():
            self.task_function()  # Execute the task

            # Schedule the next execution using threading.Timer
            threading.Timer(self.interval, self._run).start()

    def start(self):
        """
        Start the cyclic task.
        
        Clears the stop event and initiates the first execution cycle.
        """
        self._stop_event.clear()  # Clear any previous stop signal
        self._run()  # Start the execution cycle

    def stop(self):
        """
        Stop the cyclic task.
        
        Sets the stop event to prevent further executions of the task.
        Any currently running task will complete, but no new tasks will be scheduled.
        """
        self._stop_event.set()  # Signal to stop further executions

# ------------------------------------------------------------------------------------------------------
class MasterBRBCinfo:
    """
    Class for accessing and managing B&R Bus Controller information and settings.
    
    This class provides properties and methods to read and write various parameters
    of a B&R Bus Controller via Modbus TCP, including network settings, watchdog configuration,
    product data, and process data statistics.
    """
    def __init__(self, BRmaster):
        """
        Initialize the MasterBRBCinfo instance.
        
        Args:
            BRmaster (MasterBRBC): The master Modbus client object that handles the communication.
        """
        self.BRmaster = BRmaster  # Reference to the master Modbus client
        self.RefreshTimer = None  # Timer for watchdog refresh
        self._refresh_interval = 1  # Default refresh interval in seconds

    def __del__(self):
        """
        Destructor for cleaning up resources when the instance is deleted.
        
        Stops the refresh timer if it's active to prevent memory leaks and
        dangling thread references.
        """
        # Stop the refresh timer when the object is destroyed
        if self.RefreshTimer:
            self.RefreshTimer.stop()
            self.BRmaster._debug_message(1, "Refresh timer stopped")

    def _string_to_address(self, adr):
        """
        Convert an IP address string to a list of integers.
        
        Args:
            adr (str): IP address in dot-decimal notation (e.g., "192.168.1.1").
            
        Returns:
            list: List of integers representing the IP address, or None if conversion fails.
        """
        try:
            return [int(x) for x in adr.split('.')]
        except ValueError:
            return None

    # ---- Network Communication Properties ----
    
    @property
    def com_ip(self):
        """
        Get the current IP address of the Bus Controller.
        
        Returns:
            str: The current IP address in dot-decimal notation, or "error" if reading fails.
        """
        values = self.BRmaster._SyncReadRegisters(0x1013, 4)  # Read 4 registers from address 0x1013
        values = self.BRmaster._WordArray2WordByte(values)    # Convert word array to byte array
        if values is None or len(values) != 8:
            return "error"
        # Format as IP address (values[1], [3], [5], [7] contain the actual octets)
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @property
    def com_ip_flash(self):
        """
        Get the IP address stored in flash memory (persistent across reboots).
        
        Returns:
            str: The flash IP address in dot-decimal notation, or "error" if reading fails.
        """
        values = self.BRmaster._SyncReadRegisters(0x1003, 4)  # Read from flash memory address
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 8:
            return "error"
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @com_ip_flash.setter
    def com_ip_flash(self, value):
        """
        Set the IP address in flash memory (will be used after reboot).
        
        Args:
            value (str): The IP address to set in dot-decimal notation.
        """
        values = self._string_to_address(value)  # Convert string to list of integers
        if values:
            self.BRmaster._SyncWriteRegisters(0x1003, values)  # Write to flash memory address

    @property
    def com_mac(self):
        """
        Get the MAC address of the Bus Controller.
        
        Returns:
            str: The MAC address in hexadecimal notation with hyphens, or "error" if reading fails.
        """
        values = self.BRmaster._SyncReadRegisters(0x1000, 3)  # Read 3 registers (6 bytes) for MAC
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 6:
            return "error"
        # Format as MAC address (XX-XX-XX-XX-XX-XX)
        return '-'.join(f"{x:02X}" for x in values)

    # ---- Watchdog Properties and Methods ----
    
    @property
    def watchdog_threshold(self):
        """
        Get the watchdog timeout threshold in milliseconds.
        
        Returns:
            int: The watchdog threshold value.
        """
        return self.BRmaster._SyncReadWord(0x1040)

    @watchdog_threshold.setter
    def watchdog_threshold(self, value):
        """
        Set the watchdog timeout threshold in milliseconds.
        
        Args:
            value (int): The watchdog threshold value to set.
        """
        self.BRmaster._SyncWriteRegisters(0x1040, value)

    @property
    def watchdog_elapsed(self):
        """
        Get the elapsed time since the last watchdog reset in milliseconds.
        
        Returns:
            int: The elapsed time since last reset.
        """
        return self.BRmaster._SyncReadWord(0x1041)

    @property
    def watchdog_status(self):
        """
        Get the current watchdog status.
        
        Returns:
            int: The status code (0xC1 = active, 0xC2 = expired).
        """
        return self.BRmaster._SyncReadWord(0x1042)

    def watchdog_reset(self):
        """
        Reset the watchdog timer and start the refresh timer.
        
        This method resets the watchdog on the Bus Controller and sets up a periodic
        timer to keep resetting it at regular intervals (half the watchdog threshold).
        """
        # Set refresh interval to half the watchdog threshold (in seconds)
        self._refresh_interval = self.watchdog_threshold/2000
        # Send watchdog reset command to
        self.BRmaster._SyncWriteRegisters(0x1044, 0xc1)

        if self.RefreshTimer:
            self.RefreshTimer.stop()
            self.BRmaster._debug_message(1, "Refresh timer stopped")

        self.RefreshTimer = RefreshTimer(interval=self._refresh_interval, task_function=self._RefreshTimer_Elapsed)
        self.RefreshTimer.start()
        self.BRmaster._debug_message(1, "Refresh timer started")

    def _RefreshTimer_Elapsed(self):
        try:
            if self.BRmaster._connected:
                if self.watchdog_status == 0xC2:
                    raise OnException(self.BRmaster.excWatchdog)
                else:
                    self.BRmaster._debug_message(2, "Watchdog is ok")

                response = self.BRmaster.client.read_input_registers(address=0x1042, count=1)
                if response.isError():
                    raise self.BRmaster.OnException(response.exception_code, 'error reading to register')
            
        except Exception as error:
            raise error

    # ---- Product Data Properties ----

    @property
    def productdata_serial(self):
        """
        Get the serial number of the Bus Controller.
        
        Returns:
            str: The serial number as a 9-digit string, or "error" if reading fails.
        """
        values = self.BRmaster._SyncReadRegisters(0x1080, 3)  # Read 3 registers for serial number
        values = self.BRmaster._WordArray2WordByte(values)    # Convert to byte array
        if values is None or len(values) != 6:
            return "error"
        # Format as 9-digit serial number (3 digits for each value)
        return f"{values[0]:03}{values[1]:03}{values[2]:03}"

    @property
    def productdata_code(self):
        """
        Get the product code of the Bus Controller.
        
        Returns:
            int: The product code.
        """
        return self.BRmaster._SyncReadWord(0x1083)

    @property
    def productdata_hw_major(self):
        """
        Get the major hardware version of the Bus Controller.
        
        Returns:
            int: The major hardware version.
        """
        return self.BRmaster._SyncReadWord(0x1084)

    @property
    def productdata_hw_minor(self):
        """
        Get the minor hardware version of the Bus Controller.
        
        Returns:
            int: The minor hardware version.
        """
        return self.BRmaster._SyncReadWord(0x1085)

    @property
    def productdata_fw_major(self):
        """
        Get the major firmware version of the Bus Controller.
        
        Returns:
            int: The major firmware version number.
        """
        return self.BRmaster._SyncReadWord(0x1086)

    @property
    def productdata_fw_minor(self):
        """
        Get the minor firmware version of the Bus Controller.
        
        Returns:
            int: The minor firmware version number.
        """
        return self.BRmaster._SyncReadWord(0x1087)

    @property
    def productdata_hw_fpga(self):
        """
        Get the FPGA hardware version of the Bus Controller.
        
        Returns:
            int: The FPGA hardware version.
        """
        return self.BRmaster._SyncReadWord(0x1088)

    @property
    def productdata_boot(self):
        """
        Get the bootloader version of the Bus Controller.
        
        Returns:
            int: The bootloader version.
        """
        return self.BRmaster._SyncReadWord(0x1089)

    @property
    def productdata_fw_major_def(self):
        """
        Get the default major firmware version of the Bus Controller.
        
        Returns:
            int: The default major firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108A)

    @property
    def productdata_fw_minor_def(self):
        """
        Get the default minor firmware version of the Bus Controller.
        
        Returns:
            int: The default minor firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108B)

    @property
    def productdata_fw_major_upd(self):
        """
        Get the update major firmware version of the Bus Controller.
        
        Returns:
            int: The update major firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108C)

    @property
    def productdata_fw_minor_upd(self):
        """
        Get the update minor firmware version of the Bus Controller.
        
        Returns:
            int: The update minor firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108D)

    @property
    def productdata_fw_fpga_def(self):
        """
        Get the default FPGA firmware version of the Bus Controller.
        
        Returns:
            int: The default FPGA firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108E)

    @property
    def productdata_fw_fpga_upd(self):
        """
        Get the update FPGA firmware version of the Bus Controller.
        
        Returns:
            int: The update FPGA firmware version.
        """
        return self.BRmaster._SyncReadWord(0x108F)

    # ---- Modbus Statistics Properties ----

    @property
    def modbus_refresh(self):
        """
        Get the current watchdog refresh interval in seconds.
        
        Returns:
            float: The refresh interval in seconds.
        """
        return self._refresh_interval

    @property
    def modbus_clients(self):
        """
        Get the number of currently connected Modbus clients.
        
        Returns:
            int: The number of connected clients.
        """
        return self.BRmaster._SyncReadWord(0x10C0)

    @property
    def modbus_global_tel_cnt(self):
        """
        Get the global telegram count since power-up.
        
        Returns:
            list: 4 register values representing the counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10C1, 4)

    @property
    def modbus_local_tel_cnt(self):
        """
        Get the local telegram count for the current connection.
        
        Returns:
            list: 4 register values representing the local telegram counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10C3, 4)

    @property
    def modbus_global_prot_cnt(self):
        """
        Get the global protocol error count since power-up.
        
        Returns:
            list: 4 register values representing the global protocol error counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10C5, 4)

    @property
    def modbus_local_prot_cnt(self):
        """
        Get the local protocol error count for the current connection.
        
        Returns:
            list: 4 register values representing the local protocol error counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10C7, 4)

    @property
    def modbus_global_prot_frag_cnt(self):
        """
        Get the global protocol fragment count since power-up.
        
        Returns:
            list: 4 register values representing the global protocol fragment counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10D1, 4)

    @property
    def modbus_local_prot_frag_cnt(self):
        """
        Get the local protocol fragment count for the current connection.
        
        Returns:
            list: 4 register values representing the local protocol fragment counter.
        """
        return self.BRmaster._SyncReadRegisters(0x10D3, 4)

    @property
    def modbus_global_max_cmd(self):
        """
        Get the maximum global command execution time in microseconds.
        
        Returns:
            list: 4 register values representing the maximum execution time.
        """
        return self.BRmaster._SyncReadRegisters(0x10C9, 4)

    @property
    def modbus_local_max_cmd(self):
        """
        Get the maximum local command execution time in microseconds.
        
        Returns:
            list: 4 register values representing the maximum execution time.
        """
        return self.BRmaster._SyncReadRegisters(0x10CB, 4)

    @property
    def modbus_global_min_cmd(self):
        """
        Get the minimum global command execution time in microseconds.
        
        Returns:
            list: 4 register values representing the minimum execution time.
        """
        return self.BRmaster._SyncReadRegisters(0x10CD, 4)

    @property
    def modbus_local_min_cmd(self):
        """
        Get the minimum local command execution time in microseconds.
        
        Returns:
            list: 4 register values representing the minimum execution time.
        """
        return self.BRmaster._SyncReadRegisters(0x10CF, 4)

    # ---- Process Data Properties ----

    @property
    def process_modules(self):
        """
        Get the number of configured I/O modules.
        
        Returns:
            int: The number of configured modules.
        """
        return self.BRmaster._SyncReadWord(0x1100)

    @property
    def process_analog_inp_cnt(self):
        """
        Get the count of analog input registers.
        
        Returns:
            int: The number of analog input registers.
        """
        return self.BRmaster._SyncReadWord(0x1101)

    @property
    def process_analog_inp_size(self):
        """
        Get the size of analog input data in bytes.
        
        Returns:
            int: The size of analog input data.
        """
        return self.BRmaster._SyncReadWord(0x1102)

    @property
    def process_analog_out_cnt(self):
        """
        Get the count of analog output registers.
        
        Returns:
            int: The number of analog output registers.
        """
        return self.BRmaster._SyncReadWord(0x1103)

    @property
    def process_analog_out_size(self):
        """
        Get the size of analog output data in bytes.
        
        Returns:
            int: The size of analog output data.
        """
        return self.BRmaster._SyncReadWord(0x1104)

    @property
    def process_digital_inp_cnt(self):
        """
        Get the count of digital input bytes.
        
        Returns:
            int: The number of digital input bytes.
        """
        return self.BRmaster._SyncReadWord(0x1105)

    @property
    def process_digital_inp_size(self):
        """
        Get the size of digital input data in bits.
        
        Returns:
            int: The size of digital input data.
        """
        return self.BRmaster._SyncReadWord(0x1106)

    @property
    def process_digital_out_cnt(self):
        """
        Get the count of digital output bytes.
        
        Returns:
            int: The number of digital output bytes.
        """
        return self.BRmaster._SyncReadWord(0x1107)

    @property
    def process_digital_out_size(self):
        """
        Get the size of digital output data in bits.
        
        Returns:
            int: The size of digital output data.
        """
        return self.BRmaster._SyncReadWord(0x1108)

    @property
    def process_status_out_cnt(self):
        """
        Get the count of status output bytes.
        
        Returns:
            int: The number of status output bytes.
        """
        return self.BRmaster._SyncReadWord(0x1107)

    @property
    def process_status_out_size(self):
        """
        Get the size of status output data in bits.
        
        Returns:
            int: The size of status output data.
        """
        return self.BRmaster._SyncReadWord(0x1108)

    @property
    def process_status_x2x_cnt(self):
        """
        Get the count of X2X status bytes.
        
        Returns:
            int: The number of X2X status bytes.
        """
        return self.BRmaster._SyncReadWord(0x1105)

    @property
    def process_status_x2x_size(self):
        """
        Get the size of X2X status data in bits.
        
        Returns:
            int: The size of X2X status data.
        """
        return self.BRmaster._SyncReadWord(0x1106)

    # ---- Control Methods ----

    def ctrl_save(self):
        """
        Save the current configuration to flash memory.
        
        This ensures that settings are retained after a power cycle.
        """
        self.BRmaster._SyncWriteRegisters(0x1140, 0xC1)

    def ctrl_load(self):
        """
        Load configuration from flash memory.
        
        This restores settings from flash to the active configuration.
        """
        self.BRmaster._SyncWriteRegisters(0x1141, 0xC1)

    def ctrl_erase(self):
        """
        Erase the configuration in flash memory.
        
        This removes all persistent settings from flash memory.
        """
        self.BRmaster._SyncWriteRegisters(0x1142, 0xC1)

    def ctrl_reboot(self):
        """
        Reboot the Bus Controller.
        
        This initiates a complete restart of the Bus Controller.
        """
        self.BRmaster._SyncWriteRegisters(0x1143, 0xC0)

    def ctrl_close(self):
        """
        Close all open connections to the Bus Controller.
        
        This forcibly closes all active client connections.
        """
        self.BRmaster._SyncWriteRegisters(0x1144, 0xC1)

    def ctrl_reset_cfg(self):
        """
        Reset the Bus Controller configuration to factory defaults.
        
        This method performs a sequence of operations to reset the configuration
        and then reboots the Bus Controller.
        """
        self.BRmaster._SyncWriteRegisters(0x1145, 0xC0)
        time.sleep(0.02)
        self.BRmaster._SyncWriteRegisters(0x1146, 0xC1)
        time.sleep(0.02)
        self.BRmaster._SyncWriteRegisters(0x1188, 0xC0)
        time.sleep(0.05)
        self.BRmaster._SyncWriteRegisters(0x1140, 0xC1)
        time.sleep(2)
        self.BRmaster._SyncWriteRegisters(0x1143, 0xC1)

    # ---- Miscellaneous Properties ----

    @property
    def misc_node(self):
        """
        Get the node ID of the Bus Controller.
        
        Returns:
            int: The node ID.
        """
        return self.BRmaster._SyncReadWord(0x1180)

    @property
    def misc_init_delay(self):
        """
        Get the initialization delay in milliseconds.
        
        Returns:
            int: The delay value in milliseconds.
        """
        return self.BRmaster._SyncReadWord(0x1181)

    @misc_init_delay.setter
    def misc_init_delay(self, value):
        """
        Set the initialization delay in milliseconds.
        
        Args:
            value (int): The delay value in milliseconds.
        """
        self.BRmaster._SyncWriteRegisters(0x1181, value)

    @property
    def misc_check_io(self):
        """
        Get the I/O checking mode of the Bus Controller.
        
        Returns:
            int: The I/O checking mode value.
        """
        return self.BRmaster._SyncReadWord(0x1182)

    @misc_check_io.setter
    def misc_check_io(self, value):
        """
        Set the I/O checking mode of the Bus Controller.
        
        Args:
            value (int): The I/O checking mode value to set.
        """
        self.BRmaster._SyncWriteRegisters(0x1182, value)

    @property
    def misc_telnet_pw(self):
        """
        Get the telnet password setting of the Bus Controller.
        
        Returns:
            int: The telnet password setting.
        """
        return self.BRmaster._SyncReadWord(0x1183)

    @misc_telnet_pw.setter
    def misc_telnet_pw(self, value):
        """
        Set the telnet password setting of the Bus Controller.
        
        Args:
            value (int): The telnet password setting to set.
        """
        self.BRmaster._SyncWriteRegisters(0x1183, value)

    @property
    def misc_cfg_changed(self):
        """
        Check if the configuration has changed.
        
        Returns:
            bool: True if configuration has changed, False otherwise.
        """
        return self.BRmaster._SyncReadWord(0x1184) == 0xC1

    @misc_cfg_changed.setter
    def misc_cfg_changed(self, value):
        """
        Set the configuration changed flag.
        
        Args:
            value (bool): True to set the flag, False to clear it.
        """
        self.BRmaster._SyncWriteRegisters(0x1184, 0xC1 if value else 0xC0)

    @property
    def misc_status(self):
        """
        Get the general status of the Bus Controller.
        
        Returns:
            int: The status value.
        """
        return self.BRmaster._SyncReadWord(0x1186)

    @property
    def misc_status_error(self):
        """
        Get the error status of the Bus Controller.
        
        Returns:
            int: The error status value.
        """
        return self.BRmaster._SyncReadWord(0x1187)

    # ---- X2X Bus Statistics Properties ----

    @property
    def x2x_cnt(self):
        """
        Get the X2X bus cycle counter.
        
        Returns:
            int: The number of X2X bus cycles since startup.
        """
        return self.BRmaster._SyncReadWord(0x11C0)

    @property
    def x2x_bus_off(self):
        """
        Get the X2X bus off counter.
        
        Returns:
            int: The number of bus off events.
        """
        return self.BRmaster._SyncReadWord(0x11C1)

    @property
    def x2x_syn_err(self):
        """
        Get the X2X synchronous error counter.
        
        Returns:
            int: The number of synchronous communication errors.
        """
        return self.BRmaster._SyncReadWord(0x11C2)

    @property
    def x2x_syn_bus_timing(self):
        """
        Get the X2X synchronous bus timing error count.
        
        Returns:
            int: The number of synchronous bus timing errors.
        """
        return self.BRmaster._SyncReadWord(0x11C3)

    @property
    def x2x_syn_frame_timing(self):
        """
        Get the X2X synchronous frame timing error count.
        
        Returns:
            int: The number of synchronous frame timing errors.
        """
        return self.BRmaster._SyncReadWord(0x11C4)

    @property
    def x2x_syn_frame_crc(self):
        """
        Get the X2X synchronous frame CRC error count.
        
        Returns:
            int: The number of synchronous frame CRC errors.
        """
        return self.BRmaster._SyncReadWord(0x11C5)

    @property
    def x2x_syn_frame_pending(self):
        """
        Get the X2X synchronous frame pending error count.
        
        Returns:
            int: The number of synchronous frame pending errors.
        """
        return self.BRmaster._SyncReadWord(0x11C6)

    @property
    def x2x_syn_buffer_underrun(self):
        """
        Get the X2X synchronous buffer underrun count.
        
        Returns:
            int: The number of synchronous buffer underrun errors.
        """
        return self.BRmaster._SyncReadWord(0x11C7)

    @property
    def x2x_syn_buffer_overflow(self):
        """
        Get the X2X synchronous buffer overflow count.
        
        Returns:
            int: The number of synchronous buffer overflow errors.
        """
        return self.BRmaster._SyncReadWord(0x11C8)

    @property
    def x2x_asyn_err(self):
        """
        Get the X2X asynchronous error count.
        
        Returns:
            int: The number of asynchronous communication errors.
        """
        return self.BRmaster._SyncReadWord(0x11C9)

    @property
    def x2x_asyn_bus_timing(self):
        """
        Get the X2X asynchronous bus timing error count.
        
        Returns:
            int: The number of asynchronous bus timing errors.
        """
        return self.BRmaster._SyncReadWord(0x11CA)

    @property
    def x2x_asyn_frame_timing(self):
        """
        Get the X2X asynchronous frame timing error count.
        
        Returns:
            int: The number of asynchronous frame timing errors.
        """
        return self.BRmaster._SyncReadWord(0x11CB)

    @property
    def x2x_asyn_frame_crc(self):
        """
        Get the X2X asynchronous frame CRC error count.
        
        Returns:
            int: The number of asynchronous frame CRC errors.
        """
        return self.BRmaster._SyncReadWord(0x11CC)

    @property
    def x2x_asyn_frame_pending(self):
        """
        Get the X2X asynchronous frame pending error count.
        
        Returns:
            int: The number of asynchronous frame pending errors.
        """
        return self.BRmaster._SyncReadWord(0x11CD)

    @property
    def x2x_asyn_buffer_underrun(self):
        """
        Get the X2X asynchronous buffer underrun count.
        
        Returns:
            int: The number of asynchronous buffer underrun errors.
        """
        return self.BRmaster._SyncReadWord(0x11CE)

    @property
    def x2x_asyn_buffer_overflow(self):
        """
        Get the X2X asynchronous buffer overflow count.
        
        Returns:
            int: The number of asynchronous buffer overflow errors.
        """
        return self.BRmaster._SyncReadWord(0x11CF)

    @property
    def ns_cnt(self):
        """
        Get the network packet count since startup.
        
        Returns:
            int: The number of network packets processed.
        """
        return self.BRmaster._SyncReadWord(0x1200)

    @property
    def ns_lost_cnt(self):
        """
        Get the count of lost network packets.
        
        Returns:
            int: The number of lost network packets.
        """
        return self.BRmaster._SyncReadWord(0x1201)

    @property
    def ns_oversize_cnt(self):
        """
        Get the count of oversized network packets.
        
        Returns:
            int: The number of oversized network packets.
        """
        return self.BRmaster._SyncReadWord(0x1202)

    @property
    def ns_crc_cnt(self):
        """
        Get the count of network CRC errors.
        
        Returns:
            int: The number of network CRC errors.
        """
        return self.BRmaster._SyncReadWord(0x1203)

    @property
    def ns_collision_cnt(self):
        """
        Get the count of network collision events.
        
        Returns:
            int: The number of network collision events.
        """
        return self.BRmaster._SyncReadWord(0x1206)
