import unittest

from . import six502

class TestAddressingModes(unittest.TestCase):
    def setUp(self):
        self.addr = 11337
        self.memory = bytearray(2**16)
        self.memory[self.addr] = 42
        self.cpu = six502.CPU(self.memory)

    def test_abs(self):
        instruction = six502.Instruction('LDA', 'abs', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, self.addr)

    def test_absx(self):
        self.cpu.x = 7
        instruction = six502.Instruction('LDA', 'absx', (self.addr-7).to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, self.addr)

    def test_indirect_no_x(self):
        self.cpu.x = 0
        self.memory[self.addr+1] = 57
        instruction = six502.Instruction('LDA', 'indx', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, int.from_bytes(bytes([42, 57]), 'little'))

    def test_indirect_with_x(self):
        self.memory[self.addr + 3] = 99
        self.memory[self.addr + 4] = 66

        self.cpu.x = 3
        instruction = six502.Instruction('LDA', 'indx', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, int.from_bytes(bytes([99, 66]), 'little'))

    def test_indirect_with_y(self):
        self.memory[self.addr+1] = 57

        self.cpu.y = 20
        instruction = six502.Instruction('LDA', 'indy', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(
            result,
            int.from_bytes(bytes([42, 57]), 'little') + 20
        )
