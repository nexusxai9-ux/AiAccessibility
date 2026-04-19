import subprocess
import sys

# UI.py now acts as the master orchestrator and will dynamically launch 
# all the other modules and capture their terminal outputs into the UI text box.
if __name__ == "__main__":
    print("Launching Nexus UI...")
    subprocess.Popen([sys.executable, "UI.py"])