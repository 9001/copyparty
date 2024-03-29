#!/usr/bin/env python3

import sys

sys.path.insert(0, ".")
cmd = sys.argv[1]

if cmd == "cpp":
    from copyparty.__main__ import main

    argv = ["__main__", "-vsrv::r:c,e2ds,e2ts"]
    main(argv=argv)

elif cmd == "test":
    from unittest import main

    argv = ["__main__", "discover", "-s", "tests"]
    main(module=None, argv=argv)

else:
    raise Exception()

# import dis; print(dis.dis(main))


# macos:
#   option1) python3.9 -m pip install --user -U vmprof==0.4.9
#   option2) python3.9 -m pip install --user -U https://github.com/vmprof/vmprof-python/archive/refs/heads/master.zip
#
# python -m vmprof -o prof --lines ./scripts/profile.py test

# linux: ~/.local/bin/vmprofshow prof tree | awk '$2>1{n=5} !n{next} 1;{n--} !n{print""}'
# macos: ~/Library/Python/3.9/bin/vmprofshow prof tree
#   win: %appdata%\..\Roaming\Python\Python39\Scripts\vmprofshow.exe prof tree
