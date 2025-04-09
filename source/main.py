from modbusTCPBR import MasterBRBC
import asyncio

MODBUS_IP = "192.168.1.77"
MODBUS_PORT = 502
DEBUG_MODE = 2  # 0 = no debug, 1 = some debug, 2 = all debug

async def main():
    # Connect to the Modbus server
    master = None 

    try:
        # Create an instance of MasterBRBC
        master = MasterBRBC(DEBUG_MODE)

        master.Connect(MODBUS_IP, MODBUS_PORT)
        await master.BCinfo.watchdog_reset()

        # List all names from MDinfo
        if master.MDinfo:
            print("Found the following modules:")
            for module in master.MDinfo:
                print("--------------------------------------------------")
                print("Module Name:", module.name)
                if module.digital_in_index != 65535:
                    print("Digital Inputs:", module.digital_in_index)
                if module.digital_out_index != 65535:
                    print("Digital Outputs:", module.digital_out_index)
                if module.analog_in_index != 65535:  
                    print("Analog Inputs:", module.analog_in_index)
                if module.analog_out_index != 65535: 
                    print("Analog Outputs:", module.analog_out_index)
        else:
            print("No MDinfo available.")
        print("--------------------------------------------------")     

        # Read digital inputs from module 1
        digital_inputs = master.ReadDigitalInputs(1, 8)
        print("Digital Inputs:", digital_inputs)

        # Write digital outputs to module 2
        master.WriteDigitalOutputs(2, [True, True, True, True, True, False, False, False])
        print("Digital Outputs written")

        master.BCinfo.ctrl_reboot()

    except Exception as e:
        print("Bus controller error:", e)
        if hasattr(e, 'id'):
            if e.id == 11:
                print("Module has no digital inputs")
            elif e.id == 12:
                print("Module has no digital outputs")
            elif e.id == 13:
                print("Module has no analog inputs")
            elif e.id == 14:
                print("Module has no analog outputs")

            else:
                print(f"Error: {str(e.message)} (Code:{str(e.id)})")

        else:
            if hasattr(e, 'message') and hasattr(e, 'id'):
                print(f"Error: {str(e.message)} (Code:{str(e.id)})")
            else:
                print(f"Error: {str(e)}")

    finally:
        # Disconnect from the Modbus server
        if master:
            await master.Disconnect()
            print("Done")

if __name__ == "__main__":
    asyncio.run(main())
