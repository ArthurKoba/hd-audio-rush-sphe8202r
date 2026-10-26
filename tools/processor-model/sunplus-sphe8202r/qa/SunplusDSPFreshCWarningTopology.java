//@category Sunplus/Verification
// Read-only native C diagnostics on a saved original-source QA module.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.util.*;
public class SunplusDSPFreshCWarningTopology extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();
  if(args.length!=2||!args[0].equals(currentProgram.getExecutableSHA256()) ||
     !"SunplusSPHEAudioDSP:BE:16:default".equals(currentProgram.getLanguageID().getIdAsString())||
     currentProgram.isChanged()||currentProgram.getFunctionManager().getFunctionCount()!=Integer.parseInt(args[1]))
   throw new IllegalArgumentException("Exact saved source image and function denominator required");
  int before=currentProgram.getDomainFile().getVersion();
  int checked=0,successes=0,warningLines=0,bad=0,unresolved=0;
  Map<String,Integer> categories=new TreeMap<>();
  DecompInterface dc=new DecompInterface();
  if(!dc.openProgram(currentProgram))throw new IllegalStateException("Native C generator not available");
  try {
   for(Function fn:currentProgram.getFunctionManager().getFunctions(true)){
    monitor.checkCancelled();if(fn.isExternal())continue;checked++;
    DecompileResults result=dc.decompileFunction(fn,30,monitor);
    if(!result.decompileCompleted()||result.getDecompiledFunction()==null){
      println("FRESH_C_FAILURE "+fn.getEntryPoint()+" "+result.getErrorMessage());continue;
    }
    String text=result.getDecompiledFunction().getC();successes++;
    if(text.contains("halt_baddata"))bad++;
    int warnings=0,indirect=0;
    for(String line:text.split("\\n")){
      if(line.contains("WARNING:")){
        warnings++;warningLines++;
        String category=line.contains("unreachable block")?"UNREACHABLE_BLOCK":
          line.contains("jumptable")?"JUMP_TABLE":
          line.contains("overlap")?"SYMBOL_OVERLAP":"OTHER";
        categories.merge(category,1,Integer::sum);
        println("FRESH_C_WARNING function="+fn.getEntryPoint()+" category="+
          category+" text="+line.trim());
      }
      if(line.contains("__ghidra_unresolved_indirect_jump(")){indirect++;unresolved++;}
    }
    if(warnings>0||indirect>0)println("FRESH_C_GAP function="+fn.getEntryPoint()+
      " warnings="+warnings+" indirect="+indirect);
   }
  } finally {dc.dispose();}
  println("FRESH_C_TOPOLOGY native="+checked+" C_ok="+successes+" warning_lines="+warningLines+
    " unsupported_C="+bad+" unresolved_indirect="+unresolved+" warnings_by_type="+categories);
  if(currentProgram.isChanged()||currentProgram.getDomainFile().getVersion()!=before)
     throw new IllegalStateException("Read-only Analyzer C pass changed saved project");
 }
}
