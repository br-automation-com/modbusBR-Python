import os

# ------------------------------------------------------------------------------------------------------------
class MasterBRMDinfo:
    """
    Represents information about a B&R I/O module connected to the Bus Controller.
    
    This class encapsulates module-specific information such as module identification,
    hardware configuration, I/O capabilities, and access to module-specific parameters.
    Each instance corresponds to a single physical I/O module in the system.
    
    The class provides read access to module properties, with some properties allowing
    write access for configuration purposes. Module information is retrieved from
    reserved Modbus address ranges, with each module occupying 16 consecutive registers
    starting at a base address of 0xA000 + (module_number * 16).
    """
    
    def __init__(self, BRmaster, mod_nr):
        """
        Initializes a module information object for a specific I/O module.
        
        During initialization, this method reads basic module information including
        the module ID, I/O configuration, and hardware details from the Bus Controller.
        It automatically maps the module's capabilities (digital/analog I/O) and
        retrieves its name from the hardware ID lookup table.
        
        Args:
            BRmaster: Reference to the parent MasterBRBC object for Modbus communication.
            mod_nr: Zero-based module number/slot position in the I/O rack.
        """
        # Store references to parent controller and module number
        self.BRmaster = BRmaster  # Reference to the master Modbus client
        self.mod_nr = mod_nr      # Module index/slot number (0-based)
        
        # Read basic module information from Modbus registers
        # Each module uses 16 registers starting at 0xA000 + (module_number * 16)
        self._id = self.BRmaster._SyncReadWord(0xA001 + mod_nr * 16)  # Hardware ID
        self._name = self._Get_HardwareName(self._id)  # Convert ID to human-readable name
        
        # Read I/O configuration information
        # These indices point to where this module's I/O data is located in the process image
        # A value of 0xFFFF indicates that the specific I/O type is not available
        self._analog_in_index = self.BRmaster._SyncReadWord(0xA004 + mod_nr * 16)
        self._analog_out_index = self.BRmaster._SyncReadWord(0xA005 + mod_nr * 16)
        self._digital_in_index = self.BRmaster._SyncReadWord(0xA006 + mod_nr * 16)
        self._digital_out_index = self.BRmaster._SyncReadWord(0xA007 + mod_nr * 16)

    @property
    def status(self):
        """
        Get the module status.
        
        Returns:
            int: Status code indicating the current state of the module:
                 0: Not configured/not present
                 1: OK/operational
                 2: Warning condition
                 3: Error condition
        """
        return self.BRmaster._SyncReadWord(0xA000 + self.mod_nr * 16)

    @property
    def id(self):
        """
        Get the hardware identification number.
        
        Returns:
            int: The numeric hardware ID that uniquely identifies the module type.
                 This ID corresponds to entries in the hardware list file.
        """
        return self._id

    @property
    def name(self):
        """
        Get the human-readable module name.
        
        Returns:
            str: The module name as derived from the hardware list file,
                 or "unknown (ID)" if the ID is not found in the file.
        """
        return self._name

    @property
    def serial(self):
        """
        Get the module's serial number.
        
        Reads three consecutive registers that contain the module's 
        unique serial number.
        
        Returns:
            str: A formatted 9-digit serial number string, or None if reading fails.
        """
        # Read 3 registers containing the serial number components
        response = self.BRmaster._SyncReadRegisters(0xA001 + self.mod_nr * 16, 3)
        if len(response) == 3:
            # Format as a 9-digit serial number (3 digits for each register value)
            serial = f"{response[0]:03}{response[1]:03}{response[2]:03}"
            return serial
        # Return None implicitly if reading fails or returns wrong size

    @property
    def analog_in_index(self):
        """
        Get the starting index for analog input data.
        
        Returns:
            int: The index where this module's analog input data begins in the
                 process image, or 0xFFFF if the module has no analog inputs.
        """
        return self._analog_in_index

    @property
    def analog_out_index(self):
        """
        Get the starting index for analog output data.
        
        Returns:
            int: The index where this module's analog output data begins in the
                 process image, or 0xFFFF if the module has no analog outputs.
        """
        return self._analog_out_index

    @property
    def digital_in_index(self):
        """
        Get the starting index for digital input data.
        
        Returns:
            int: The index where this module's digital input data begins in the
                 process image (in bytes, each containing 8 inputs),
                 or 0xFFFF if the module has no digital inputs.
        """
        return self._digital_in_index

    @property
    def digital_out_index(self):
        """
        Get the starting index for digital output data.
        
        Returns:
            int: The index where this module's digital output data begins in the
                 process image (in bytes, each containing 8 outputs),
                 or 0xFFFF if the module has no digital outputs.
        """
        return self._digital_out_index

    @property
    def cfg_hw(self):
        """
        Get or set the hardware configuration register value.
        
        This property allows reading and writing the hardware configuration
        register for the module. The register value determines the module's
        hardware-specific settings.
        
        Returns:
            int: The current value of the hardware configuration register.
        """
        return self.BRmaster._SyncReadWord(0xA008 + self.mod_nr * 16)

    @cfg_hw.setter
    def cfg_hw(self, value):
        """
        Set the hardware configuration register value.
        
        Args:
            value (int): The new value to write to the hardware configuration register.
        """
        self.BRmaster._SyncWriteRegisters(0xA008 + self.mod_nr * 16, value)

    @property
    def cfg_function_modell(self):
        """
        Get or set the function model configuration register value.
        
        This property allows reading and writing the function model configuration
        register for the module. The register value determines the module's
        functional behavior.
        
        Returns:
            int: The current value of the function model configuration register.
        """
        return self.BRmaster._SyncReadWord(0xA009 + self.mod_nr * 16)

    @cfg_function_modell.setter
    def cfg_function_modell(self, value):
        """
        Set the function model configuration register value.
        
        Args:
            value (int): The new value to write to the function model configuration register.
        """
        self.BRmaster._SyncWriteRegisters(0xA009 + self.mod_nr * 16, value)

    @property
    def cfg_index(self):
        """
        Get or set the index configuration register value.
        
        This property allows reading and writing the index configuration
        register for the module. The register value determines the module's
        index settings.
        
        Returns:
            int: The current value of the index configuration register.
        """
        return self.BRmaster._SyncReadWord(0xA00A + self.mod_nr * 16)

    @cfg_index.setter
    def cfg_index(self, value):
        """
        Set the index configuration register value.
        
        Args:
            value (int): The new value to write to the index configuration register.
        """
        self.BRmaster._SyncWriteRegisters(0xA00A + self.mod_nr * 16, value)

    @property
    def cfg_size(self):
        """
        Get or set the size configuration register value.
        
        This property allows reading and writing the size configuration
        register for the module. The register value determines the module's
        size settings.
        
        Returns:
            int: The current value of the size configuration register.
        """
        return self.BRmaster._SyncReadWord(0xA00B + self.mod_nr * 16)

    @cfg_size.setter
    def cfg_size(self, value):
        """
        Set the size configuration register value.
        
        Args:
            value (int): The new value to write to the size configuration register.
        """
        self.BRmaster._SyncWriteRegisters(0xA00B + self.mod_nr * 16, value)

    @property
    def cfg_firmware(self):
        """
        Get the firmware version register value.
        
        This property allows reading the firmware version register for the module.
        The register value indicates the module's firmware version.
        
        Returns:
            int: The current value of the firmware version register.
        """
        return self.BRmaster._SyncReadWord(0xA00C + self.mod_nr * 16)

    @property
    def cfg_variant(self):
        """
        Get the variant configuration register value.
        
        This property allows reading the variant configuration register for the module.
        The register value indicates the module's variant settings.
        
        Returns:
            int: The current value of the variant configuration register.
        """
        return self.BRmaster._SyncReadWord(0xA00D + self.mod_nr * 16)

    def _Get_HardwareName(self, HardwareId):
        """
        Retrieve the human-readable name for a given hardware ID.
        
        This method looks up the hardware ID in a text file containing
        hardware ID-to-name mappings. If the ID is not found, it returns
        a default "unknown" name.
        
        Args:
            HardwareId (int): The numeric hardware ID to look up.
        
        Returns:
            str: The human-readable name corresponding to the hardware ID,
                 or "unknown (ID)" if the ID is not found.
        """
        try:
            if HardwareId > 0:
                startup_dir = os.path.dirname(os.path.abspath(__file__))
                hwlist_path = os.path.join(startup_dir, 'hwlist.txt')
                with open(hwlist_path, 'r') as file:
                    for line in file:
                        parts = line.strip().split(',')
                        if len(parts) > 1 and parts[1].strip() == str(HardwareId):
                            return parts[0].strip()
            return f"unknown ({HardwareId})"
        except Exception as error:
            raise error

