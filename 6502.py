import collections
import operator

Instruction = collections.namedtuple('Instruction', ['optype', 'addressing_mode', 'operand', 'byte_size'])

# map of opcode to tuple of type, addressing_mode, and byte_size
OPCODE_TABLE = {
    0xEA: ("NOP", None, 1),
    0x20: ("JSR", None, 3),

    # stack instructions
    0x48: ("PHA", None, 1),
    0x68: ("PLA", None, 1),

    # flow control
    0x4C: ("JMP", "abs", 3),
    0x6C: ("JMP", "ind", 3),

    0xC9: ("CMP", "immediate", 2),
    0xC5: ("CMP", "zpg", 2),
    0xD5: ("CMP", "zpgx", 2),
    0xCD: ("CMP", "abs", 3),
    0xDD: ("CMP", "absx", 3),
    0xD9: ("CMP", "absy", 3),
    0xC1: ("CMP", "indx", 2),
    0xD1: ("CMP", "indy", 2),

    # loading memory
    0xA2: ("LDX", "immediate", 2),
    0xA6: ("LDX", "zpg", 2),
    0xB6: ("LDX", "zpgy", 2),
    0xAE: ("LDX", "abs", 3),
    0xBE: ("LDX", "absy", 3),

    0xA0: ("LDY", "immediate", 2),
    0xA4: ("LDY", "zpg", 2),
    0xB4: ("LDY", "zpgx", 2),
    0xAC: ("LDY", "abs", 3),
    0xBC: ("LDY", "absx", 3),

    0xA9: ("LDA", "immediate", 2),
    0xA5: ("LDA", "zpg", 2),
    0xB5: ("LDA", "zpgx", 2),
    0xAD: ("LDA", "abs", 3),
    0xBD: ("LDA", "absx", 3),
    0xB9: ("LDA", "absy", 3),
    0xA1: ("LDA", "indx", 2),
    0xB1: ("LDA", "indy", 2),

    # storing memory
    0x86: ("STX", "zpg", 2),
    0x96: ("STX", "zpgy", 2),
    0x8E: ("STX", "abs", 3),

    0x84: ("STY", "zpg", 2),
    0x94: ("STY", "zpgx", 2),
    0x8C: ("STY", "abs", 3),

    0x85: ("STA", "zpg", 2),
    0x95: ("STA", "zpgx", 2),
    0x8D: ("STA", "abs", 3),
    0x9D: ("STA", "absx", 3),
    0x99: ("STA", "absy", 3),
    0x81: ("STA", "indx", 2),
    0x91: ("STA", "indy", 2),

    # transfers
    0xAA: ("TAX", None, 1),
    0x8A: ("TXA", None, 1),
    0xCA: ("DEX", None, 1),
    0xE8: ("INX", None, 1),
    0xA8: ("TAY", None, 1),
    0x98: ("TYA", None, 1),
    0x88: ("DEY", None, 1),
    0xC8: ("INY", None, 1),

}

def as_int(bs):
    return int.from_bytes(bs, 'little', signed=False)


def read_as_address(mem, addr):
    # read the value from offset addr, addr + 1
    # and interpret the result as a 16bit addr
    bs = mem[addr:addr+2]
    return as_int(bs)


def read_instruction(mem, addr):
    opcode = mem[addr]

    # TODO: handle invalid opcodes
    optype, addressing_mode, byte_size = OPCODE_TABLE[opcode]

    # check if we need to read additional bytes for the operand
    operand_bytes = None
    if byte_size > 1:
        operand_bytes = mem[addr+1:addr+byte_size]
    return Instruction(optype, addressing_mode, operand_bytes, byte_size)

class CPU:
    def __init__(self, memory):
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0
        self.pc = 0
        self.flags = {
            'N': False,
            'V': False,
            'B': False,
            'D': False,
            'I': False,
            'Z': False,
            'C': False
        }
        self.memory = memory

    def run(self):
        # stack starts by pointing at the last byte of the 01 page
        self.sp = 0x01FF
        # start by reading the address used to initalize the program counter
        self.pc = read_as_address(self.mem, 0xfffc)
        while True:
            self.step()

    def step(self):
        instruction = read_instruction(mem, self.pc)
        self.evaluate(instruction)

        # we shouldn't increment the program counter after a jump instruction
        if instruction.optype == "JMP":
            continue
        else:
            self.pc += instruction.byte_size

    def evaluate(self, instruction):
        method = operator.attrgetter(instruction.optype)(self)
        method(instruction)


    # return the address refrenced by the operand and the addressing mode
    def resolve_address(self, instruction):
        val = as_int(instruction.operand)
        match instruction.addressing_mode:
            case "zpg":
                return val
            case "zpgx"
                return val + self.x % 256
            case "zpgy"
                return val + self.y % 256
            case "abs":
                return val
            case "absx":
                return val + self.x
            case "absy":
                return val + self.y
            case "indx":
                return read_as_address(self.mem, val + self.x)
            case "indy":
                return read_as_address(self.mem, val) + self.y


    # OP Implementations
    def NOP(self, _):
        pass

    def TAX(self, _):
        self.x = self.a

    def TXA(self, _):
        self.a = self.x

    def DEX(self, _):
        self.x = (self.x - 1) % 256
        # TODO flags?

    def INX(self, _):
        self.x = (self.x + 1) % 256

    def TAY(self, _):
        self.y = self.a

    def TYA(self, _):
        self.a = self.y

    def DEY(self, _):
        self.y = (self.y - 1) % 256

    def INY(self, _):
        self.y = (self.y + 1) % 256

    def PHA(self, _):
        self.memory[sp] = self.a
        self.sp -= 1

    def PLA(self, _):
        self.sp += 1
        self.a = self.memory[sp]

    def JMP(self, instruction):
        val = as_int(instruction.operand)
        match instruction.addressing_mode:
            case "abs":
                dest = val
            case "ind":
                # TODO: special case where the operand references the last byte of the page
                dest = read_as_address(self.mem, val)
        self.pc = dest

    def CMP(self, instruction):
        if instruction.mode == 'immediate':
            val = as_int(instruction.operand)
        else:
            addr = resolve_address(self, instruction)
            val = as_int(self.mem[addr])

        self.flags['C'] = self.a >= val
        self.flags['Z'] = self.a == val
        self.flags['N'] = self.a >= 0x80

    def LDA(self, instruction):
        if instruction.mode == 'immediate':
            val = as_int(instruction.operand)
        else:
            addr = resolve_address(self, instruction)
            val = as_int(self.mem[addr])

        self.a = val

    def STA(self, instruction):
        addr = resolve_address(self, instruction)
        self.mem[addr] = self.a


if __name__ == '__main__':
    mem = bytearray(2 ** 32)
    cpu = CPU(mem)
    cpu.run()