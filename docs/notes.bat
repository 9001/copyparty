rem appending a static ip to a dhcp nic on windows 10-1703 or later
netsh interface ipv4 show interface
netsh interface ipv4 set interface interface="Ethernet 2" dhcpstaticipcoexistence=enabled
netsh interface ipv4 add address "Ethernet 2" 10.1.2.4 255.255.255.0
