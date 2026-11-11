import sys

from .cli import main

# stdin is read as bytes (sys.stdin.buffer) and decoded strictly, so no stdin
# reconfiguration is needed. stdout/stderr: UTF-8 and no CRLF translation, so
# stderr is exactly "<CODE>\n" on every platform.
sys.stdout.reconfigure(encoding="utf-8", newline="\n")
sys.stderr.reconfigure(encoding="utf-8", newline="\n")
sys.exit(main())
