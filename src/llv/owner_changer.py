import subprocess

pfad = r"C:\Users\mschulz\Pictures\boom.png"
new_owner = r"EDER\breum"

# /grant:r remappt existing ACLs, /setowner setzt nur den Owner
res = subprocess.run([
    "icacls", pfad,
    "/setowner", new_owner,
    
], capture_output=True, text=True)

print(res.stdout)
if res.returncode != 0:
    print("Fehler:", res.stderr)
