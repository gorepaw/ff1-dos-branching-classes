// Decompile the functions containing the given addresses (Thumb code assumed).
// Creates functions on demand, since the project is imported without auto-analysis.
// Usage: python tools/ghidra.py script DecompileAt.java <out.c> <addr|@listfile> ...
//   addresses are GBA bus addresses in hex (0x0801591C) or ROM offsets (1591C).
//   A "@file" argument reads one address per line ('#' starts a comment).
// @category FF1DoS
import java.io.PrintWriter;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.lang.Register;
import ghidra.program.model.lang.RegisterValue;
import ghidra.program.model.listing.Function;

public class DecompileAt extends GhidraScript {

    private Address parse(String s) {
        long v = Long.parseLong(s.trim().replaceFirst("^0x", ""), 16);
        if (v < 0x08000000L) v += 0x08000000L;
        return toAddr(v & ~1L);
    }

    private Function ensureFunction(Address a) throws Exception {
        Function f = getFunctionContaining(a);
        if (f != null) return f;
        if (getInstructionAt(a) == null) {
            Register tmode = currentProgram.getRegister("TMode");
            DisassembleCommand cmd = new DisassembleCommand(a, null, true);
            cmd.setInitialContext(new RegisterValue(tmode, BigInteger.ONE));
            cmd.applyTo(currentProgram, monitor);
        }
        CreateFunctionCmd cf = new CreateFunctionCmd(a);
        cf.applyTo(currentProgram, monitor);
        return getFunctionAt(a);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String out = args[0];
        List<String> addrs = new ArrayList<>();
        for (int i = 1; i < args.length; i++) {
            if (args[i].startsWith("@")) {
                for (String line : Files.readAllLines(Paths.get(args[i].substring(1)))) {
                    line = line.replaceFirst("#.*", "").trim();
                    if (!line.isEmpty()) addrs.add(line.split("\\s+")[0]);
                }
            } else {
                addrs.add(args[i]);
            }
        }
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        Set<Function> done = new LinkedHashSet<>();
        try (PrintWriter w = new PrintWriter(out, "UTF-8")) {
            for (String s : addrs) {
                Address a = parse(s);
                Function f = ensureFunction(a);
                if (f == null) {
                    w.println("// " + a + ": could not create function\n");
                    continue;
                }
                if (!done.add(f)) continue;
                DecompileResults r = ifc.decompileFunction(f, 120, monitor);
                w.println("// FUNCTION " + f.getEntryPoint() + " (requested " + a + ")");
                w.println(r != null && r.decompileCompleted()
                        ? r.getDecompiledFunction().getC() : "// decompile failed\n");
            }
        }
        println("wrote " + done.size() + " functions to " + out);
    }
}
