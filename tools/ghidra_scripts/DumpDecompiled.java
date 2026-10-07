// Decompile every function in the program and write them to ghidra/decomp.c
// (one block per function, headed by "// FUNCTION <address> <name>").
// Usage: python tools/ghidra.py script DumpDecompiled.java <output path>
// @category FF1DoS
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class DumpDecompiled extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String out = args.length > 0 ? args[0] : "decomp.c";
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int n = 0, failed = 0;
        try (PrintWriter w = new PrintWriter(out, "UTF-8")) {
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (monitor.isCancelled()) break;
                DecompileResults r = ifc.decompileFunction(f, 60, monitor);
                w.println("// FUNCTION " + f.getEntryPoint() + " " + f.getName());
                if (r != null && r.decompileCompleted()) {
                    w.println(r.getDecompiledFunction().getC());
                } else {
                    w.println("// decompile failed\n");
                    failed++;
                }
                if (++n % 500 == 0) println("decompiled " + n);
            }
        }
        println("done: " + n + " functions, " + failed + " failed -> " + out);
    }
}
