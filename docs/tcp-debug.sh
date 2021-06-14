(cd ~/dev/copyparty && strace -Tttyyvfs 256 -o strace.strace python3 -um copyparty -i 127.0.0.1 --http-only --stackmon /dev/shm/cpps,10 ) 2>&1 | tee /dev/stderr > ~/log-copyparty-$(date +%Y-%m%d-%H%M%S).txt

14/Jun/2021:16:34:02 1623688447.212405 death
14/Jun/2021:16:35:02 1623688502.420860 back

tcpdump -nni lo -w /home/ed/lo.pcap

# 16:35:25.324662 IP 127.0.0.1.48632 > 127.0.0.1.3920: Flags [F.], seq 849, ack 544, win 359, options [nop,nop,TS val 809396796 ecr 809396796], length 0

tcpdump -nnr /home/ed/lo.pcap | awk '/ > 127.0.0.1.3920: /{sub(/ > .*/,"");sub(/.*\./,"");print}' | sort -n | uniq | while IFS= read -r port; do echo; tcpdump -nnr /home/ed/lo.pcap 2>/dev/null | grep -E "\.$port( > |: F)" | sed -r 's/ > .*, /, /'; done | grep -E '^16:35:0.*length [^0]' -C50

16:34:02.441732 IP 127.0.0.1.48638, length 0
16:34:02.441738 IP 127.0.0.1.3920, length 0
16:34:02.441744 IP 127.0.0.1.48638, length 0
16:34:02.441756 IP 127.0.0.1.48638, length 791
16:34:02.441759 IP 127.0.0.1.3920, length 0
16:35:02.445529 IP 127.0.0.1.48638, length 0
16:35:02.489194 IP 127.0.0.1.3920, length 0
16:35:02.515595 IP 127.0.0.1.3920, length 216
16:35:02.515600 IP 127.0.0.1.48638, length 0

grep 48638 "$(find ~ -maxdepth 1 -name log-copyparty-\*.txt | sort | tail -n 1)"

1623688502.510380 48638 rh
1623688502.511291 48638 Unrecv direct ...
1623688502.511827 48638 rh = 791
16:35:02.518 127.0.0.1 48638       shut(8): [Errno 107] Socket not connected
Exception in thread httpsrv-0.1-48638:

grep 48638 ~/dev/copyparty/strace.strace
14561 16:35:02.506310 <... accept4 resumed> {sa_family=AF_INET, sin_port=htons(48638), sin_addr=inet_addr("127.0.0.1")}, [16], SOCK_CLOEXEC) = 8<TCP:[127.0.0.1:3920->127.0.0.1:48638]> <0.000012>
15230 16:35:02.510725 write(1<pipe:[256639555]>, "1623688502.510380 48638 rh\n", 27 <unfinished ...>
