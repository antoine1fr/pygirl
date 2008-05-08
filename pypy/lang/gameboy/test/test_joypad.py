from pypy.lang.gameboy.joypad import *
from pypy.lang.gameboy.interrupt import *
from pypy.lang.gameboy import constants
import math

BUTTON_CODE = 0x3

def get_joypad():
    return Joypad(get_driver(), Interrupt())

def get_driver():
    return JoypadDriver()

def get_button():
    return Button(BUTTON_CODE)
    
def test_number_to_bool_bin():
    assert len(number_to_bool_bin(16, 1)) == 1
    assert len(number_to_bool_bin(1, 16)) == 16
    for i in range(0, 20):
        number = 0
        binNumber = number_to_bool_bin(i)
        size = len(binNumber)
        str = ""
        for j in range(0, size):
            if binNumber[j]:
                number += (1 << (size-j-1))
                str += ("1")
            else:
                str += ("0")
        assert number == i
    
def number_to_bool_bin(number, size=None):
    if size == None:
        if number == 0:
            return []
        size = int(math.ceil(math.log(number, 2)))+1
    bin = [False]*size
    for i in range(0, size):
        if (number & (1 << i)) != 0:
            bin[size-i-1] = True
    return bin

# TEST BUTTON ------------------------------------------------------------------

def test_ini():
    value = 0xf
    button = Button(value)
    assert button.oppositeButton == None
    assert button.codeValue == value
    assert button.is_pressed() == False
    
    button2 = Button(value, button)
    assert button2.oppositeButton == button
    assert button2.codeValue == value
    
def test_getCode():
    button = get_button()
    assert button.get_code() == 0
    button.press()
    assert button.get_code() == button.codeValue
    
def test_press_release():
    button = get_button()
    button2 = get_button()
    button.oppositeButton = button2;
    button2.press()
    assert button2.is_pressed() == True
    button.press()
    assert button.is_pressed() == True
    assert button2.is_pressed() == False
    button.release()
    assert button.is_pressed() == False
    assert button2.is_pressed() == False

# TEST JOYPAD DRIVER -----------------------------------------------------------

def test_ini():
    driver = get_driver()
    assert driver.raised == False
    assert driver.get_button_code() == 0
    assert driver.get_direction_code() == 0
    
def test_isRaised():
    driver = get_driver()
    driver.raised = True
    assert driver.raised == True
    assert driver.is_raised() == True
    assert driver.raised == False
    
def test_button_code_values():
    driver = get_driver()
    assert driver.up.codeValue == constants.BUTTON_UP 
    assert driver.right.codeValue == constants.BUTTON_RIGHT   
    assert driver.down.codeValue == constants.BUTTON_DOWN
    assert driver.left.codeValue == constants.BUTTON_LEFT
    assert driver.select.codeValue == constants.BUTTON_SELECT
    assert driver.start.codeValue == constants.BUTTON_START
    assert driver.a.codeValue == constants.BUTTON_A
    assert driver.b.codeValue == constants.BUTTON_B
    
    
def test_toggle_opposite_directions():
    driver = get_driver()
    directions = [(driver.button_up, driver.up, driver.down),
                 (driver.button_down, driver.down, driver.up),
                 (driver.button_left, driver.left, driver.right),
                 (driver.button_right, driver.right, driver.left)]
    for dir in directions:
        toggleFunction = dir[0]
        button = dir[1]
        oppositeButton = dir[2]
        driver.reset()
        
        oppositeButton.press()
        assert driver.raised == False
        assert button.is_pressed() == False
        assert oppositeButton.is_pressed() == True
        assert driver.get_direction_code() == oppositeButton.codeValue
        assert driver.get_button_code() == 0
        
        toggleFunction()
        assert driver.raised == True
        assert button.is_pressed() == True
        assert oppositeButton.is_pressed() == False
        assert driver.get_direction_code() == button.codeValue
        assert driver.get_button_code() == 0
        
        toggleFunction(False)
        assert button.is_pressed() == False
        assert oppositeButton.is_pressed() == False
        assert driver.get_direction_code() == 0
        assert driver.get_button_code() == 0
    
    
def test_toggle_buttons():
    driver = get_driver()
    buttons = [(driver.button_select, driver.select),
                 (driver.button_start, driver.start),
                 (driver.button_a, driver.a),
                 (driver.button_b, driver.b)]
    for button in buttons:
        toggleFunction = button[0]
        button = button[1]
        driver.reset()
        
        assert button.is_pressed() == False
        assert driver.get_button_code() == 0
        assert driver.get_direction_code() == 0
        
        toggleFunction()
        assert driver.raised == True
        assert button.is_pressed() == True
        assert driver.get_button_code() == button.codeValue
        assert driver.get_direction_code() == 0
        
        toggleFunction(False)
        assert button.is_pressed() == False
        assert driver.get_button_code() == 0
        assert driver.get_direction_code() == 0
        
        
def test_toggle_multiple_buttons():
    driver = get_driver()
    buttons = [(driver.button_select, driver.select),
                 (driver.button_start, driver.start),
                 (driver.button_a, driver.a),
                 (driver.button_b, driver.b)]
    toggle_multiple_test(driver, driver.get_button_code, buttons)
    
def test_toggle_mutliple_directions():
    """ 
    only testing non-opposite buttons, since they would exclude each other
    """
    driver = get_driver()
    directions = [(driver.button_up, driver.up),
                 #(driver.button_down, driver.down),
                 #(driver.button_left, driver.left),
                 (driver.button_right, driver.right)]
    toggle_multiple_test(driver, driver.get_direction_code, directions)
    
def toggle_multiple_test(driver, codeGetter, buttons):
    size = len(buttons)
    for i in range(0, 2**size):
        toggled = number_to_bool_bin(i, size)
        code = 0
        for j in range(0, size):
            if toggled[j]:
                buttons[j][0]()
                code |= buttons[j][1].codeValue
            else:
                buttons[j][0](False)
            assert buttons[j][1].is_pressed() == toggled[j]
        assert codeGetter() == code
                


# TEST JOYPAD ------------------------------------------------------------------

def test_reset(joypad=None):
    if joypad == None:
        joypad = get_joypad()
    assert joypad.joyp == 0xF
    assert joypad.cycles == constants.JOYPAD_CLOCK
        
def test_emulate():
    joypad = get_joypad()
    ticks = 2
    cycles = joypad.cycles
    joypad.emulate(ticks)
    assert cycles - joypad.cycles == ticks

def test_emulate_zero_ticks():
    joypad = get_joypad()
    joypad.cycles = 2
    ticks = 2
    joypad.emulate(ticks)
    assert joypad.cycles == constants.JOYPAD_CLOCK
    
def test_emulate_zero_ticks_update():   
    joypad = get_joypad() 
    value = 0x1
    joypad.joyp = value
    joypad.driver.buttonCode = 0x4
    joypad.driver.raised = True
    joypad.cycles = 2
    ticks = 2
    joypad.emulate(ticks)
    assert joypad.cycles == constants.JOYPAD_CLOCK
    assert joypad.joyp == value
    assert joypad.buttonCode == 0
    
def test_read_write():
    joypad = get_joypad()
    value = 0x2
    joypad.write(constants.JOYP, value)
    joyp = 0xC + (value & 0x3)
    assert joypad.joyp == joyp
    joyp = (joyp << 4) + 0xF
    assert joypad.read(constants.JOYP) == joyp
    assert joypad.read(constants.JOYP+1) == 0xFF
    # no change on writing the wrong address
    joypad.write(constants.JOYP+1, value+1)
    assert joypad.read(constants.JOYP) == joyp
    
    
def test_update():
    joypad = get_joypad()
    joypad.driver.button_select()
    assert joypad.driver.get_button_code() == constants.BUTTON_SELECT
    joypad.driver.button_up()
    assert joypad.driver.get_direction_code() == constants.BUTTON_UP
    assert joypad.buttonCode == 0xF
    joypad.joyp = 0x1
    joypad.update()
    assert joypad.buttonCode == (constants.BUTTON_SELECT | constants.BUTTON_UP)
    
    joypad.joyp = 0x2
    joypad.update()
    assert joypad.buttonCode == (constants.BUTTON_SELECT | constants.BUTTON_UP)
    
    joypad.joyp = 0x3
    joypad.update()
    assert joypad.buttonCode == 0xF
    
    
    