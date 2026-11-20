// Grep instruction text for substrings and report the containing function.
// Usage: -postScript ReaGrep.java <outFile> <needle> [needle...]
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;

public class ReaGrep extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        if (a.length < 2) {
            println("usage: ReaGrep.java <out> <needle> [needle...]");
            return;
        }
        PrintWriter out = new PrintWriter(new OutputStreamWriter(new FileOutputStream(a[0]), "UTF-8"));
        try {
            InstructionIterator it = currentProgram.getListing().getInstructions(true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                String t = ins.toString();
                for (int i = 1; i < a.length; i++) {
                    if (t.contains(a[i])) {
                        Function f = getFunctionContaining(ins.getAddress());
                        out.println(String.format("%s\t%s\t%s\t%s",
                                a[i],
                                ins.getAddress(),
                                f == null ? "<none>" : f.getEntryPoint().toString(),
                                t));
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
