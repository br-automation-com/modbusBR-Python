# MasterBRBC Class Documentation

The `MasterBRBC` class provides an interface for interacting with the B&R X20BC0087 bis controller. It includes methods for connecting to the server, reading and writing data, and managing the bus controller. The code includes a sample usage of the class, demonstrating how to create an instance, connect to the server, and perform read/write operations. 

## Revision History

### Version 1.0
- Initial version.

## Attributes

- **`Connected`** (`bool`): Indicates whether the client is connected to the Modbus server.
- **`BCinfo`**: An instance of `MasterBRBCinfo` containing bus controller information.
- **`MDinfo`** (`list`): A list of `MasterBRMDinfo` objects representing connected X20 hardware modules.

## Constants

The class defines several constants for exception handling:

- `excWatchdog = 1`
- `excTimeout = 2`
- `excConnection = 3`
- `excDevice = 4`
- `excBUSY = 6`
- `excNoModule = 10`
- `excNoDigInData = 11`
- `excNoDigOutData = 12`
- `excNoAnaInData = 13`
- `excNoAnaOutData = 14`
- `excWrongRegData = 15`
- `excDataSize = 16`
- `excDataEmptyAnswer = 17`
- `excDataRange = 20`
- `excWrongEthernetFormat = 30`
- `excUnhandled = 40`

## Methods

### `__init__(debug: int = 0)`
Initializes the `MasterBRBC` instance.

- **Parameters**:
  - `debug` (`int`): Debug level (0 = no debug, 1 = some debug, 2 = all debug).

---

### `Connect(ip: str, port: int)`
Establishes a connection to the Modbus TCP server.

- **Parameters**:
  - `ip` (`str`): The IP address of the Modbus server.
  - `port` (`int`): The port number of the Modbus server.

---

### `Disconnect()`
Disconnects from the Modbus TCP server and stops the refresh timer.

---

### `MasterMDinfo()`
Populates the `MDinfo` list with information about connected modules.

---

### `ReadDigitalInputs(module_nr: int, size: int, offset: int = 0) -> list`
Reads digital inputs from a specified module.

- **Parameters**:
  - `module_nr` (`int`): The module number.
  - `size` (`int`): The number of inputs to read.
  - `offset` (`int`): The offset for reading inputs.

- **Returns**:
  - `list`: A list of boolean values representing the digital inputs.

---

### `WriteDigitalOutputs(module_nr: int, values: list, offset: int = 0) -> bool`
Writes digital outputs to a specified module.

- **Parameters**:
  - `module_nr` (`int`): The module number.
  - `values` (`list`): A list of boolean values to write.
  - `offset` (`int`): The offset for writing outputs.

- **Returns**:
  - `bool`: `True` if successful, otherwise raises an exception.

---

### `ReadAnalogInputs(module_nr: int, size: int, offset: int = 0) -> list`
Reads analog inputs from a specified module.

- **Parameters**:
  - `module_nr` (`int`): The module number.
  - `size` (`int`): The number of inputs to read.
  - `offset` (`int`): The offset for reading inputs.

- **Returns**:
  - `list`: A list of integer values representing the analog inputs.

---

### `WriteAnalogOutputs(module_nr: int, values: list, offset: int = 0) -> bool`
Writes analog outputs to a specified module.

- **Parameters**:
  - `module_nr` (`int`): The module number.
  - `values` (`list`): A list of integer values to write.
  - `offset` (`int`): The offset for writing outputs.

- **Returns**:
  - `bool`: `True` if successful, otherwise raises an exception.

---

# MasterBRMDinfo Class Documentation

The `MasterBRMDinfo` class provides information about a specific X20 hardware module connected to the bus controller. It includes properties for accessing module details such as hardware ID, name, and configuration.

## Attributes

- **`BRmaster`**: The `MasterBRBC` instance managing the Modbus connection.
- **`mod_nr`** (`int`): The module number.

## Properties

### `status`
- **Type**: `int`
- **Description**: The status of the module.

---

### `id`
- **Type**: `int`
- **Description**: The hardware ID of the module.

---

### `name`
- **Type**: `str`
- **Description**: The name of the hardware module.

---

### `serial`
- **Type**: `str`
- **Description**: The serial number of the module. Returns `"error"` if the module is not connected.

---

### `analog_in_index`
- **Type**: `int`
- **Description**: The index of the analog inputs for the module.

---

### `analog_out_index`
- **Type**: `int`
- **Description**: The index of the analog outputs for the module.

---

### `digital_in_index`
- **Type**: `int`
- **Description**: The index of the digital inputs for the module.

---

### `digital_out_index`
- **Type**: `int`
- **Description**: The index of the digital outputs for the module.

---

### `cfg_hw`
- **Type**: `int`
- **Description**: The hardware configuration of the module.
- **Setter**: Allows updating the hardware configuration.

---

### `cfg_function_modell`
- **Type**: `int`
- **Description**: The function model configuration of the module.
- **Setter**: Allows updating the function model configuration.

---

### `cfg_index`
- **Type**: `int`
- **Description**: The configuration index of the module.
- **Setter**: Allows updating the configuration index.

---

### `cfg_size`
- **Type**: `int`
- **Description**: The configuration size of the module.
- **Setter**: Allows updating the configuration size.

---

### `cfg_firmware`
- **Type**: `int`
- **Description**: The firmware version of the module.

---

### `cfg_variant`
- **Type**: `int`
- **Description**: The variant of the module.

---

# MasterBRBCinfo Class Documentation

The `MasterBRBCinfo` class provides an interface for accessing and managing bus controller information and configuration in a Modbus TCP system.

## Attributes

- **`BRmaster`**: The `MasterBRBC` instance managing the Modbus connection.

## Properties

### Communication Properties

- **`com_ip`** (`str`): The current IP address of the bus controller.
- **`com_ip_flash`** (`str`): The stored IP address in flash memory.
  - **Setter**: Allows updating the stored IP address.
- **`com_mac`** (`str`): The MAC address of the bus controller.
- **`com_subnet_mask`** (`str`): The subnet mask of the bus controller.
  - **Setter**: Allows updating the subnet mask.
- **`com_gateway`** (`str`): The gateway address of the bus controller.
  - **Setter**: Allows updating the gateway address.
- **`com_port`** (`int`): The communication port of the bus controller.
  - **Setter**: Allows updating the communication port.
- **`com_duration`** (`int`): The communication duration.
  - **Setter**: Allows updating the communication duration.
- **`com_mtu`** (`int`): The MTU (Maximum Transmission Unit) size.
  - **Setter**: Allows updating the MTU size.
- **`com_x2x`** (`int`): The X2X communication setting.
  - **Setter**: Allows updating the X2X communication setting.
- **`com_x2x_length`** (`int`): The X2X communication length.
  - **Setter**: Allows updating the X2X communication length.

---

### Watchdog Properties

- **`watchdog_threshold`** (`int`): The watchdog threshold value.
  - **Setter**: Allows updating the threshold value.
- **`watchdog_elapsed`** (`int`): The elapsed time since the last watchdog reset.
- **`watchdog_status`** (`int`): The current status of the watchdog.
- **`watchdog_mode`** (`int`): The mode of the watchdog.
  - **Setter**: Allows updating the watchdog mode.

---

### Product Data Properties

- **`productdata_serial`** (`str`): The serial number of the product.
- **`productdata_code`** (`int`): The product code.
- **`productdata_hw_major`** (`int`): The major hardware version.
- **`productdata_hw_minor`** (`int`): The minor hardware version.
- **`productdata_fw_major`** (`int`): The major firmware version.
- **`productdata_fw_minor`** (`int`): The minor firmware version.
- **`productdata_hw_fpga`** (`int`): The FPGA hardware version.
- **`productdata_boot`** (`int`): The bootloader version.
- **`productdata_fw_major_def`** (`int`): The default major firmware version.
- **`productdata_fw_minor_def`** (`int`): The default minor firmware version.
- **`productdata_fw_major_upd`** (`int`): The updated major firmware version.
- **`productdata_fw_minor_upd`** (`int`): The updated minor firmware version.
- **`productdata_fw_fpga_def`** (`int`): The default FPGA firmware version.
- **`productdata_fw_fpga_upd`** (`int`): The updated FPGA firmware version.

---

### Process Data Properties

- **`process_modules`** (`int`): The number of process modules.
- **`process_analog_inp_cnt`** (`int`): The count of analog inputs.
- **`process_analog_inp_size`** (`int`): The size of analog inputs.
- **`process_analog_out_cnt`** (`int`): The count of analog outputs.
- **`process_analog_out_size`** (`int`): The size of analog outputs.
- **`process_digital_inp_cnt`** (`int`): The count of digital inputs.
- **`process_digital_inp_size`** (`int`): The size of digital inputs.
- **`process_digital_out_cnt`** (`int`): The count of digital outputs.
- **`process_digital_out_size`** (`int`): The size of digital outputs.

---

### Miscellaneous Properties

- **`misc_node`** (`int`): The node ID of the bus controller.
- **`misc_init_delay`** (`int`): The initialization delay.
  - **Setter**: Allows updating the initialization delay.
- **`misc_check_io`** (`int`): The I/O check setting.
  - **Setter**: Allows updating the I/O check setting.
- **`misc_telnet_pw`** (`int`): The Telnet password.
  - **Setter**: Allows updating the Telnet password.
- **`misc_cfg_changed`** (`bool`): Indicates whether the configuration has changed.
  - **Setter**: Allows updating the configuration change status.
- **`misc_status`** (`int`): The miscellaneous status.
- **`misc_status_error`** (`int`): The miscellaneous status error.

---

### Modbus Properties

- **`modbus_clients`** (`int`): The number of Modbus clients.
- **`modbus_global_tel_cnt`** (`list`): The global telegram count.
- **`modbus_local_tel_cnt`** (`list`): The local telegram count.
- **`modbus_global_prot_cnt`** (`list`): The global protocol count.
- **`modbus_local_prot_cnt`** (`list`): The local protocol count.
- **`modbus_global_prot_frag_cnt`** (`list`): The global protocol fragment count.
- **`modbus_local_prot_frag_cnt`** (`list`): The local protocol fragment count.
- **`modbus_global_max_cmd`** (`list`): The global maximum command count.
- **`modbus_local_max_cmd`** (`list`): The local maximum command count.
- **`modbus_global_min_cmd`** (`list`): The global minimum command count.
- **`modbus_local_min_cmd`** (`list`): The local minimum command count.

---

## Methods

### `ctrl_save()`
Saves the current configuration to flash memory.

---

### `ctrl_load()`
Loads the configuration from flash memory.

---

### `ctrl_erase()`
Erases the configuration from flash memory.

---

### `ctrl_reboot()`
Reboots the bus controller.

---

### `ctrl_close()`
Closes the bus controller.

---

### `ctrl_reset_cfg()`
Resets the configuration of the bus controller.

---

### `watchdog_reset()`
RResets the watchdog timer and adjusts the refresh interval.

---