-- mGBA dev helpers for FF1 Dawn of Souls (USA).
-- Load via Tools > Scripting > File > Load script, then call functions from the
-- scripting console, e.g.  party()   snap()   diff()   setgil(99999)
--
-- RAM addresses from Data Crystal; struct field offsets are mapped in phase 1.

PARTY      = 0x020026CC  -- 4 characters x 0x48 bytes
CHAR_SIZE  = 0x48
INVENTORY  = 0x020027EC  -- 0xB2 slots x 4 bytes
GIL        = 0x02002AB4
SNAP_START = 0x02000000  -- region covered by snap()/diff()
SNAP_END   = 0x02008000

local function hexline(addr, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", emu:read8(addr + i)) end
  return table.concat(t, " ")
end

-- Hex dump of each party member's struct.
function party()
  for c = 0, 3 do
    local base = PARTY + c * CHAR_SIZE
    console:log(string.format("-- char %d @ %08X", c, base))
    for o = 0, CHAR_SIZE - 1, 16 do
      console:log(string.format("  +%02X  %s", o, hexline(base + o, math.min(16, CHAR_SIZE - o))))
    end
  end
end

-- Write one byte in a character struct: pokechar(slot 0-3, offset, value).
function pokechar(slot, offset, value)
  emu:write8(PARTY + slot * CHAR_SIZE + offset, value)
end

function setgil(n) emu:write32(GIL, n) end

-- Memory diffing: snap(), do something in game, diff() lists changed bytes.
local snapshot = nil
function snap()
  snapshot = {}
  for a = SNAP_START, SNAP_END - 1 do snapshot[a] = emu:read8(a) end
  console:log("snapshot taken")
end

function diff(maxlines)
  if not snapshot then console:log("call snap() first") return end
  maxlines = maxlines or 200
  local n = 0
  for a = SNAP_START, SNAP_END - 1 do
    local v = emu:read8(a)
    if v ~= snapshot[a] then
      n = n + 1
      if n <= maxlines then
        console:log(string.format("%08X: %02X -> %02X", a, snapshot[a], v))
      end
    end
  end
  console:log(string.format("%d bytes changed", n))
end

console:log("FF1 DoS devtools loaded: party() pokechar() setgil() snap() diff()")
