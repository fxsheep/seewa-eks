# DSP JTAG Exploration
The DSP core claims to support debugging/emulation through JTAG interface. This is an attempt to explore the DSP's JTAG interface.

## Platform-specific background: DSP SW-JTAG
According to Android kernel sources, the SoC has a [MMIO-based interface](https://github.com/fxsheep/sprd-kernel-kyletd/blob/sprdlinux3.0-kyletd/arch/arm/mach-sc8810/include/mach/globalregs.h#L494) that allows ARM subsystem to access DSP's JTAG. It looks straightforward, similar to GPIO bitbanging:
```
#define BIT_CEVA_SW_JTAG_ENA    ( BIT(8) )
#define BIT_STDO                ( BIT(4) )
#define BIT_STCK                ( BIT(3) )
#define BIT_STMS                ( BIT(2) )
#define BIT_STDI                ( BIT(1) )
#define BIT_STRTCK              ( BIT(0) )
```
By default the interface remains disabled (and probably muxed to the physical JTAG port):
```
# devmem 0x20900280
0x00000000
```
Enable it:
```
# devmem 0x20900280 32 0x100 
0x00000100
```
RTCK provides a feedback of TCK status from target, so what's written to TCK should reflect on RTCK:
```
# devmem 0x20900280 32 0x108
# devmem 0x20900280
0x00000109
```
Indeed, it works this way. Now we should be able to interact with DSP's JTAG interface by bitbanging through this register. (Note that there's a typo in their kernel source - the `BIT_STDI` is not writable so it's actually TDO, and `BIT_STDO` is writable so it's actually TDI.)  
After manually(yeah) navigating through the JTAG state machine by `devmem` like this:
```
T-L-R -> R-T-I
       0       1      0      0      0      0x8
       0       0      0      0      0      0x0
R-T-I -> S-D-S
       0       1      1      0      0      0xC
       0       0      1      0      0      0x4
S-D-S -> C-D-R
       0       1      0      0      0      0x8
       0       0      0      0      0      0x0
C-D-R -> S-D-R
       0       1      0      0      0      0x8
       0       0      0      0      0      0x0
S-D-R
       0       1      0      ?      0      0x8
       0       0      0      ?      0      0x0
```
I've got a 32bit IDCODE shifted out from TDO:
```
1 0 1 0 0 1 0 1 0 0 1 0 0 1 0 0 0 1 0 0 0 1 1 0 1 0 0 0 0 0 0 0
```
It's 0x016224A5! This matched the core's name. A brief search showed that no one has debugged the DSP publicly, may we be the first?(xD)

## JTAG interface peeking
In fact I didn't have much hope about the possibiity of JTAG - it's shift-register based, meaning that one can't avoid changing value of a data register when reading it. This is unlike a typical register mapped bus-like design, making it unsuitable for implementing debugging interface directly. So far most IP makers choose to implement an additional "protocol" (on a specific DR) that gives indirect access to debugging-related registers. Nevertheless, I tried to bruteforce all data registers (reading, and writing 0x0):
```
First try:
IR = 0, DR = 0
...
IR = 1f, DR = 0
IR = 20, DR = 1
IR = 21, DR = 0
IR = 22, DR = 0
IR = 23, DR = 0
IR = 24, DR = 1
IR = 25, DR = 0
...
IR = 33, DR = 0
IR = 34, DR = c00a87d8
IR = 35, DR = 0
...
IR = 5f, DR = 0
IR = 60, DR = 4a
IR = 61, DR = 0
...
IR = 6f, DR = 0
IR = 70, DR = ffffffff
IR = 71, DR = 0
IR = 72, DR = 16220401
IR = 73, DR = 0
...
IR = 87, DR = 0
IR = 88, DR = 1
IR = 89, DR = 0
IR = 8a, DR = 1
IR = 8b, DR = 1
IR = 8c, DR = 0
IR = 8d, DR = 0
IR = 8e, DR = 0
IR = 8f, DR = 0
IR = 90, DR = 0
IR = 91, DR = 0
IR = 92, DR = 30023
IR = 93, DR = 0
...
IR = 9f, DR = 0
IR = a0, DR = 16224a5
IR = a1, DR = 0
...
IR = ff, DR = 0
```
It turns out that we're quite lucky - although most DRs are zero, those many non-zero ones indicate that this debugging interface doesn't use additional abstractions, but provides debug register access directly! This also made me curious about how it workarounds the shift register problem - it's possible that they separated registers to read-only and write-only ones, or they just made every register's initial status determinable so the host debugger doesn't have to worry about unwanted overwriting of some controlling bits. To find out more I tried it again:
```
Second try:
IR = 0, DR = 0
...
IR = 1f, DR = 0
IR = 20, DR = 1
IR = 21, DR = 0
IR = 22, DR = 0
IR = 23, DR = 0
IR = 24, DR = 1
IR = 25, DR = 0
...
IR = 33, DR = 0
IR = 34, DR = c00a65ac
IR = 35, DR = 0
...
IR = 5f, DR = 0
IR = 60, DR = 68
IR = 61, DR = 0
...
IR = 6f, DR = 0
IR = 70, DR = ffffffff
IR = 71, DR = 0
IR = 72, DR = 16220401
IR = 73, DR = 0
...
IR = 87, DR = 0
IR = 88, DR = 1
IR = 89, DR = 0
IR = 8a, DR = 1
IR = 8b, DR = 1
IR = 8c, DR = 0
IR = 8d, DR = 0
IR = 8e, DR = 0
IR = 8f, DR = 0
IR = 90, DR = 0
IR = 91, DR = 0
IR = 92, DR = 30023
IR = 93, DR = 0
...
IR = 9f, DR = 0
IR = a0, DR = 16224a5
IR = a1, DR = 0
...
IR = ff, DR = 0
```
Not much has changed, but notice the IR = 0x34, this looks like an address in code memory! Could it be current PC value? I did a test with this simple program:
```
devmem 0x20080 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20084 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20088 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x2008C 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20090 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20094 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x20098 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x2009C 32 0x3CA03CA0 # SQ.nop SQ.nop
devmem 0x200A0 32 0x9ABFF81F # SQ.brr{t} 0xFFFFFFE0 (-0x20, to 0x20080)
```
Now DR value of IR = 0x34 always falls in 0xC0020080 - 0xC00200A4. It's not exactly value of PC, but PC+4(or PC-4 sometimes?)

## What we've got
Further analysis of the interface (and building an opensource host debugger) isn't practically feasible. But we've at least learnt how to read PC value - which enables DSP execution tracing and could potentially help a lot in instrution discovery.
