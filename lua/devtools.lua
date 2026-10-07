-- mGBA dev helpers for FF1 Dawn of Souls (USA).
-- Load via Tools > Scripting > File > Load script, then call functions from the
-- scripting console, e.g.  party()   snap()   diff()   setgil(99999)
--
-- RAM addresses from Data Crystal; struct fields from decompiling new-game init.

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

-- Character struct fields (from new-game init at 0x0804E580)
C_CLASS, C_LEVEL, C_EXP       = 0x0D, 0x0E, 0x10
C_HP, C_HPMAX, C_MP, C_MPMAX  = 0x14, 0x16, 0x18, 0x1A
C_SPELLCAP                    = 0x1C
C_STR, C_AGI, C_INT, C_STA, C_LCK = 0x1D, 0x1E, 0x1F, 0x20, 0x21

CLASSES = {[0]="Warrior","Thief","Monk","Red Mage","White Mage","Black Mage",
           "Knight","Ninja","Master","Red Wizard","White Wizard","Black Wizard",
           "Dark Knight","Ranger","Druid","Spellblade"}

local function charaddr(slot) return PARTY + slot * CHAR_SIZE end

-- Write one byte in a character struct: pokechar(slot 0-3, offset, value).
function pokechar(slot, offset, value)
  emu:write8(charaddr(slot) + offset, value)
end

-- One-line summary per party member.
function chars()
  for c = 0, 3 do
    local a = charaddr(c)
    local cls = emu:read8(a + C_CLASS)
    console:log(string.format("%d: %-12s Lv%2d  HP %4d/%4d  MP %3d/%3d  STR %2d AGI %2d INT %2d STA %2d LCK %2d",
      c, CLASSES[cls] or ("class " .. cls), emu:read8(a + C_LEVEL) + 1,
      emu:read16(a + C_HP), emu:read16(a + C_HPMAX), emu:read16(a + C_MP), emu:read16(a + C_MPMAX),
      emu:read8(a + C_STR), emu:read8(a + C_AGI), emu:read8(a + C_INT),
      emu:read8(a + C_STA), emu:read8(a + C_LCK)))
  end
end

function setclass(slot, cls) pokechar(slot, C_CLASS, cls) end

-- Sets the level byte only; stats are not recalculated.
function setlevel(slot, lv) pokechar(slot, C_LEVEL, lv - 1) end

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

console:log("FF1 DoS devtools loaded: chars() party() setclass() setlevel() pokechar() setgil() snap() diff()")
