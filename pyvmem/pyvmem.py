class VMem:
    def __init__(self, endianness="little"):
        self.mappings = {}
        if endianness != "little" and endianness != "big":
            raise ValueError("endianness can only be 'big' or 'little'")
        self.endianness = endianness
    
    def __setitem__(self, address:slice, data:bytes):
        #sanity checks
        if type(address) == int:
            address = slice(address, address+1)
        if type(address) is not slice:
            raise ValueError(f"Index must be an integer or slice got {type(address)}")
        if type(data) != bytes and type(data) != bytearray:
            raise ValueError(f"Data must be bytes or bytearray got {type(data)}")
        
        start, end = address.start, address.stop
        
        if end == None:
            end = start + len(data)
        elif start == None:
            start = end - len(data)
            print(f"{start = :#x}")

        mappings = self._get_mappings_from_addr_range(start, end)
        if len(mappings) != 1:
            raise ValueError("VMem index out of range")
        
        map_start, map_end = mappings[0]
        
        if len(data) != (end - start):
            raise ValueError(f"data length must be the same as slice length {len(data) = } vs  {end - start = }")
        if map_start > start:
            raise ValueError("VMem index out of range")
        if end > map_end:
            raise ValueError("VMem index out of range")
        

        map_rel_start = start - map_start
        map_rel_end = end - map_start
        self.mappings[(map_start, map_end)][map_rel_start:map_rel_end] = data
    
    def __repr__(self):
        representation = ""

        for map_start, map_end in self.mappings:
            representation += f"{map_start:#x}-{map_end:#x}\n"
        return representation[:-1]
        
    def __getitem__(self, address:slice):
        if type(address) == int:
            address = slice(address, address+1)
        if type(address) is not slice:
            raise ValueError(f"Index must be an integer or slice got {type(address)}")
        
        start, end = address.start, address.stop

        if end == None:
            end = start+1
        elif start == None:
            start = end-1
        
        mappings = self._get_mappings_from_addr_range(start, end)
        if len(mappings) != 1:
            raise ValueError("VMem index out of range")
        
        map_start, map_end = mappings[0]
        if map_start > start:
            raise ValueError("VMem index out of range")
        if end > map_end:
            raise ValueError("VMem index out of range")
        
        if address.stop == None:
            end = map_end
        elif address.start == None:
            start = map_start
        
        map_rel_start = start - map_start
        map_rel_end = end - map_start

        return bytes(self.mappings[(map_start, map_end)][map_rel_start:map_rel_end])
    
    def __iter__(self):
        for value in b''.join(self.mappings.values()):
            yield value


    def _get_mappings_from_addr_range(self, addr_start, addr_end):
        address_len = addr_end - addr_start
        if address_len < 0:
            raise ValueError("addr_end must be higher than addr_start")

        mappings = []

        for (map_start, map_end) in self.mappings:
            # Sought start address is within the mapping
            if map_start <= addr_start and map_end >= addr_start:
                mappings.append((map_start, map_end))
            
            # Sought end address is within the mapping
            elif map_start <= addr_end and map_end >= addr_end:
                mappings.append((map_start, map_end))

            # Mapping is inside of the range we are trying to grab
            elif addr_start <= map_start and addr_end >= map_end:
                mappings.append((map_start,map_end))

        return mappings
    
    def _get_mapping_from_addr(self, addr):
        for (map_start, map_end) in self.mappings:
            if addr >= map_start and addr <= map_end:
                return map_start, map_end
        return None, None 

        

    def add_mapping(self, start:int, end:int):
        if type(start) is not int or type(end) is not int:
            raise ValueError(f"start and end must be ints")
        if start < 0 or end < 0:
            raise ValueError(f"addresses cannot be negative")
        
        # We only add at least a page
        real_start = start & 0xfffffffffffff000
        real_end = (end & 0xfffffffffffff000)

        if end & 0xfff != 0:
            real_end += 0x1000
        elif real_end == real_start:
            real_end += 0x1000

        mappings = self._get_mappings_from_addr_range(real_start, real_end)

        # Mapping does not exist
        if len(mappings) == 0:
            self.mappings[(real_start, real_end)] = bytearray(real_end - real_start)
            return
        
        # Do mapping
        new_map_start = min(mappings)[0]
        new_map_end = max(mappings)[1]

        if new_map_start > real_start:
            new_map_start = real_start
        if new_map_end < real_end:
            new_map_end = real_end
        
        new_mapping_data = bytearray(new_map_end - new_map_start)

        for map_start, map_end in mappings:
            map_start_off = map_start - new_map_start
            map_end_off = new_map_end - map_end
            
            new_mapping_data[map_start_off:map_end_off] = self.mappings[(map_start, map_end)]
            del self.mappings[(map_start, map_end)]
        
        self.mappings[(new_map_start, new_map_end)] = new_mapping_data
    
    def read_u64(self, addr):
        return int.from_bytes(self[addr:addr+8], byteorder=self.endianness)
    
    def read_u32(self, addr):
        return int.from_bytes(self[addr:addr+4], byteorder=self.endianness)
    
    def read_u16(self, addr):
        return int.from_bytes(self[addr:addr+2], byteorder=self.endianness)
    
    def read_u8(self,addr):
        return int.from_bytes(self[addr:addr+1], byteorder=self.endianness)
    
    def read_cstr(self, addr):
        ret = b''
        for byte in self[addr:]:
            if byte == 0x0:
                break
            ret += byte.to_bytes(1,"little")
        return ret

