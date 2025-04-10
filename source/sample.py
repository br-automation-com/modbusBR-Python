from modbusTCPBR import MasterBRBC

# Configuration constants for the Modbus TCP connection
MODBUS_IP = "192.168.1.77"  # IP address of the B&R Bus Controller
MODBUS_PORT = 502           # Standard Modbus TCP port
DEBUG_MODE = 1              # Debug level: 0 = no debug, 1 = basic debug, 2 = verbose debug

def main():
    """
    Main function demonstrating the basic functionality of the MasterBRBC class.
    
    This sample script performs the following operations:
    1. Connects to a B&R Bus Controller via Modbus TCP
    2. Sets up and activates the watchdog timer
    3. Discovers and reports all connected I/O modules
    4. Demonstrates reading digital inputs from a module
    5. Demonstrates writing digital outputs to a module
    6. Handles potential errors with appropriate error messages
    7. Ensures clean disconnection even if exceptions occur
    """
    # Initialize master object as None to enable safe cleanup in finally block
    master = None 

    try:
        # --- INITIALIZATION & CONNECTION ---
        # Create an instance of MasterBRBC with the specified debug level
        print("Creating Modbus TCP master...")
        master = MasterBRBC(DEBUG_MODE)

        # Connect to the Modbus TCP server using the configured IP and port
        print(f"Connecting to {MODBUS_IP}:{MODBUS_PORT}...")
        master.Connect(MODBUS_IP, MODBUS_PORT)
        
        # Reset the watchdog timer to prevent controller safety shutdown
        # This starts periodic watchdog refreshing in the background
        print("Setting up watchdog timer...")
        master.BCinfo.watchdog_reset()

        # --- MODULE DISCOVERY & REPORTING ---
        # Display information about all discovered modules
        if master.MDinfo:
            print("Found the following modules:")
            for i, module in enumerate(master.MDinfo):
                print("--------------------------------------------------")
                print(f"Module {i}: {module.name}")
                
                # Print I/O capabilities - 65535 (0xFFFF) indicates capability not present
                if module.digital_in_index != 65535:
                    print(f"Digital Inputs: Index {module.digital_in_index}")
                if module.digital_out_index != 65535:
                    print(f"Digital Outputs: Index {module.digital_out_index}")
                if module.analog_in_index != 65535:
                    print(f"Analog Inputs: Index {module.analog_in_index}")
                if module.analog_out_index != 65535: 
                    print(f"Analog Outputs: Index {module.analog_out_index}")
        else:
            # No modules were found - possible hardware configuration issue
            print("No modules available. Check hardware configuration.")
        print("--------------------------------------------------")     

        # --- DIGITAL I/O OPERATIONS ---
        # Read 8 digital input channels from module 1 (second module, zero-indexed)
        # This will fail with OnException(11) if the module has no digital inputs
        print("Reading digital inputs from module 1...")
        digital_inputs = master.ReadDigitalInputs(1, 8)
        print(f"Digital Inputs: {digital_inputs}")

        # Write 8 digital output channels to module 2 (third module, zero-indexed)
        # This will fail with OnException(12) if the module has no digital outputs
        print("Writing digital outputs to module 2...")
        master.WriteDigitalOutputs(2, [True, True, True, True, True, False, False, False])
        print("Digital Outputs written successfully")

        # Here you could add other operations like:
        # - Reading analog inputs
        # - Writing analog outputs
        # - Reading/writing specific module configuration parameters
        # - Using advanced Bus Controller features

    except Exception as e:
        # --- ERROR HANDLING ---
        print("Bus controller error:", e)
        
        # Handle specific OnException error codes with custom messages
        if hasattr(e, 'id'):
            if e.id == 1:
                print("Error: Watchdog has expired - connection timeout")
            elif e.id == 11:
                print("Error: Module has no digital inputs - operation not supported")
            elif e.id == 12:
                print("Error: Module has no digital outputs - operation not supported")
            elif e.id == 13:
                print("Error: Module has no analog inputs - operation not supported")
            elif e.id == 14:
                print("Error: Module has no analog outputs - operation not supported")
            else:
                print(f"Error: {str(e.message)} (Code:{str(e.id)})")
        else:
            if hasattr(e, 'message') and hasattr(e, 'id'):
                print(f"Error: {str(e.message)} (Code:{str(e.id)})")
            else:
                print(f"Error: {str(e)}")

    finally:
        # --- CLEANUP ---
        # Disconnect from the Modbus TCP server
        if master:
            print("Disconnecting from Modbus TCP server...")
            master.Disconnect()
            print("Done")

if __name__ == "__main__":
    main()
