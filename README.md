# seewa-eks
Fun with some DSP cores inside some phone-SoCs. The specific Android phone is Samsung GT-S7568, which is a decade old at the time of writing. Background information can be found [here](https://github.com/fxsheep/kyletd_modem/wiki). 

## Writeups
These are what I've done so far, in time order:
 - [`t32_insn_bruteforce`](https://github.com/fxsheep/seewa-eks/tree/main/info/t32_insn_bruteforce): A way to discover DSP instruction set and encoding with commercial but publicly available [software](https://www.lauterbach.com/).
 - [`dsp_memory_server`](https://github.com/fxsheep/seewa-eks/tree/main/info/dsp_memory_server): The first DSP 'application' (well, sort of) I've written without access to proprietary ISA documentation
