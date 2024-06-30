class Decoder:
    @staticmethod
    def decode_I_type(instruction):
        instruction_subtype = Instruction_parser.get_subtype__funct3(instruction)
        destination_reg     = Instruction_parser.get_destination_register__rd(instruction)
        source_reg          = Instruction_parser.get_source_register__rs1(instruction)
        immediate_val       = Instruction_parser.get_hardcoded_number__immediate_i(instruction)

        return instruction_subtype, destination_reg, source_reg, immediate_val

    @staticmethod
    def decode_J_type(instruction):
        destination_reg = Instruction_parser.get_destination_register__rd(instruction)
        immediate_val   = Instruction_parser.get_hardcoded_number__immediate_j(instruction)

        return destination_reg, immediate_val

    @staticmethod
    def decode_U_type(instruction):
        destination_reg = Instruction_parser.get_destination_register__rd(instruction)
        immediate_val   = Instruction_parser.get_hardcoded_number__immediate_u(instruction)

        return destination_reg, immediate_val

    @staticmethod
    def decode_B_type(instruction):
        instruction_subtype = Instruction_parser.get_subtype__funct3(instruction)
        source_reg_1        = Instruction_parser.get_source_register__rs1(instruction)
        source_reg_2        = Instruction_parser.get_source_register__rs2(instruction)
        immediate_val       = Instruction_parser.get_hardcoded_number__immediate_b(instruction)

        return instruction_subtype, source_reg_1, source_reg_2, immediate_val

    @staticmethod
    def decode_S_type(instruction):
        instruction_subtype = Instruction_parser.get_subtype__funct3(instruction)
        source_reg_1        = Instruction_parser.get_source_register__rs1(instruction)
        source_reg_2        = Instruction_parser.get_source_register__rs2(instruction)
        immediate_val       = Instruction_parser.get_hardcoded_number__immediate_s(instruction)

        return instruction_subtype, source_reg_1, source_reg_2, immediate_val

    @staticmethod
    def decode_R_type(instruction):
        instruction_subtype_f3 = Instruction_parser.get_subtype__funct3(instruction)
        instruction_subtype_f7 = Instruction_parser.get_subtype__funct7(instruction)
        source_reg_1        = Instruction_parser.get_source_register__rs1(instruction)
        source_reg_2        = Instruction_parser.get_source_register__rs2(instruction)
        destination_reg     = Instruction_parser.get_destination_register__rd(instruction)

        return instruction_subtype_f3, instruction_subtype_f7, source_reg_1, source_reg_2, destination_reg

    @staticmethod
    def decode_R_type_atomic(instruction):
        instruction_subtype_f3 = Instruction_parser.get_subtype__funct3(instruction)
        instruction_subtype_f5 = Instruction_parser.get_subtype__funct5(instruction)
        source_reg_1        = Instruction_parser.get_source_register__rs1(instruction)
        source_reg_2        = Instruction_parser.get_source_register__rs2(instruction)
        destination_reg     = Instruction_parser.get_destination_register__rd(instruction)
        return instruction_subtype_f3, instruction_subtype_f5, source_reg_1, source_reg_2, destination_reg

    @staticmethod
    def get_subtype__funct3(instruction):
        val = instruction & 0b00000000000000000111000000000000
        val = val >> 12
        return val

    @staticmethod
    def get_subtype__funct5(instruction):
        val = instruction >> 27
        return val

    @staticmethod
    def get_subtype__funct7(instruction):
        val = instruction >> 25
        return val

    @staticmethod
    def get_source_register__rs1(instruction):
        val = instruction & 0b00000000000011111000000000000000
        return val >> 15

    @staticmethod
    def get_source_register__rs2(instruction):
        val = instruction & 0b00000001111100000000000000000000
        return val >> 20

    @staticmethod
    def get_destination_register__rd(instruction):
        val = instruction & 0b00000000000000000000111110000000
        val = val >> 7
        return val

    @staticmethod
    def get_hardcoded_number__immediate_i(instruction):
        val = instruction >> 20
        return val

    @staticmethod
    def get_hardcoded_number__immediate_u(instruction):
        val = instruction >> 12
        return val

    @staticmethod
    def get_hardcoded_number__immediate_j(instruction):
        instruction_bits_31_31 = instruction & 0b10000000000000000000000000000000
        instruction_bits_30_21 = instruction & 0b01111111111000000000000000000000
        instruction_bits_20_20 = instruction & 0b00000000000100000000000000000000
        instruction_bits_19_12 = instruction & 0b00000000000011111111000000000000

        immediate_bits_20_20 = instruction_bits_31_31 >> 11
        immediate_bits_19_12 = instruction_bits_19_12
        immediate_bits_11_11 = instruction_bits_20_20 >> 9
        immediate_bits_10_01 = instruction_bits_30_21 >> 20
        immediate_bits_00_00 = 0

        val = immediate_bits_20_20 | immediate_bits_19_12 | immediate_bits_11_11 | immediate_bits_10_01 | immediate_bits_00_00

        return val

    @staticmethod
    def get_hardcoded_number__immediate_b(instruction):
        instruction_bits_31_31 = instruction & 0b10000000000000000000000000000000
        instruction_bits_30_25 = instruction & 0b01111110000000000000000000000000
        instruction_bits_11_08 = instruction & 0b00000000000000000000111100000000
        instruction_bits_07_07 = instruction & 0b00000000000000000000000010000000

        immediate_bits_12_12 = instruction_bits_31_31 >> 19
        immediate_bits_11_11 = instruction_bits_07_07 << 4
        immediate_bits_10_05 = instruction_bits_30_25 >> 20
        immediate_bits_04_01 = instruction_bits_11_08 >> 7
        immediate_bits_00_00 = 0

        val = immediate_bits_12_12 | immediate_bits_11_11 | immediate_bits_10_05 | immediate_bits_04_01 | immediate_bits_00_00

        return val

    @staticmethod
    def get_hardcoded_number__immediate_s(instruction):
        instruction_bits_31_25 = instruction & 0b11111110000000000000000000000000
        instruction_bits_11_07 = instruction & 0b00000000000000000000111110000000

        immediate_bits_11_05 = instruction_bits_31_25 >> 20
        immediate_bits_04_00 = instruction_bits_11_07 >> 7

        val = immediate_bits_11_05 | immediate_bits_04_00

        return val
