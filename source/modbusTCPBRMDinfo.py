import os

# ------------------------------------------------------------------------------------------------------------
class MasterBRMDinfo:
    def __init__(self, BRmaster, mod_nr):
        self.BRmaster = BRmaster
        self.mod_nr = mod_nr
        self._id = self.BRmaster._SyncReadWord(0xA001 + mod_nr * 16)
        self._name = self._Get_HardwareName(self._id)
        self._analog_in_index = self.BRmaster._SyncReadWord(0xA004 + mod_nr * 16)
        self._analog_out_index = self.BRmaster._SyncReadWord(0xA005 + mod_nr * 16)
        self._digital_in_index = self.BRmaster._SyncReadWord(0xA006 + mod_nr * 16)
        self._digital_out_index = self.BRmaster._SyncReadWord(0xA007 + mod_nr * 16)

    @property
    def status(self):
        return self.BRmaster._SyncReadWord(0xA000 + self.mod_nr * 16)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def serial(self):
        response = self.BRmaster._SyncReadRegisters(0xA001 + self.mod_nr * 16, 3)
        if len(response) == 3:
            serial = f"{response[0]:03}{response[1]:03}{response[2]:03}"
            return serial

    @property
    def analog_in_index(self):
        return self._analog_in_index

    @property
    def analog_out_index(self):
        return self._analog_out_index

    @property
    def digital_in_index(self):
        return self._digital_in_index

    @property
    def digital_out_index(self):
        return self._digital_out_index

    @property
    def cfg_hw(self):
        return self.BRmaster._SyncReadWord(0xA008 + self.mod_nr * 16)

    @cfg_hw.setter
    def cfg_hw(self, value):
        self.BRmaster._SyncWriteRegisters(0xA008 + self.mod_nr * 16, value)

    @property
    def cfg_function_modell(self):
        return self.BRmaster._SyncReadWord(0xA009 + self.mod_nr * 16)

    @cfg_function_modell.setter
    def cfg_function_modell(self, value):
        self.BRmaster._SyncWriteRegisters(0xA009 + self.mod_nr * 16, value)

    @property
    def cfg_index(self):
        return self.BRmaster._SyncReadWord(0xA00A + self.mod_nr * 16)

    @cfg_index.setter
    def cfg_index(self, value):
        self.BRmaster._SyncWriteRegisters(0xA00A + self.mod_nr * 16, value)

    @property
    def cfg_size(self):
        return self.BRmaster._SyncReadWord(0xA00B + self.mod_nr * 16)

    @cfg_size.setter
    def cfg_size(self, value):
        self.BRmaster._SyncWriteRegisters(0xA00B + self.mod_nr * 16, value)

    @property
    def cfg_firmware(self):
        return self.BRmaster._SyncReadWord(0xA00C + self.mod_nr * 16)

    @property
    def cfg_variant(self):
        return self.BRmaster._SyncReadWord(0xA00D + self.mod_nr * 16)

    def _Get_HardwareName(self, HardwareId):
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

