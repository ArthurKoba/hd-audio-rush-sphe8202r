//@category Sunplus/Architecture
// Saved original program linked composite CALL+CE classification readback.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.PcodeOp;
import com.xebyte.sunplus.SunplusNativeCeCallCompositeRecovery;
import java.util.*;
public class SunplusDSPCompositeCallCeReadback extends GhidraScript {
 public void run()throws Exception{
  var args=getScriptArgs();if(args.length!=2||!args[0].equals(currentProgram.getExecutableSHA256())||currentProgram.isChanged())throw new IllegalStateException("Exact saved source required");
  if(currentProgram.getFunctionManager().getFunctionCount()!=Integer.parseInt(args[1]))throw new IllegalStateException("Function inventory mismatch");
  var options=currentProgram.getOptions(SunplusNativeCeCallCompositeRecovery.OPTIONS_NAME);
  int rawInvalid=0,classified=0,unresolved=0;
  for(Instruction ins:currentProgram.getListing().getInstructions(true)){
   monitor.checkCancelled();if(!"PM".equals(ins.getAddress().getAddressSpace().getName())||ins.getLength()!=3)continue;
   if(!"INVALID".equals(ins.getFlowType().toString()))continue;
   rawInvalid++;
   String proof=options.getString(ins.getAddress().toString(),"");
   if(proof.isEmpty()){unresolved++;continue;}
   if(!proof.startsWith("CONFIRMED_STATIC|CALL=")||!proof.contains("|DO=")||!proof.contains("|CE_BACKEDGE=")||!proof.contains("|RUNTIME_STACK=UNKNOWN")||!proof.contains("|NATIVE_BYTES="+HexFormat.of().formatHex(ins.getBytes())))throw new IllegalStateException("Composite source is misclassified "+ins.getAddress());
   boolean call=false,branch=false;for(PcodeOp op:ins.getPcode()){if(op.getOpcode()==PcodeOp.CALL)call=true;if(op.getOpcode()==PcodeOp.BRANCH)branch=true;}
   if(!call||!branch||ins.getFlows().length!=2)throw new IllegalStateException("Source CALLED and CE lost "+ins.getAddress());
   classified++;println("COMPOSITE_CE_CALL_SAVED_SOURCE at="+ins.getAddress()+" proof="+proof+" GhidraFlowType="+ins.getFlowType()+" realFlowEdges="+Arrays.toString(ins.getFlows()));
  }
  if(classified!=options.getInt("verified_composite_ce_call_count",-1)||unresolved!=options.getInt("unresolved_invalid_native_flow_count",-1))throw new IllegalStateException("Native source-flow composite total mismatch");
  println("COMPOSITE_CE_CALL_READBACK invalidGhidraFlowType="+rawInvalid+" compositeClassified="+classified+" unresolvedNativeFlow="+unresolved+" savedSourceSHA="+currentProgram.getExecutableSHA256());
 }
}
