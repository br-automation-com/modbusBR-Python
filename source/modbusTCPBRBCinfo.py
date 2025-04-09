import struct
import time
import asyncio

# ------------------------------------------------------------------------------------------------------
class MasterBRBCinfo:
    def __init__(self, BRmaster):
        self.BRmaster = BRmaster

    def _string_to_address(self, adr):
        try:
            return [int(x) for x in adr.split('.')]
        except ValueError:
            return None

    @property
    def com_ip(self):
        values = self.BRmaster._SyncReadRegisters(0x1013, 4)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 8:
            return "error"
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @property
    def com_ip_flash(self):
        values = self.BRmaster._SyncReadRegisters(0x1003, 4)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 8:
            return "error"
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @com_ip_flash.setter
    def com_ip_flash(self, value):
        values = self._string_to_address(value)
        if values:
            self.BRmaster._SyncWriteRegisters(0x1003, values)

    @property
    def com_mac(self):
        values = self.BRmaster._SyncReadRegisters(0x1000, 3)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 6:
            return "error"
        return '-'.join(f"{x:02X}" for x in values)

    @property
    def com_subnet_mask(self):
        values = self.BRmaster._SyncReadRegisters(0x1007, 4)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 8:
            return "error"
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @com_subnet_mask.setter
    def com_subnet_mask(self, value):
        values = self._string_to_address(value)
        if values:
            self.BRmaster._SyncWriteRegisters(0x1007, values)

    @property
    def com_gateway(self):
        values = self.BRmaster._SyncReadRegisters(0x100B, 4)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 8:
            return "error"
        return f"{values[1]}.{values[3]}.{values[5]}.{values[7]}"

    @com_gateway.setter
    def com_gateway(self, value):
        values = self._string_to_address(value)
        if values:
            self.BRmaster._SyncWriteRegisters(0x100B, values)

    @property
    def com_port(self):
        return self.BRmaster._SyncReadWord(0x100F)

    @com_port.setter
    def com_port(self, value):
        self.BRmaster._SyncWriteRegisters(0x100F, value)

    @property
    def com_duration(self):
        return self.BRmaster._SyncReadWord(0x1010)

    @com_duration.setter
    def com_duration(self, value):
        self.BRmaster._SyncWriteRegisters(0x1010, value)

    @property
    def com_mtu(self):
        return self.BRmaster._SyncReadWord(0x1011)

    @com_mtu.setter
    def com_mtu(self, value):
        self.BRmaster._SyncWriteRegisters(0x1011, value)

    @property
    def com_x2x(self):
        return self.BRmaster._SyncReadWord(0x1012)

    @com_x2x.setter
    def com_x2x(self, value):
        self.BRmaster._SyncWriteRegisters(0x1012, value)

    @property
    def com_x2x_length(self):
        return self.BRmaster._SyncReadWord(0x1017)

    @com_x2x_length.setter
    def com_x2x_length(self, value):
        self.BRmaster._SyncWriteRegisters(0x1017, value)

    @property
    def watchdog_threshold(self):
        return self.BRmaster._SyncReadWord(0x1040)

    @watchdog_threshold.setter
    def watchdog_threshold(self, value):
        self.BRmaster._SyncWriteRegisters(0x1040, value)

    @property
    def watchdog_elapsed(self):
        return self.BRmaster._SyncReadWord(0x1041)

    @property
    def watchdog_status(self):
        return self.BRmaster._SyncReadWord(0x1042)

    @property
    def watchdog_mode(self):
        return self.BRmaster._SyncReadWord(0x1043)

    @watchdog_mode.setter
    def watchdog_mode(self, value):
        self.BRmaster._SyncWriteRegisters(0x1043, value)

    async def watchdog_reset(self):
        refresh_timer = self.watchdog_threshold/2
        self.BRmaster._SyncWriteRegisters(0x1044, 0xc1)

        if self.BRmaster._refresh_task:
            self.BRmaster._refresh_task.cancel()

            # Wait for the task to finish
            try:
                await self.BRmaster._refresh_task
            except asyncio.CancelledError:
                if self.BRmaster._debug > 1:
                    print("Refresh timer stopped")

        self.BRmaster._refresh_interval = refresh_timer/1000
        self.BRmaster._refresh_task = asyncio.create_task(self.BRmaster._RefreshTimer(self.BRmaster._refresh_interval, self.BRmaster._RefreshTimer_Elapsed))
        if self.BRmaster._debug > 1:
            print("Refresh timer started")

    @property
    def productdata_serial(self):
        values = self.BRmaster._SyncReadRegisters(0x1080, 3)
        values = self.BRmaster._WordArray2WordByte(values)
        if values is None or len(values) != 6:
            return "error"
        return f"{values[0]:03}{values[1]:03}{values[2]:03}"

    @property
    def productdata_code(self):
        return self.BRmaster._SyncReadWord(0x1083)

    @property
    def productdata_hw_major(self):
        return self.BRmaster._SyncReadWord(0x1084)

    @property
    def productdata_hw_minor(self):
        return self.BRmaster._SyncReadWord(0x1085)

    @property
    def productdata_fw_major(self):
        return self.BRmaster._SyncReadWord(0x1086)

    @property
    def productdata_fw_minor(self):
        return self.BRmaster._SyncReadWord(0x1087)

    @property
    def productdata_hw_fpga(self):
        return self.BRmaster._SyncReadWord(0x1088)

    @property
    def productdata_boot(self):
        return self.BRmaster._SyncReadWord(0x1089)

    @property
    def productdata_fw_major_def(self):
        return self.BRmaster._SyncReadWord(0x108A)

    @property
    def productdata_fw_minor_def(self):
        return self.BRmaster._SyncReadWord(0x108B)

    @property
    def productdata_fw_major_upd(self):
        return self.BRmaster._SyncReadWord(0x108C)

    @property
    def productdata_fw_minor_upd(self):
        return self.BRmaster._SyncReadWord(0x108D)

    @property
    def productdata_fw_fpga_def(self):
        return self.BRmaster._SyncReadWord(0x108E)

    @property
    def productdata_fw_fpga_upd(self):
        return self.BRmaster._SyncReadWord(0x108F)

    @property
    def modbus_refresh(self):
        return self.BRmaster._refresh_interval

    @modbus_refresh.setter
    def modbus_refresh(self, value):
        self.BRmaster._MBmaster._refresh_interval = value

    @property
    def modbus_clients(self):
        return self.BRmaster._SyncReadWord(0x10C0)

    @property
    def modbus_global_tel_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10C1, 4)

    @property
    def modbus_local_tel_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10C3, 4)

    @property
    def modbus_global_prot_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10C5, 4)

    @property
    def modbus_local_prot_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10C7, 4)

    @property
    def modbus_global_prot_frag_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10D1, 4)

    @property
    def modbus_local_prot_frag_cnt(self):
        return self.BRmaster._SyncReadRegisters(0x10D3, 4)

    @property
    def modbus_global_max_cmd(self):
        return self.BRmaster._SyncReadRegisters(0x10C9, 4)

    @property
    def modbus_local_max_cmd(self):
        return self.BRmaster._SyncReadRegisters(0x10CB, 4)

    @property
    def modbus_global_min_cmd(self):
        return self.BRmaster._SyncReadRegisters(0x10CD, 4)

    @property
    def modbus_local_min_cmd(self):
        return self.BRmaster._SyncReadRegisters(0x10CF, 4)

    @property
    def process_modules(self):
        return self.BRmaster._SyncReadWord(0x1100)

    @property
    def process_analog_inp_cnt(self):
        return self.BRmaster._SyncReadWord(0x1101)

    @property
    def process_analog_inp_size(self):
        return self.BRmaster._SyncReadWord(0x1102)

    @property
    def process_analog_out_cnt(self):
        return self.BRmaster._SyncReadWord(0x1103)

    @property
    def process_analog_out_size(self):
        return self.BRmaster._SyncReadWord(0x1104)

    @property
    def process_digital_inp_cnt(self):
        return self.BRmaster._SyncReadWord(0x1105)

    @property
    def process_digital_inp_size(self):
        return self.BRmaster._SyncReadWord(0x1106)

    @property
    def process_digital_out_cnt(self):
        return self.BRmaster._SyncReadWord(0x1107)

    @property
    def process_digital_out_size(self):
        return self.BRmaster._SyncReadWord(0x1108)

    @property
    def process_status_out_cnt(self):
        return self.BRmaster._SyncReadWord(0x1107)

    @property
    def process_status_out_size(self):
        return self.BRmaster._SyncReadWord(0x1108)

    @property
    def process_status_x2x_cnt(self):
        return self.BRmaster._SyncReadWord(0x1105)

    @property
    def process_status_x2x_size(self):
        return self.BRmaster._SyncReadWord(0x1106)

    def ctrl_save(self):
        self.BRmaster._SyncWriteRegisters(0x1140, 0xC1)

    def ctrl_load(self):
        self.BRmaster._SyncWriteRegisters(0x1141, 0xC1)

    def ctrl_erase(self):
        self.BRmaster._SyncWriteRegisters(0x1142, 0xC1)

    def ctrl_reboot(self):
        self.BRmaster._SyncWriteRegisters(0x1143, 0xC0)

    def ctrl_close(self):
        self.BRmaster._SyncWriteRegisters(0x1144, 0xC1)

    def ctrl_reset_cfg(self):
        self.BRmaster._SyncWriteRegisters(0x1145, 0xC0)
        time.sleep(0.02)
        self.BRmaster._SyncWriteRegisters(0x1146, 0xC1)
        time.sleep(0.02)
        self.BRmaster._SyncWriteRegisters(0x1188, 0xC0)
        time.sleep(0.05)
        self.BRmaster._SyncWriteRegisters(0x1140, 0xC1)
        time.sleep(2)
        self.BRmaster._SyncWriteRegisters(0x1143, 0xC1)

    @property
    def misc_node(self):
        return self.BRmaster._SyncReadWord(0x1180)

    @property
    def misc_init_delay(self):
        return self.BRmaster._SyncReadWord(0x1181)

    @misc_init_delay.setter
    def misc_init_delay(self, value):
        self.BRmaster._SyncWriteRegisters(0x1181, value)

    @property
    def misc_check_io(self):
        return self.BRmaster._SyncReadWord(0x1182)

    @misc_check_io.setter
    def misc_check_io(self, value):
        self.BRmaster._SyncWriteRegisters(0x1182, value)

    @property
    def misc_telnet_pw(self):
        return self.BRmaster._SyncReadWord(0x1183)

    @misc_telnet_pw.setter
    def misc_telnet_pw(self, value):
        self.BRmaster._SyncWriteRegisters(0x1183, value)

    @property
    def misc_cfg_changed(self):
        return self.BRmaster._SyncReadWord(0x1184) == 0xC1

    @misc_cfg_changed.setter
    def misc_cfg_changed(self, value):
        self.BRmaster._SyncWriteRegisters(0x1184, 0xC1 if value else 0xC0)

    @property
    def misc_status(self):
        return self.BRmaster._SyncReadWord(0x1186)

    @property
    def misc_status_error(self):
        return self.BRmaster._SyncReadWord(0x1187)

    @property
    def x2x_cnt(self):
        return self.BRmaster._SyncReadWord(0x11C0)

    @property
    def x2x_bus_off(self):
        return self.BRmaster._SyncReadWord(0x11C1)

    @property
    def x2x_syn_err(self):
        return self.BRmaster._SyncReadWord(0x11C2)

    @property
    def x2x_syn_bus_timing(self):
        return self.BRmaster._SyncReadWord(0x11C3)

    @property
    def x2x_syn_frame_timing(self):
        return self.BRmaster._SyncReadWord(0x11C4)

    @property
    def x2x_syn_frame_crc(self):
        return self.BRmaster._SyncReadWord(0x11C5)

    @property
    def x2x_syn_frame_pending(self):
        return self.BRmaster._SyncReadWord(0x11C6)

    @property
    def x2x_syn_buffer_underrun(self):
        return self.BRmaster._SyncReadWord(0x11C7)

    @property
    def x2x_syn_buffer_overflow(self):
        return self.BRmaster._SyncReadWord(0x11C8)

    @property
    def x2x_asyn_err(self):
        return self.BRmaster._SyncReadWord(0x11C9)

    @property
    def x2x_asyn_bus_timing(self):
        return self.BRmaster._SyncReadWord(0x11CA)

    @property
    def x2x_asyn_frame_timing(self):
        return self.BRmaster._SyncReadWord(0x11CB)

    @property
    def x2x_asyn_frame_crc(self):
        return self.BRmaster._SyncReadWord(0x11CC)

    @property
    def x2x_asyn_frame_pending(self):
        return self.BRmaster._SyncReadWord(0x11CD)

    @property
    def x2x_asyn_buffer_underrun(self):
        return self.BRmaster._SyncReadWord(0x11CE)

    @property
    def x2x_asyn_buffer_overflow(self):
        return self.BRmaster._SyncReadWord(0x11CF)

    @property
    def ns_cnt(self):
        return self.BRmaster._SyncReadWord(0x1200)

    @property
    def ns_lost_cnt(self):
        return self.BRmaster._SyncReadWord(0x1201)

    @property
    def ns_oversize_cnt(self):
        return self.BRmaster._SyncReadWord(0x1202)

    @property
    def ns_crc_cnt(self):
        return self.BRmaster._SyncReadWord(0x1203)

    @property
    def ns_collision_cnt(self):
        return self.BRmaster._SyncReadWord(0x1206)
