//@category Sunplus/Verification
// Exact source-image readback, no mutation; counts only native DO/CE P-code edges.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.*;
import java.util.regex.*;

public class SunplusDSPResetEscapeNativeCeReadback extends GhidraScript {
 private static final Pattern DO=Pattern.compile("^DO 0x([0-9a-f]+) UNTIL CE$",Pattern.CASE_INSENSITIVE);
 public void run() throws Exception {
  String[] args=getScriptArgs();
  if(args.length!=1 || !args[0].equals(currentProgram.getExecutableSHA256()) ||
      !"SunplusSPHEAudioDSP:BE:16:default".equals(currentProgram.getLanguageID().getIdAsString()) ||
      currentProgram.isChanged())throw new IllegalStateException("Unmatched native image or unsaved state");
  int version=currentProgram.getDomainFile().getVersion();
  Listing listing=currentProgram.getListing();
  int total=0,direct=0,indirect=0,unknown=0;
  for(Instruction begin:listing.getInstructions(true)) {
   if(!"PM".equals(begin.getAddress().getAddressSpace().getName()))continue;
   Matcher m=DO.matcher(begin.toString().trim());if(!m.matches())continue;
   total++;
   int target=Integer.parseInt(m.group(1),16);
   Address at=currentProgram.getAddressFactory().getAddress(String.format("PM:%04x",target));
   Instruction end=listing.getInstructionAt(at);
   if(end==null){unknown++;continue;}
   int branches=0,computed=0,conditional=0;
   Address expected=currentProgram.getAddressFactory().getAddress(String.format("PM:%04x",
     (int)begin.getAddress().getAddressableWordOffset()+1));
   for(PcodeOp op:end.getPcode()){
    if(op.getOpcode()==PcodeOp.BRANCH && op.getInput(0).getAddress().equals(expected))branches++;
    if(op.getOpcode()==PcodeOp.BRANCHIND)computed++;
    if(op.getOpcode()==PcodeOp.CBRANCH)conditional++;
   }
   if(branches==1 && conditional>0 && computed==0)direct++;
   else if(computed==1 && conditional>0) {
    indirect++;
    Function f=currentProgram.getFunctionManager().getFunctionContaining(begin.getAddress());
    println("CE_REMAINS source="+begin.getAddress()+" target="+at+
      " owner="+(f==null?"NONE":f.getEntryPoint()));
   } else unknown++;
  }
  println("CE_NATIVE_READBACK total="+total+" direct="+direct+" indirect="+indirect+
      " unknown="+unknown+" functions="+currentProgram.getFunctionManager().getFunctionCount()+
      " sha="+currentProgram.getExecutableSHA256());
  if(total!=direct+indirect+unknown || currentProgram.isChanged() ||
     currentProgram.getDomainFile().getVersion()!=version)
    throw new IllegalStateException("Readback integrity failure");
 }
}
