from ctypes import *
from binascii import hexlify
import re
import py
from support import BaseCTypesTestChecker

def dump(obj):
    # helper function to dump memory contents in hex, with a hyphen
    # between the bytes.
    # cast it to the raw buffer
    try:
        import _rawffi
    except ImportError:
        h = hexlify(buffer(obj))
    else:
        size = sizeof(obj)
        a = _rawffi.Array('c').fromaddress(obj._buffer.buffer, size)
        h = hexlify([a[i] for i in range(len(a))])
    return re.sub(r"(..)", r"\1-", h)[:-1]

class Value(Structure):
    _fields_ = [("val", c_byte)]

class Container(Structure):
    _fields_ = [("pvalues", POINTER(Value))]

class TestOne(BaseCTypesTestChecker):
    def test(self):
        # create an array of 4 values
        val_array = (Value * 4)()

        # create a container, which holds a pointer to the pvalues array.
        c = Container()
        c.pvalues = val_array

        # memory contains 4 NUL bytes now, that's correct
        assert "00-00-00-00" == dump(val_array)

        # set the values of the array through the pointer:
        for i in range(4):
            c.pvalues[i].val = i + 1

        values = [c.pvalues[i].val for i in range(4)]

        # These are the expected results: here s the bug!
        assert (
            (values, dump(val_array))) == (
            ([1, 2, 3, 4], "01-02-03-04")
        )

    def test_2(self):

        val_array = (Value * 4)()

        # memory contains 4 NUL bytes now, that's correct
        assert "00-00-00-00" == dump(val_array)

        ptr = cast(val_array, POINTER(Value))
        # set the values of the array through the pointer:
        for i in range(4):
            ptr[i].val = i + 1

        values = [ptr[i].val for i in range(4)]

        # These are the expected results: here s the bug!
        assert (
            (values, dump(val_array))) == (
            ([1, 2, 3, 4], "01-02-03-04")
        )
