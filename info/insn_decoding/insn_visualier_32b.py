#!/usr/bin/env python3
import subprocess
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
        num = (sum(bit << i for i, bit in enumerate(bits)) & 0x3fffffff) >> 8
        command = ["xz", "-d", "-c", "insn_32_0x100.txt.xz"]
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        for i, line in enumerate(p.stdout):
            if i == num:
                text.delete("1.0", tk.END)
                text.insert(tk.END, line.decode("utf-8"))
                break

root = tk.Tk()
root.title("32-bit Binary Switches")

switches = [BitSwitch(root, bit=i) for i in range(32)]
for switch in switches:
    switch.pack(side="left")

text = tk.Text(root, height=3, width=50)
text.pack()

root.mainloop()


