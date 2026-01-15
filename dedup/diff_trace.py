import argparse
import lldb
import json

# ----------- Command-Line Arguments -----------
parser = argparse.ArgumentParser(description="LLDB instruction-level tracer with stdout match halt")
parser.add_argument("--program", required=True, help="Path to the compiled binary")
parser.add_argument("--args", default="", help="Quoted string of program arguments")
parser.add_argument("--target-output", required=True, help="String to look for in stdout")
parser.add_argument("--output", default="trace_output.json", help="Output file for instruction trace")
args = parser.parse_args()

PROGRAM_PATH = args.program
PROGRAM_ARGS = args.args.split()
TARGET_OUTPUT = args.target_output
TRACE_OUTPUT_FILE = args.output

# ----------- Initialize LLDB -----------
lldb.SBDebugger.Initialize()
debugger = lldb.SBDebugger.Create()
debugger.SetAsync(False)

target = debugger.CreateTargetWithFileAndArch(PROGRAM_PATH, lldb.LLDB_ARCH_DEFAULT)
if not target or not target.IsValid():
  print(f"Failed to create target: {PROGRAM_PATH}")
  exit(1)

# ----------- Set Breakpoint -----------
bp = target.BreakpointCreateByName("main")

# Fallback to entry address if "main" not found
if not bp.IsValid() or bp.GetNumLocations() == 0:
  print("'main' not found. Falling back to binary entry point...")
  module = target.GetModuleAtIndex(0)
  if not module or not module.IsValid():
      print("Failed to get module for binary.")
      exit(1)

  entry_addr = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
  bp = target.BreakpointCreateByAddress(entry_addr)

if not bp.IsValid() or bp.GetNumLocations() == 0:
  print("Could not set a valid breakpoint.")
  lldb.SBDebugger.Terminate()
  exit(1)

print(f"Breakpoint set at ID {bp.GetID()}")

# ----------- Launch Process -----------
launch_info = lldb.SBLaunchInfo(PROGRAM_ARGS)
launch_info.SetWorkingDirectory(".")
error = lldb.SBError()
process = target.Launch(launch_info, error)

if error.Fail():
  print("Launch failed:", error.GetCString())
  lldb.SBDebugger.Terminate()
  exit(1)
print(f"Launch successful. PID={process.GetProcessID()}")
print("Immediate process state:", lldb.SBDebugger.StateAsCString(process.GetState()))


# ----------- Wait for Breakpoint Hit -----------
while True:
  if process.GetState() == lldb.eStateStopped:
    print("Hit breakpoint. Starting instruction trace...")
    break
  else:
    print("Process not in stopped state. Current state:", lldb.SBDebugger.StateAsCString(process.GetState()))
    lldb.SBDebugger.Terminate()
    exit(1)

# print("Hit breakpoint. Starting instruction trace...")

# ----------- Begin Instruction-Level Trace -----------
trace = []
stdout_collected = ""

while process.IsValid() and process.GetState() != lldb.eStateExited:
  thread = process.GetSelectedThread()
  if not thread.IsValid():
      break

  frame = thread.GetSelectedFrame()
  module = frame.GetModule()
  
  filename = module.GetFileSpec().GetFilename()
  if not filename or PROGRAM_PATH not in filename:
    thread.StepOver()
    continue

  fn = frame.GetFunctionName()
  file = frame.GetLineEntry().GetFileSpec().GetFilename()
  line = frame.GetLineEntry().GetLine()

  trace_line = f"{fn} - {file}:{line}"
  trace.append(trace_line)

  output = process.GetSTDOUT(4096)
  if output:
    stdout_collected += output
    if TARGET_OUTPUT in stdout_collected:
      print(f"Target output '{TARGET_OUTPUT}' detected. Stopping trace.")
      break

  # Step to next instruction
  thread.StepInstruction(False)

# ----------- Dump to Output File -----------
with open(TRACE_OUTPUT_FILE, "w") as f:
  for line in trace:
    f.write(line)
    f.write("\n")

print(f"Trace complete. {len(trace)} instructions saved to '{TRACE_OUTPUT_FILE}'")

lldb.SBDebugger.Terminate()
