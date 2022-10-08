# DSP Memory Server

In this section, I'm writing a simple application that runs on the DSP, 'communicates' with ARM and reads arbitrary DSP address according to ARM's request and return the value as result. This is my first attempt to write an 'application' on the DSP, using instruction bruteforcing technique introduced in `t32_insn_bruteforce`. Since we have zero documentation about how these mnemonic means, this humble attempt is going to verify my guesses. In T32 we could see the DSP uses separate program/data space, so I'm also going to see how they're mapped in this platform with this program.

## ARM-to-DSP access
Before we are going to run programs on DSP, there's a shortcut in our platform that allows us to access (partial, starting from 0x0) address space of DSP from ARM, by setting some registers, as documented [here](https://github.com/fxsheep/sprd-kernel-kyletd/blob/36b969d0fd0fcbd02fbc3b81a140b120f1a347e2/arch/arm/mach-sc8810/include/mach/globalregs.h#L502) and [here](https://github.com/fxsheep/sprd-kernel-kyletd/blob/36b969d0fd0fcbd02fbc3b81a140b120f1a347e2/arch/arm/mach-sc8810/include/mach/globalregs.h#L249):
```
devmem 0x20900204 32 0xdb00 # AHB_CTRL1_ARM_DAHB_SLEEP_EN = 0
devmem 0x20900284 32 0x5 # BIT_ASHB_ARMTODSP_EN_I = 1
```
Now we should be able to access DSP's 0x0 with this:
```
devmem 0x70000000
```

## DSP manipulation
Normally the DSP would run GSM low-level stack and IPCs with the modem OS on ARM, running in a paravirt machine. We need to stop the modem VM:
```
echo 2 > /proc/nk/stop
```
Alternatively, stop Android:
```
stop
```
Since the GSM modem part of DSP firmware entry is at 0x00020080(on ARM), we could load our code by overwriting it:
```
devmem 0x20080 32 0x3CA03CA0 # SQ.nop SQ.nop
```
Keep in mind that
 - 0x0 on ARM (DDR region) is mapped to 0xC0000000 in DSP code space, as we seen from rough disassembly of DSP FW in T32.
 - The bus endianness of ARM and DSP seems to be different. i.e. you'll need to reverse the endian manually before loading/getting code/data to/from DSP.

Now we could stop/reset(restart) the DSP by writing registers, as documented [here](https://github.com/fxsheep/sprd-kernel-kyletd/blob/36b969d0fd0fcbd02fbc3b81a140b120f1a347e2/arch/arm/mach-sc8810/include/mach/globalregs.h#L212).

Stop and reset DSP:
```
devmem 0x2090028C 32 0 #stop DSP
```
Restart DSP:
```
devmem 0x2090028C 32 1 #restart DSP
```

## DSP Application
To implement what we're expecting to do, we're going to need some basic instructions: some kind of 'MOV' that transfers data into registers, 'LOAD' that reads memory, 'STORE' that writes memory, and 'JUMP' that creates an infinite loop. Of course we also need to know some 32bit registers that allows general use. Luckily the T32 has given us information about all registers, the rX and gX seems to be general purpose 32bit, so I chose rX for convenience.

After a search I picked these, which looked friendly: (these namings doesn't differ too much from computer architectures we're familiar with)
```
0x0A00 SC.mov #0x0,r0 //move an immediate to a register, right?
0x0A21 SC.mov #0x4,r1 //well maybe
0x5001 LS0.ld{dw} (r0),r0 //load a dword from address specified in r0, to r0 itself, yes?
0x5001 LS0.ld{dw} (r0),r0
0x5411 LS0.st{dw} r0,(r1) //load a dword from r0 to address specified in r1
0x9ABFF81F SQ.brr{t} 0xFFFFFFE0 // Should be BRanch Relative, because I didn't find any other candidate that looks like do that?
//dunno what {t} means though...
```

To make it simpler, I'll use this simplest 'IPC' mechanism:
```
[0x0] = src addr
[0x4] = val
```
The DSP continuously reads an address specified by a dword at 0x0, read its value from DSP data space, then stores it at 0x4. On ARM side, we just need to write the address we are interested in to 0x70000000 and get result from 0x70000004.

After some struggling I finally figured out this:
```
devmem 0x2090028C 32 0 #stop DSP
devmem 0x20080 32 0x0A000A21 # SC.mov #0x0,r0  SC.mov #0x4,r1 //r0 = 0x0, r1 = 0x4
devmem 0x20084 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20088 32 0x50013CA0 # LS0.ld{dw} (r0),r0  SQ.nop //r0 is now loaded with address desired to read
devmem 0x2008C 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20090 32 0x50013CA0 # LS0.ld{dw} (r0),r0  SQ.nop //r0 is now loaded with value we read
devmem 0x20094 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20098 32 0x54113CA0 # LS0.st{dw} r0,(r1)  SQ.nop //value in r0 is stored to memory at 0x4
devmem 0x2009C 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x200A0 32 0x9ABFF81F # SQ.brr{t} 0xFFFFFFE0 (-0x20, to 0x20080) //loop
devmem 0x2090028C 32 1 #restart DSP
```

We could now:
 - write the address you wanna read by DSP: `devmem 0x70000000 32 0xc0020080`
 - read result (dword value of this address): `devmem 0x70000004`

And it works! After letting DSP read 0xC0020080, it immediately returned `0x0A000A21`, which is the value of our program's first dword - this also proved the assumption that our platform is using combined DSP prog/data address space is (probably) correct.

## Why so many NOPs
It's after some trial-and-failure did I realize that this DSP is indeed VLIW, where instruction synchornization isn't taken care by hardware at all, but should be taken care by compiler, via manual NOPs stuffing. Otherwise, the results could be messed up(i.e. an instruction being executed expects result from a former instruction that hasn't completed).
