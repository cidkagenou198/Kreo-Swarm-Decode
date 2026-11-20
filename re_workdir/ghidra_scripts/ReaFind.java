// Scan instructions for scalar operands equal to the given values.
// Usage: -postScript ReaFind.java <outFile> <hexval> [hexval...]
// Prints: value \t function-entry \t instruction
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.OperandType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;

public class ReaFind extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        if (a.length < 2) {
            println("usage: ReaFind.java <out> <hexval> [hexval...]");
            return;
        }
        Set<Long> want = new HashSet<>();
        for (int i = 1; i < a.length; i++) want.add(Long.decode(a[i]));

        PrintWriter out = new PrintWriter(new OutputStreamWriter(new FileOutputStream(a[0]), "UTF-8"));
        try {
            InstructionIterator it = currentProgram.getListing().getInstructions(true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                int n = ins.getNumOperands();
                for (int op = 0; op < n; op++) {
                    if (ins.getOperandType(op) != OperandType.SCALAR) continue;
                    Object[] o = ins.getOpObjects(op);
                    for (Object obj : o) {
                        if (!(obj instanceof ghidra.program.model.scalar.Scalar)) continue;
                        long v = ((ghidra.program.model.scalar.Scalar) obj).getUnsignedValue();
                        if (!want.contains(v)) continue;
                        Function f = getFunctionContaining(ins.getAddress());
                        out.println(String.format("0x%x\t%s\t%s\t%s",
                                v,
                                f == null ? "<none>" : f.getEntryPoint().toString(),
                                f == null ? "?" : f.getName(),
                                ins.toString()));
                        break;
                    }
                }
            }
        } finally {
            out.flush();
            out.close();
        }
    }
}
