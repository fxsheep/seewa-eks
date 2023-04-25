#!/usr/bin/env python3
import tkinter as tk

class BitSwitch(tk.Frame):
    def __init__(self, master=None, bit=0, **kwargs):
        super().__init__(master, **kwargs)
        self.bit = bit
        self.var = tk.BooleanVar()
        self.var.set(False)
        self.checkbox = tk.Checkbutton(self, variable=self.var, command=self.update_text)
        self.checkbox.pack(side="right")

    def update_text(self):
        bits = [switch.var.get() for switch in reversed(switches)]
        num = sum(bit << i for i, bit in enumerate(bits))
        with open("insn_16_nohex.txt", "r") as f:
            lines = f.readlines()
            if num < len(lines):
                text.delete("1.0", "end")
                text.insert("end", lines[num])

root = tk.Tk()
root.title("16-bit Binary Switches")

switches = [BitSwitch(root, bit=i) for i in range(16)]
for switch in switches:
    switch.pack(side="left")

text = tk.Text(root, height=3, width=50)
text.pack()

root.mainloop()


