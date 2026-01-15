import lldb

path_filter=""
trace_output_file=""

def crash_hook(debugger, command, result, internal_dict):
  target = debugger.GetSelectedTarget()
  process = target.GetProcess()

  for thread in process:
    if thread.GetStopReason() == lldb.eStopReasonSignal:
      signal_number = thread.GetStopReasonDataAtIndex(0)
      if signal_number == 11 or signal_number == 6:  # SIGSEGV or SIGABRT
        result.PutCString("\n!!! SIGSEGV or SIGABRT detected !!!\n")

        with open(trace_output_file, 'a') as f:
          frame_counter = 0
          for fidx in thread:
            func_name = frame.GetFunctionName()
            if not func_name:
                sym = frame.GetSymbol()
                func_name = sym.GetName() if sym.IsValid() else "<no function>"
            print(func_name)

            le = fidx.GetLineEntry()
            fs = le.GetFileSpec()
            
            # if fs and fs.GetDirectory() and path_filter in fs.GetDirectory():
            f.write(f"{fs.GetDirectory()}/{fs.GetFilename()}:{le.GetLine()}\n")
            frame_counter += 1

            # Save at most 5 most recent frames
            if frame_counter == 5:
              break

        result.SetStatus(lldb.eReturnStatusSuccessFinishResult)

  debugger.HandleCommand("continue")