# pyvmem

A data structure to work with virtual memory in Python.

```py
from pyvmem import VMem
a = VMem()
a.add_mapping(0x404000, 0x405000)

a[0x404000:0x404008] = b'A'*0x8  # Specifying exact range. If range is shorter or longer than the data, it raisees a ValueError
a[0x404010:] = b'B'*0x8 # Specifying only start of range but not end of range. Adds the length of the bytestring to the mem array

print(a[0x404000:0x404020].hex()) # Output: 4141414141414141000000000000000042424242424242420000000000000000
print(a) # Output: 0x404000-0x405000

a.add_mapping(0x403000, 0x408000) # Overlaps with previous mappings, keeps data inside of the original mappings which it overlaps
print(a) # Output: 0x403000-0x408000

print(a[0x404000:0x404020].hex()) # Output: 4141414141414141000000000000000042424242424242420000000000000000

some_str = a.read_cstr(0x404000) # Reads up to first NULL byte. 
print(some_str) # Output: b'AAAAAAAA'

print(hex(a.read_u64(0x404000))) # Output: 0x4141414141414141

a[0x404000:] = b'C'*8 #Overwrites the first 8 A's with C's instead
print(a[0x404000:0x404008]) #Output: b'CCCCCCCC'
```
### What is it for?
I sometimes have to emulate functions with a lot of memory values being thrown around along with pointer arithmetics.

Very often when I had this problem I wish a tool like this existed, which just allowed me to treat a list like a virtual memory map. So I made it.

This has helped me countless times in not only emulating C based functions when reversing, but also just makes /proc/pid/mem and /proc/pid/maps files and dumps a lot easier to work with.
