# constants.CATRIGE constants.TYPES
# ___________________________________________________________________________

from pypy.lang.gameboy import constants
import os

def has_cartridge_battery(self, cartridgeType):    
    return (cartridgeType == constants.TYPE_MBC1_RAM_BATTERY \
                or cartridgeType == constants.TYPE_MBC2_BATTERY \
                or cartridgeType == constants.TYPE_MBC3_RTC_BATTERY \
                or cartridgeType == constants.TYPE_MBC3_RTC_RAM_BATTERY \
                or cartridgeType == constants.TYPE_MBC3_RAM_BATTERY \
                or cartridgeType == constants.TYPE_MBC5_RAM_BATTERY \
                or cartridgeType == constants.TYPE_MBC5_RUMBLE_RAM_BATTERY \
                or cartridgeType == constants.TYPE_HUC1_RAM_BATTERY)


def create_bank_controller(self, cartridgeType, rom, ram, clock):
        if constants.CATRIDGE_TYPE_MAPPING.has_key(cartridgeType) :
            return constants.CATRIDGE_TYPE_MAPPING[cartridgeType](rom, ram, clock)
        else:
            raise InvalidMemoryBankTypeError("Unsupported memory bank controller (0x"+hex(cartridgeType)+")")

class InvalidMemoryBankTypeError(Exception):
    pass



# ==============================================================================
# CARTRIDGE

class CartridgeManager(object):
    
    def __init__(self, clockDriver):
        self.clock = clockDriver
        self.cartridge = None
        
    def reset(self):
        if not self.has_battery():
            self.ram[0:len(self.ram):1] = 0xFF
        self.mbc.reset()

    def read(self, address):
        return self.mbc.read(address)
    
    def write(self, address, data):
        self.mbc.write(address, data)
    
    def load(self, cartridge):
        self.cartridge = cartridge
        self.rom  = self.cartridge.read()
        self.check_rom()
        self.create_ram()
        self.load_battery()
        self.mbc = self.create_bank_controller(self.get_memory_bank_type(), self.rom, self.ram, self.clock)
        
    def check_rom(self):
        if not self.verify_header():
            raise Exeption("Cartridge header is corrupted")
        if self.cartridge.get_size() < self.get_rom_size():
            raise Exeption("Cartridge is truncated")
        
    def create_ram(self):
        ramSize = self.get_ram_size()
        if self.get_memory_bank_type() >= constants.TYPE_MBC2 \
                and self.get_memory_bank_type() <= constants.TYPE_MBC2_BATTERY:
            ramSize = 512
        self.ram = [0xFF]*ramSize
        
    def load_battery(self):
        if self.cartridge.has_battery():
            self.ram = self.cartridge.read_battery()

    def save(self, cartridgeName):
        if self.cartridge.has_battery():
            self.cartridge.write_battery(self.ram)
            
    def get_memory_bank_type(self):
        return self.rom[constants.CARTRIDGE_TYPE_ADDRESS] & 0xFF
    
    def get_memory_bank(self):
        return self.mbc

    def get_rom(self):
        return self.rom
        
    def get_rom_size(self):
        romSize = self.rom[constants.CARTRIDGE_ROM_SIZE_ADDRESS] & 0xFF
        if romSize>=0x00 and romSize<=0x07:
            return 32768 << romSize
        return -1
        
    def get_ram_size(self):
        return constants.CARTRIDGE_RAM_SIZE_MAPPING[self.rom[constants.CARTRIDGE_RAM_SIZE_ADDRESS]]
    
    def get_destination_code(self):
        return self.rom[constants.DESTINATION_CODE_ADDRESS] & 0xFF
    
    def get_licensee_code():
        return self.rom[constants.LICENSEE_ADDRESS] & 0xFF

    def get_rom_version(self):
        return self.rom[constants.CARTRIDGE_ROM_VERSION_ADDRESS] & 0xFF
    
    def get_header_checksum(self):
        return self.rom[constants.HEADER_CHECKSUM_ADDRESS] & 0xFF
    
    def get_checksum(self):
        return ((self.rom[constants.CHECKSUM_A_ADDRESS] & 0xFF) << 8) \
                + (self.rom[constants.CHECKSUM_B_ADDRESS] & 0xFF)
    
    def has_battery(self):
        return has_cartridge_battery(self.getMemoryBankType())
    
    def verify(self):
        checksum = 0
        for address in range(len(self.rom)):
            if address is not 0x014E and address is not 0x014F:
                checksum = (checksum + (self.rom[address] & 0xFF)) & 0xFFFF
        return (checksum == self.get_checksum())
    
    def verify_header(self):
        if len(self.rom) < 0x0150:
            return False
        checksum = 0xE7
        for address in range(0x0134, 0x014C):
            checksum = (checksum - (self.rom[address] & 0xFF)) & 0xFF
        return (checksum == self.get_header_checksum())
    
    def create_bank_controller(self, type, rom, ram, clockDriver):
        return MEMORY_BANK_MAPPING[type](rom, ram, clockDriver)


# ------------------------------------------------------------------------------

    
class Cartridge(object):
    """
        File mapping. Holds the file contents
    """
    def __init__(self, file=None):
        self.reset()
        if file != None:
            self.load(file)
        
    def reset(self):
        self.cartridgeName =""
        self.cartridgeFilePath = ""
        self.cartridgeFile = None    
        self.batteryName =""
        self.batteryFilePath = ""
        self.batteryFile = None
        
        
    def load(self, cartridgeFilePath):
        self.cartridgeFilePath = cartridgeFilePath
        self.cartridgeName = os.path.basename(cartridgeFilePath)
        self.cartridgeFile = open(cartridgeFilePath)
        self._load_battery(cartridgeFilePath)
        
        
    def _load_battery(self, cartridgeFilePath):
        self.batteryFilePath = self._create_battery_file_path(cartridgeFilePath)
        self.batteryName = os.path.basename(self.batteryFilePath)
        if self.has_battery():
            self.batteryFile = open(self.batteryFilePath)
    
    def _create_battery_file_path(self, cartridgeFilePath):
        if cartridgeFilePath.endswith(constants.CARTRIDGE_FILE_EXTENSION):
            return cartridgeFilePath.replace(constants.CARTRIDGE_FILE_EXTENSION,
                    constants.BATTERY_FILE_EXTENSION)
        elif cartridgeFilePath.endswith(constants.CARTRIDGE_COLOR_FILE_EXTENSION):
            return cartridgeFilePath.replace(constants.CARTRIDGE_COLOR_FILE_EXTENSION,
                    constants.BATTERY_FILE_EXTENSION)
        else:
            return cartridgeFilePath + constants.BATTERY_FILE_EXTENSION
    
    def has_battery(self):
        return os.path.exists(self.batteryFilePath)
    
    def read(self):
        self.cartridgeFile.seek(0)
        return map(map_to_byte, self.cartridgeFile.read())
    
    def read_battery(self):
        self.batteryFile.seek(0)
        return  map(map_to_byte, self.batteryFile.read())
    
    def write_battery(self, ram):
        self.batteryFile = open(self.batteryFilePath, "w")
        self.batteryFile.write(("").join(map(chr, ram)))
        self.batteryFile = open(self.batteryFilePath, "r+")
        
    def remove_battery(self):
        if self.has_battery():
            os.remove(self.batteryFilePath)
            
    def get_size(self):
        return os.path.getsize(self.cartridgeFilePath)
        
    def get_battery_size(self):
        return os.path.getsize(self.batteryFilePath)
        
     

def map_to_byte(value):
    return ord(value) & 0xFF
   
# ==============================================================================
# CARTRIDGE TYPES

class MBC(object):
    
    def __init__(self, rom, ram, clockDriver):
        self.set_rom(rom)
        self.set_ram(ram)

    def reset(self):
        self.romBank = constants.ROM_BANK_SIZE
        self.ramBank = 0
        self.ramEnable = False
        self.rom = []
        self.ram = []
        self.romSize = 0
        self.ramSize = 0
        self.minRomBankSize = 0
        self.maxRomBankSize = 0
        self.minRamBankSize = 0
        self.maxRamBankSize = 0
    
    def set_rom(self, buffer):
        banks = len(buffer) / constants.ROM_BANK_SIZE
        if banks < self.minRomBankSize or banks > self.maxRomBankSize:
            raise Exception("Invalid constants.ROM size")
        self.rom = buffer
        self.romSize = constants.ROM_BANK_SIZE*banks - 1


    def set_ram(self, buffer):
        banks = len(buffer) / constants.RAM_BANK_SIZE
        if banks < self.minRamBankSize or banks > self.maxRamBankSize:
            raise Exception("Invalid constants.RAM size")
        self.ram = buffer
        self.ramSize = constants.RAM_BANK_SIZE*banks - 1
        
        
    def read(self, address):    
        if address <= 0x3FFF: # 0000-3FFF
            return self.rom[address] & 0xFF
        elif address <= 0x7FFF:# 4000-7FFF
            print address, self.romBank
            return self.rom[self.romBank + (address & 0x3FFF)] & 0xFF
        elif address >= 0xA000 and address <= 0xBFFF and self.ramEnable: # A000-BFFF
                return self.ram[self.ramBank + (address & 0x1FFF)] & 0xFF
        return 0xFF
    
    def write(self, address, data):
        pass
  

#-------------------------------------------------------------------------------

  
class DefaultMBC(MBC):
    
    def __init__(self, rom, ram, clockDriver):
        self.reset()
        self.minRomBankSize = 0
        self.maxRomBankSize = 0xFFFFFF
        self.minRamBankSize = 0
        self.maxRamBankSize = 0xFFFFFF
        MBC.__init__(self, rom, ram, clockDriver)
    

#-------------------------------------------------------------------------------
  

class MBC1(MBC):
    """
    PyBoy GameBoy (TM) Emulator
    
    Memory Bank Controller 1 (2MB constants.ROM, 32KB constants.RAM)
     
    0000-3FFF    ROM Bank 0 (16KB)
    4000-7FFF    ROM Bank 1-127 (16KB)
    A000-BFFF    RAM Bank 0-3 (8KB)
     """
    def __init__(self, rom, ram, clockDriver):
        self.reset()
        self.minRamBankSize = 0
        self.maxRamBankSize = 4
        self.minRomBankSize = 2    
        self.maxRomBankSize = 128
        MBC.__init__(self, rom, ram, clockDriver)
        
    def reset(self):
        MBC.reset(self)
        self.memoryModel = 0

    def write(self, address, data):
        if address <= 0x1FFF:  # 0000-1FFF
            self.write_ram_enable(address, data)
        elif address <= 0x3FFF: # 2000-3FFF
            self.write_rom_bank_1(address, data)
        elif address <= 0x5FFF: # 4000-5FFF
            self.write_rom_bank_2(address, data)
        elif address <= 0x7FFF: # 6000-7FFF
            self.memoryModel = data & 0x01
        elif address >= 0xA000 and address <= 0xBFFF and self.ramEnable: # A000-BFFF
            self.ram[self.ramBank + (address & 0x1FFF)] = data

    def write_ram_enable(self, address, data):
        if self.ramSize > 0:
            self.ramEnable = ((data & 0x0A) == 0x0A)
    
    def write_rom_bank_1(self, address, data):
        if (data & 0x1F) == 0:
            data = 1
        if self.memoryModel == 0:
            self.romBank = ((self.romBank & 0x180000) + ((data & 0x1F) << 14)) & self.romSize
        else:
            self.romBank = ((data & 0x1F) << 14) & self.romSize
        
    def write_rom_bank_2(self, address, data):
        if self.memoryModel == 0:
            self.romBank = ((self.romBank & 0x07FFFF) + ((data & 0x03) << 19)) & self.romSize
        else:
            self.ramBank = ((data & 0x03) << 13) & self.ramSize
  

#-------------------------------------------------------------------------------

      
class MBC2(MBC):
    """
    PyBoy GameBoy (TM) Emulator
    
    Memory Bank Controller 2 (256KB constants.ROM, 512x4bit constants.RAM)
    
    0000-3FFF    ROM Bank 0 (16KB)
    4000-7FFF    ROM Bank 1-15 (16KB)
    A000-A1FF    RAM Bank (512x4bit)
     """
     
    RAM_BANK_SIZE = 512

    def __init__(self, rom, ram, clockDriver):
        self.reset()
        self.minRamBankSize = constants.RAM_BANK_SIZE
        self.maxRamBankSize = constants.RAM_BANK_SIZE
        self.minRomBankSize = 2    
        self.maxRomBankSize = 16
        MBC.__init__(self, rom, ram, clockDriver)
        

    def read(self, address):
        if address > 0xA1FF:
            return 0xFF
        else:
            return super.read(address)

    def write(self, address, data):
        if address <= 0x1FFF:  # 0000-1FFF
            self.write_ram_enable(address, data)
        elif address <= 0x3FFF: # 2000-3FFF
            self.write_rom_bank()
        elif address >= 0xA000 and address <= 0xA1FF: # A000-A1FF
            self.write_ram(address, data)
            
    def write_ram_enable(self, address, data):
        if (address & 0x0100) == 0:
            self.ramEnable = ((data & 0x0A) == 0x0A)
            
    def write_rom_bank(self, address):
        if (address & 0x0100) == 0:
            return
        if (data & 0x0F) == 0:
            data = 1
        self.romBank = ((data & 0x0F) << 14) & self.romSize
        
    def write_ram(self, address, data):
        if self.ramEnable:
            self.ram[address & 0x01FF] = data & 0x0F


#-------------------------------------------------------------------------------


class MBC3(MBC):
    """
    PyBoy GameBoy (TM) Emulator
    
    Memory Bank Controller 3 (2MB constants.ROM, 32KB constants.RAM, Real Time Clock)
    
    0000-3FFF    ROM Bank 0 (16KB)
    4000-7FFF    ROM Bank 1-127 (16KB)
    A000-BFFF    RAM Bank 0-3 (8KB)
    """
    def __init__(self, rom, ram, clock):
        self.reset()
        self.minRamBankSize = 0
        self.maxRamBankSize = 4
        self.minRomBankSize = 2    
        self.maxRomBankSize = 128
        
        self.clock = clock
        self.clockLDaysclockLControl = None

        MBC.__init__(self, rom, ram, clockDriver)
        self.reset()


    def reset(self):
        MBC.reset(self)
        self.clockTime = self.clock.getTime()
        self.clockLatch = self.clockRegister = 0
        self.clockSeconds = self.clockMinutes = self.clockHours = self.clockDays = self.clockControl = 0
        self.clockLSeconds = self.clockLMinutes = self.clockLHours = self.clockLDays = self.clockLControl = 0


    def read(self, address):
        if (address >= 0xA000 and address <= 0xBFFF):  # A000-BFFF
            if (self.ramBank >= 0):
                return self.ram[self.ramBank + (address & 0x1FFF)] & 0xFF
            else:
                return self.read_clock_data(address)
        else:
            return super.read(address)
        
    def read_clock_data(self, address):
        if self.clockRegister == 0x08:
            return self.clockLSeconds
        if self.clockRegister == 0x09:
            return self.clockLMinutes
        if self.clockRegister == 0x0A:
            return self.clockLHours
        if self.clockRegister == 0x0B:
            return self.clockLDays
        if self.clockRegister == 0x0C:
            return self.clockLControl
    
    def write(self, address, data):
        if address <= 0x1FFF: # 0000-1FFF
            self.write_ram_enable(address, data)
        elif address <= 0x3FFF: # 2000-3FFF
            self.write_rom_bank(address, data)
        elif address <= 0x5FFF:  # 4000-5FFF
            self.write_ram_bank(address, data)
        elif address <= 0x7FFF: # 6000-7FFF
            self.write_clock_latch(address, data)
        elif address >= 0xA000 and address <= 0xBFFF and self.ramEnable: # A000-BFFF
            self.write_clock_data(address, data)
    
    def write_ram_enable(self, address, data):
        if self.ramSize > 0:
            self.ramEnable = ((data & 0x0A) == 0x0A)
             
    def write_rom_bank(self, address, data):
        if data == 0:
            data = 1
        self.romBank = ((data & 0x7F) << 14) & self.romSize
            
    def write_ram_bank(self, address, data):
        if data >= 0x00 and data <= 0x03:
            self.ramBank = (data << 13) & self.ramSize
        else:
            self.ramBank = -1
            self.clockRegister = data
                
    def write_clock_latch(self, address, data):
        if self.clockLatch == 0 and data == 1:
            self.latchClock()
        if data == 0 or data == 1:
            self.clockLatch = data
            
    def write_clock_data(self, address, data):
        if self.ramBank >= 0:
            self.ram[self.ramBank + (address & 0x1FFF)] = data
        else:
            self.updateClock()
            if self.clockRegister == 0x08:
                self.clockSeconds = data
            if self.clockRegister == 0x09:
                self.clockMinutes = data
            if self.clockRegister == 0x0A:
                self.clockHours = data
            if self.clockRegister == 0x0B:
                self.clockDays = data
            if self.clockRegister == 0x0C:
                self.clockControl = (self.clockControl & 0x80) | data
        

    def latch_clock(self):
        self.updateClock()
        self.clockLSeconds = self.clockSeconds
        self.clockLMinutes = self.clockMinutes
        self.clockLHours = self.clockHours
        self.clockLDays = self.clockDays & 0xFF
        self.clockLControl = (self.clockControl & 0xFE) | ((self.clockDays >> 8) & 0x01)


    def update_clock():
        now = self.clock.get_time()
        if (self.clockControl & 0x40) == 0:
            elapsed = now - self.clockTime
            while elapsed >= 246060:
                elapsed -= 246060
                self.clockDays+=1
            while elapsed >= 6060:
                elapsed -= 6060
                self.clockHours+=1
            while elapsed >= 60:
                elapsed -= 60
                self.clockMinutes+=1
            self.clockSeconds += elapsed
            while self.clockSeconds >= 60:
                self.clockSeconds -= 60
                self.clockMinutes+=1
            while self.clockMinutes >= 60:
                self.clockMinutes -= 60
                self.clockHours+=1
            while self.clockHours >= 24:
                self.clockHours -= 24
                self.clockDays+=1
            while self.clockDays >= 512:
                self.clockDays -= 512
                self.clockControl |= 0x80
        self.clockTime = now


#-------------------------------------------------------------------------------


class MBC5(MBC):
    """
    PyBoy GameBoy (TM) Emulator
    
    Memory Bank Controller 5 (8MB constants.ROM, 128KB constants.RAM)
     *
    0000-3FFF    ROM Bank 0 (16KB)
    4000-7FFF    ROM Bank 1-511 (16KB)
    A000-BFFF    RAM Bank 0-15 (8KB)
    """
    def __init__(self, rom, ram, clockDriver, rumble):
        self.reset()
        self.minRamBankSize = 0
        self.maxRamBankSize = 16
        self.minRomBankSize = 2    
        self.maxRomBankSize = 512
        
        self.rumble = rumble
        MBC.__init__(self, rom, ram, clockDriver)


    def write(self, address, data):
        if address <= write_ram_enable:  # 0000-1FFF
            self.writeRAMEnable(address, data)
        elif address <= 0x2FFF:  # 2000-2FFF
            self.romBank = ((self.romBank & (0x01 << 22)) + ((data & 0xFF) << 14)) & self.romSize
        elif address <= 0x3FFF: # 3000-3FFF
            self.romBank = ((self.romBank & (0xFF << 14)) + ((data & 0x01) << 22)) & self.romSize
        elif address <= 0x4FFF:  # 4000-4FFF
            self.write_ram_bank(address, data)
        elif address >= 0xA000 and address <= 0xBFFF and self.ramEnable:  # A000-BFFF
            self.ram[self.ramBank + (address & 0x1FFF)] = data

    def write_ram_enable(self, address, data):
        if self.ramSize > 0:
            self.ramEnable = ((data & 0x0A) == 0x0A)
            
    def write_ram_bank(self, address, data):
        if self.rumble:
            self.ramBank = ((data & 0x07) << 13) & self.ramSize
        else:
            self.ramBank = ((data & 0x0F) << 13) & self.ramSize


#-------------------------------------------------------------------------------


class HuC1(MBC):
    def __init__(self, ram, rom, clockDriver):
        self.reset()
        MBC.__init__(self, rom, ram, clockDriver)



#-------------------------------------------------------------------------------



class HuC3(MBC):
    """
    PyBoy GameBoy (TM) Emulator
    
    Hudson Memory Bank Controller 3 (2MB constants.ROM, 128KB constants.RAM, constants.RTC)
    
    0000-3FFF    ROM Bank 0 (16KB)
    4000-7FFF    ROM Bank 1-127 (16KB)
    A000-BFFF    RAM Bank 0-15 (8KB)
    """
    def __init__(self, rom, ram, clock):
        self.reset()
        self.minRamBankSize = 0
        self.maxRamBankSize = 4
        self.minRomBankSize = 2    
        self.maxRomBankSize = 128
        self.clock = clock
        self.clockRegister = 0
        self.clockShift = 0
        self.clockTime = 0
        
        self.set_rom(rom)
        self.set_ram(ram)
        self.ramFlag = 0
        self.ramValue = 0
        MBC.__init__(self, rom, ram, clockDriver)


    def reset(self):
        MBC.reset(self)
        self.ramFlag = 0
        self.ramValue = 0
        self.clockRegister = 0
        self.clockShift = 0
        self.clockTime = self.clock.get_time()


    def read(self, address):
        if address >= 0xA000 and address <= 0xBFFF:# A000-BFFF
            if (self.ramFlag == 0x0C):
                return self.ramValue
            elif (self.ramFlag == 0x0D):
                return 0x01
            elif (self.ramFlag == 0x0A or self.ramFlag == 0x00):
                if (self.ramSize > 0):
                    return self.ram[self.ramBank + (address & 0x1FFF)] & 0xFF
        else:
            super.read(address)
    
    def write(self, address, data):
        if address <= 0x1FFF: # 0000-1FFF
            self.ramFlag = data
        elif address <= 0x3FFF:# 2000-3FFF
            self.writeROMBank(address, data)
        elif address <= 0x5FFF: # 4000-5FFF
            self.ramBank = ((data & 0x0F) << 13) & self.ramSize
        elif address >= 0xA000 and address <= 0xBFFF: # A000-BFFF
            self.writeRAMFlag(address, data)
         
    def write_rom_bank(self, address, data):
        if (data & 0x7F) == 0:
            data = 1
        self.romBank = ((data & 0x7F) << 14) & self.romSize
        
    def write_ram_flag(self, address, data):
        if self.ramFlag == 0x0B:
            self.writeWithRamFlag0x0B(address, data)
        elif (self.ramFlag >= 0x0C and self.ramFlag <= 0x0E):
            pass
        elif self.ramFlag == 0x0A and self.ramSize > 0:
            self.ram[self.ramBank + (address & 0x1FFF)] = data
                        
    def write_with_ram_flag_0x0B(self, address, data):
        if (data & 0xF0) == 0x10:
            self.write_ram_value_clock_shift(address, data)
        elif (data & 0xF0) == 0x30:
            self.write_clock_register_clock_shift(address, data)
        elif (data & 0xF0) == 0x40:
            self.write_clock_shift(address, data)
        elif (data & 0xF0) == 0x50:
            pass
        elif (data & 0xF0) == 0x60:
            self.ramValue = 0x01
         
    def write_ram_value_clock_shift(self, address, data):
        if self.clockShift > 24:
            return
        self.ramValue = (self.clockRegister >> self.clockShift) & 0x0F
        self.clockShift += 4
            
    def write_clock_register_clock_shift(self, address, data):
        if self.clockShift > 24:
            return
        self.clockRegister &= ~(0x0F << self.clockShift)
        self.clockRegister |= ((data & 0x0F) << self.clockShift)
        self.clockShift += 4
                    
    def write_clock_shift(self, address, data):
        switch = data & 0x0F
        self.updateClock()
        if switch == 0:
            self.clockShift = 0
        elif switch == 3:
            self.clockShift = 0
        elif switch == 7:
            self.clockShift = 0
            
    def update_clock(self):
        now = self.clock.getTime()
        elapsed = now - self.clockTime
        # years (4 bits)
        while elapsed >= 365246060:
            self.clockRegister += 1 << 24
            elapsed -= 365246060
        # days (12 bits)
        while elapsed >= 246060:
            self.clockRegister += 1 << 12
            elapsed -= 246060
        # minutes (12 bits)
        while elapsed >= 60:
            self.clockRegister += 1
            elapsed -= 60
        if (self.clockRegister & 0x0000FFF) >= 2460:
            self.clockRegister += (1 << 12) - 2460
        if (self.clockRegister & 0x0FFF000) >= (365 << 12):
            self.clockRegister += (1 << 24) - (365 << 12)
        self.clockTime = now - elapsed


# MEMORY BANK MAPPING ----------------------------------------------------------


MEMORY_BANK_TYPE_RANGES = [
    (constants.TYPE_MBC1,             constants.TYPE_MBC1_RAM_BATTERY,        MBC1),
    (constants.TYPE_MBC2,             constants.TYPE_MBC2_BATTERY,            MBC2),
    (constants.TYPE_MBC3_RTC_BATTERY, constants.TYPE_MBC3_RAM_BATTERY,        MBC3),
    (constants.TYPE_MBC5,             constants.TYPE_MBC5_RUMBLE_RAM_BATTERY, MBC5),
    (constants.TYPE_HUC3_RTC_RAM,     constants.TYPE_HUC3_RTC_RAM,            HuC3),
    (constants.TYPE_HUC1_RAM_BATTERY, constants.TYPE_HUC1_RAM_BATTERY,        HuC1)
]


def initialize_mapping_table():
    result = [DefaultMBC] * 256
    for entry in MEMORY_BANK_TYPE_RANGES:
        if len(entry) == 2:
            positions = [entry[0]]
        else:
            positions = range(entry[0], entry[1]+1)
        for pos in positions:
            result[pos] = entry[-1]
    return result

MEMORY_BANK_MAPPING = initialize_mapping_table()
