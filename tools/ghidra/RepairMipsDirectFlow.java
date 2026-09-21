// Audit by default; pass script argument "apply" to repair proven stale refs.
// Analysis metadata only: never rebases, disassembles, or modifies module bytes.
// Scope: currently defined MIPS32 J/JAL instructions, not indirect/data refs.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.security.MessageDigest;
import java.util.*;

public class RepairMipsDirectFlow extends GhidraScript {
    private long deadline;
    private void budget() {
        if (System.nanoTime() > deadline) throw new IllegalStateException("4s execution budget exceeded");
    }
    private String digest() throws Exception {
        long size = currentProgram.getMemory().getSize();
        if (size > 301072 || size < 1) throw new IllegalStateException("Unexpected memory size");
        byte[] data = new byte[(int) size];
        int got = currentProgram.getMemory().getBytes(currentProgram.getMinAddress(), data);
        if (got != data.length) throw new IllegalStateException("Incomplete module read");
        StringBuilder result = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(data)) result.append(String.format("%02x", b & 255));
        return result.toString();
    }
    private static class Change {
        Instruction instruction; Reference old; long target; int word;
        Change(Instruction i, Reference r, long t, int w) { instruction=i; old=r; target=t; word=w; }
    }
    private List<Change> audit(boolean report) throws Exception {
        List<Change> changes = new ArrayList<>();
        int direct = 0;
        long delta = currentProgram.getImageBase().getOffset() & 0x0fffffffL;
        InstructionIterator iterator = currentProgram.getListing().getInstructions(true);
        while (iterator.hasNext()) {
            budget();
            Instruction i = iterator.next();
            int word = currentProgram.getMemory().getInt(i.getAddress());
            int opcode = word >>> 26;
            if (opcode != 2 && opcode != 3) continue;
            direct++;
            long target = ((i.getAddress().getOffset()+4) & 0xf0000000L) | ((word & 0x03ffffffL) << 2);
            int flows = 0;
            for (Reference r : i.getReferencesFrom()) {
                if (!r.getReferenceType().isFlow()) continue;
                flows++;
                if (r.getToAddress().getOffset() == target) continue;
                if (r.getSource() != SourceType.DEFAULT || !r.isMemoryReference() ||
                    ((r.getToAddress().getOffset()-target) & 0xffffffffL) != delta)
                    throw new IllegalStateException("Unrecognized mismatch at " + i.getAddress());
                changes.add(new Change(i,r,target,word));
                if (report) println(String.format("REPAIR_PLAN %s %s -> %08x word=%08x",i.getAddress(),r.getToAddress(),target,word));
            }
            if (flows != 1) throw new IllegalStateException("Expected one flow ref at " + i.getAddress());
        }
        println("program=" + currentProgram.getName() + " direct=" + direct + " mismatches=" + changes.size());
        return changes;
    }
    public void run() throws Exception {
        deadline = System.nanoTime() + 4000000000L;
        long base; String expected; int count;
        switch (currentProgram.getName()) {
        case "wma.bin": base=0x8073f000L; count=2; expected="8fd9d673b847b6764e8bd52888a86f42f040c0c07a141b9c3384f503eae8f26f"; break;
        case "cdrom.bin": base=0x8074c800L; count=17; expected="476368446103ddeb3e067ec556472e7d2e18d68e6da2ce7911a539661f6f3b61"; break;
        case "drv_other.bin": base=0x80775800L; count=24; expected="e9463f81093a43990c39ca39555d2742f29ebb2fe7fc7ca7e8eac0b694de6451"; break;
        default: throw new IllegalStateException("Unsupported program");
        }
        if (!currentProgram.getLanguageID().toString().equals("MIPS:LE:32:default") ||
            currentProgram.getImageBase().getOffset()!=base || currentProgram.getMinAddress().getOffset()!=base)
            throw new IllegalStateException("Unexpected language/base");
        if (!digest().equals(expected)) throw new IllegalStateException("Not the canonical module bytes");
        List<Change> changes=audit(true);
        boolean apply=getScriptArgs().length==1 && getScriptArgs()[0].equals("apply");
        if (!apply || changes.isEmpty()) { println("No mutation; apply="+apply); return; }
        if (changes.size()!=count) throw new IllegalStateException("Expected mismatch count changed; re-audit first");
        int transaction=currentProgram.startTransaction("Repair proven stale MIPS J/JAL refs, issue #9");
        boolean commit=false;
        try {
            ReferenceManager rm=currentProgram.getReferenceManager();
            for (Change c:changes) {
                budget();
                Address target=c.instruction.getAddress().getAddressSpace().getAddress(c.target);
                boolean primary=c.old.isPrimary();
                rm.delete(c.old);
                Reference replacement=rm.addMemoryReference(c.instruction.getAddress(),target,c.old.getReferenceType(),SourceType.USER_DEFINED,c.old.getOperandIndex());
                rm.setPrimary(replacement,primary);
                String note=String.format("[#9] Flow ref corrected from %s to %08x using unchanged instruction word %08x; no byte patch.",c.old.getToAddress(),c.target,c.word);
                String old=currentProgram.getListing().getComment(CodeUnit.EOL_COMMENT,c.instruction.getAddress());
                currentProgram.getListing().setComment(c.instruction.getAddress(),CodeUnit.EOL_COMMENT,old==null?note:old+"\n"+note);
            }
            if (!audit(false).isEmpty() || !digest().equals(expected)) throw new IllegalStateException("Postcondition failed");
            budget(); commit=true;
        } finally { currentProgram.endTransaction(transaction,commit); }
        println("COMMITTED_METADATA_REPAIRS="+changes.size()+" canonical_bytes_unchanged=true; save the program to persist");
    }
}
