// Ghidra headless helper for KreoSWARM75 static analysis.
// Usage: -postScript ReaDump.java <command> <outFile> [args...]
//   decomp     <out> <va> [va...]     decompile function(s) containing VA
//   imports    <out>                  external symbols + all call sites
//   functions  <out>                  every function: entry, name, size
//   strings    <out>                  defined strings + containing function
//   xrefs      <out> <va> [va...]     references to VA (incl. data/call)
//   bytes      <out> <va> <len>       raw bytes at VA

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.data.DataUtilities;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;

public class ReaDump extends GhidraScript {

    private PrintWriter out;

    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        if (a.length < 2) {
            println("usage: decomp|imports|functions|strings|xrefs|bytes <out> [args]");
            return;
        }
        String cmd = a[0];
        out = new PrintWriter(new OutputStreamWriter(new FileOutputStream(a[1]), "UTF-8"));
        try {
            if ("decomp".equals(cmd)) {
                for (int i = 2; i < a.length; i++) decomp(toVa(a[i]));
            } else if ("imports".equals(cmd)) {
                imports();
            } else if ("functions".equals(cmd)) {
                functions();
            } else if ("strings".equals(cmd)) {
                strings();
            } else if ("xrefs".equals(cmd)) {
                for (int i = 2; i < a.length; i++) xrefs(toVa(a[i]));
            } else if ("bytes".equals(cmd)) {
                bytes(toVa(a[2]), Integer.decode(a[3]));
            } else if ("disasm".equals(cmd)) {
                disasm(toVa(a[2]), Integer.decode(a[3]));
            } else if ("syms".equals(cmd)) {
                syms(a[2]);
            } else {
                out.println("unknown command " + cmd);
            }
        } finally {
            out.flush();
            out.close();
        }
    }

    private Address toVa(String s) {
        long v = Long.decode(s);
        AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
        return sp.getAddress(v);
    }

    private String fnName(Address addr) {
        Function f = getFunctionContaining(addr);
        if (f == null) return "<no-function>";
        return f.getName() + " @ " + f.getEntryPoint();
    }

    private void decomp(Address va) {
        Function f = getFunctionContaining(va);
        if (f == null) {
            out.println("=== " + va + " NOT IN A FUNCTION ===");
            return;
        }
        DecompInterface di = new DecompInterface();
        di.toggleCCode(true);
        di.toggleSyntaxTree(true);
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);
        DecompileResults res = di.decompileFunction(f, 120, new ConsoleTaskMonitor());
        out.println("=== " + f.getName() + " @ " + f.getEntryPoint()
                + "  size=" + f.getBody().getNumAddresses()
                + "  completed=" + res.decompileCompleted() + " ===");
        if (res.decompileCompleted()) {
            out.println(res.getDecompiledFunction().getC());
        } else {
            out.println("// decompile failed: " + res.getErrorMessage());
        }
        out.println();
        try { di.dispose(); } catch (Exception ignored) { }
    }

    private void imports() {
        SymbolTable st = currentProgram.getSymbolTable();
        SymbolIterator it = st.getAllSymbols(true);
        for (Symbol s : it) {
            if (!s.isExternal()) continue;
            Address a = s.getAddress();
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(a);
            int n = 0;
            StringBuilder sb = new StringBuilder();
            for (Reference r : refs) {
                n++;
                sb.append("\n    from ").append(r.getFromAddress())
                  .append("  ").append(r.getReferenceType())
                  .append("  ").append(fnName(r.getFromAddress()));
            }
            if (n > 0) {
                out.println(s.getName() + "  @" + a + "  (" + n + " refs)" + sb);
            }
        }
    }

    private void functions() {
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            out.println(f.getEntryPoint() + "\t" + f.getBody().getNumAddresses() + "\t" + f.getName());
        }
    }

    private void strings() {
        long count = 0;
        for (var d : currentProgram.getListing().getDefinedData(true)) {
            if (!d.hasStringValue()) continue;
            count++;
            out.println(d.getAddress() + "\t" + fnName(d.getAddress()) + "\t"
                    + d.getValue().toString().replace('\n', ' '));
        }
        out.println("// total strings: " + count);
    }

    private void xrefs(Address va) {
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(va);
        int n = 0;
        for (Reference r : refs) {
            n++;
            out.println(va + " <- " + r.getFromAddress() + "  " + r.getReferenceType()
                    + "  " + fnName(r.getFromAddress()) + "\n    "
                    + insnAt(r.getFromAddress()));
        }
        if (n == 0) out.println(va + " <- no references");
    }

    private String insnAt(Address a) {
        Instruction ins = currentProgram.getListing().getInstructionContaining(a);
        return ins == null ? "?" : ins.toString();
    }

    private void syms(String regex) {
        SymbolTable st = currentProgram.getSymbolTable();
        SymbolIterator it = st.getAllSymbols(true);
        int n = 0;
        for (Symbol s : it) {
            if (!s.getName().matches(regex)) continue;
            n++;
            out.println(s.getAddress() + "\t" + s.getSymbolType() + "\t" + s.getName()
                    + "\tparent=" + (s.getParentSymbol() == null ? "-" : s.getParentSymbol().getName()));
        }
        out.println("// matches: " + n);
    }

    private void disasm(Address va, int count) {
        InstructionIterator it = currentProgram.getListing().getInstructions(va, true);
        int n = 0;
        while (it.hasNext() && n < count) {
            Instruction ins = it.next();
            out.println(ins.getAddress() + "  " + ins.toString());
            n++;
        }
    }

    private void bytes(Address va, int len) throws Exception {        Memory mem = currentProgram.getMemory();
        byte[] buf = new byte[len];
        int got = mem.getBytes(va, buf);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < got; i++) {
            if (i % 16 == 0) sb.append("\n").append(va.add(i)).append("  ");
            sb.append(String.format("%02x ", buf[i]));
        }
        out.println(sb);
    }
}
