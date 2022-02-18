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

    def test_indirect_x_doesnt_carry(self):
        self.memory[0x0300] = 99
        self.memory[0x0301] = 99

        self.memory[0x0200] = 66
        self.memory[0x0201] = 66

        self.cpu.x = 1
        # if this addressing mode used carry we would expect it to use the address stored in 0x0300
        # since the addition with x is done without carry it will instead use the address stored in 0x0200
        operand_addr = 0x02FF
        instruction = six502.Instruction('LDA', 'indx', operand_addr.to_bytes(2, 'little'), 3)

        result = self.cpu.resolve_address(instruction)
        self.assertEqual(result, int.from_bytes(bytes([66, 66]), 'little'))


    def test_indirect_with_y(self):
        self.memory[self.addr+1] = 57

        self.cpu.y = 20
        instruction = six502.Instruction('LDA', 'indy', self.addr.to_bytes(2, 'little'), 3)
        result = self.cpu.resolve_address(instruction)
        self.assertEqual(
            result,
            int.from_bytes(bytes([42, 57]), 'little') + 20
        )

class TestSubRoutine(unittest.TestCase):
    def setUp(self):
        self.addr = 11337
        self.memory = bytearray(2**16)
        self.memory[self.addr] = 42
        self.cpu = six502.CPU(self.memory)
        self.cpu.pc = 25

    def test_JSR(self):
        self.assertEqual(self.cpu.pc, 25)
        self.assertEqual(self.cpu.sp, 0x01FF)

        instruction = six502.Instruction('JSR', 'abs', self.addr.to_bytes(2, 'little'), 3)
        self.cpu.evaluate(instruction)

        self.assertEqual(self.cpu.pc, self.addr)
        self.assertEqual(self.cpu.sp, 0x01FF - 2)


    def test_RTS(self):
        self.assertEqual(self.cpu.pc, 25)
        self.assertEqual(self.cpu.sp, 0x01FF)

        # write the jsr instruction into memory
        dest_addr_bytes = self.addr.to_bytes(2, 'little')
        self.memory[self.cpu.pc] = 0x20
        self.memory[self.cpu.pc+1] = dest_addr_bytes[0]
        self.memory[self.cpu.pc+2] = dest_addr_bytes[1]

        # perform the jsr
        self.cpu.step()

        self.assertEqual(self.cpu.pc, self.addr)
        self.assertEqual(self.cpu.sp, 0x01FF - 2)

        # Now trigger the rts
        rts = six502.Instruction('RTS', None, None, 1)
        self.cpu.evaluate(rts)

        # the original value of the program counter + 3 bytes from the jsr instruction
        self.assertEqual(self.cpu.pc, 28)
        self.assertEqual(self.cpu.sp, 0x01FF) # back to the original value
