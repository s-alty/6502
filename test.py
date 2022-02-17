import unittest

from . import six502

class TestAddressingModes(unittest.TestCase):
    def setUp(self):
        self.addr = 11337
        self.memory = bytearray(2**32)
        self.memory[self.addr] = 42
        self.cpu = six502.CPU(self.memory)

    def test_abs(self):
        instruction = six502.Instruction('LDA', 'abs', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, self.addr)
