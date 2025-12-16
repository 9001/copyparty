---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: '9001'

---

<!-- NOTE:
**please use english, or include an english translation.** aside from that,  
all of the below are optional, consider them as inspiration, delete and rewrite at will, thx md -->

### Describe the bug
a description of what the bug is

### To Reproduce
List of steps to reproduce the issue, or, if it's hard to reproduce, then at least a detailed explanation of what you did to run into it

### Expected behavior
a description of what you expected to happen

### Screenshots
if applicable, add screenshots to help explain your problem, such as the kickass crashpage :^)

### Server details (if you are using docker/podman)
remove the ones that are not relevant:
* **server OS / version:** 
* **how you're running copyparty:** (docker/podman/something-else)
* **docker image:** (variant, version, and arch if you know)
* **copyparty arguments and/or config-file:** 

### Server details (if you're NOT using docker/podman)
remove the ones that are not relevant:
* **server OS / version:** 
* **what copyparty did you grab:** (sfx/exe/pip/arch/...)
* **how you're running it:** (in a terminal, as a systemd-service, ...)
* run copyparty with `--version` and grab the last 3 lines (they start with `copyparty`, `CPython`, `sqlite`) and paste them below this line:
* **copyparty arguments and/or config-file:** 

### Client details
if the issue is possibly on the client-side, then mention some of the following:
* the device type and model: 
* OS version: 
* browser version: 

### The rest of the stack
if you are connecting directly to copyparty then that's cool, otherwise please mention everything else between copyparty and the browser (reverseproxy, tunnels, etc.)

### Server log
if the issue might be server-related, include everything that appears in the copyparty log during startup, and also anything else you think might be relevant

### Additional context
any other context about the problem here
