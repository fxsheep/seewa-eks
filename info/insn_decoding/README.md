# DSP instruction encoding 
Discovering how instructions are encoded is fundamental to building a disassembler/assembler for the architecture. Unluckily, there's no information about this other than the huge lookup table we've created in [`t32_insn_bruteforce`](https://github.com/fxsheep/seewa-eks/tree/main/info/t32_insn_bruteforce), so we'll have to manually discover encodings from it.

## Instruction class
After a brief comparison in `insn_16.txt`, it turns out that the encoding is a mess.
I've tried 4 and 5 leading bits as instruction opcode field, neither worked - opcode determination seems to be split into multiple parts, there's 4 leading bits deciding (roughly) the 'class' of instruction, i.e. which particular execution unit this insn for, then the specific op is decided by latter fields, and they're different per class.
 - Leading 4bit field -> instruction class
```
0000 SC
0001 A.S
0010 A.L
0011 SQ
0x3DXX sequencer: VLIW slots combining?
0100 LS0
0101 LS0
0110 M0
0111 M0
1000 LS0
1001 LS0
1010 LS1
1011 LS1
1100 LS0 || SC
0xC800 A.M0 || SC
0cCA00 A.M1 || SC
0xCC00 A.S || SC
0xCE00 A.L || SC

1101 LS0 + (SC?)
1110 LS1 || SC
1111 LS1 || SC

```
