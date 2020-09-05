import subprocess
import sys
from time import sleep

print('keeping alive')
CONTINUE_CODE = 4
while True:
    status = subprocess.run([sys.executable, 'serverweb.py'] + sys.argv[1:])
    print('return code:', status.returncode)
    if status.returncode != CONTINUE_CODE:
        break
    sleep(1)
