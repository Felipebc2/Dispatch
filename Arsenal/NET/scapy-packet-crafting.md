---
id: scapy-packet-crafting
category: NET
tags: [net, scapy, packet-crafting, sniff, arp, icmp, raw-socket, replay, protocolo-binario, sr1, send]
tools: []
manuals: []
title: "NET: craft/replay packets with scapy"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [custom-tcp-service-scripting]
---

## How to recognize this pattern

- The challenge isn't a text service over TCP (that's `custom-tcp-service-scripting`), but rather
  **packet manipulation**: forging a header, responding to a custom binary protocol, ARP/ICMP, or
  replaying/altering packets from a `.pcap`.
- The prompt talks about "send the right packet", "the server responds to its own protocol", specific TCP
  flags, or hands you a pcap to reproduce/modify.

## Method

### 1. Understand the protocol (from the pcap, if there is one)
```python
from scapy.all import *
pkts = rdpcap("captura.pcap")
pkts[0].show()                 # dissect the layers
pkts[0][Raw].load              # raw payload to find the format
```

### 2. Craft and send
```python
from scapy.all import *
# L3/L4: request-response (sr1 = send & receive 1)
resp = sr1(IP(dst="10.0.0.1")/TCP(dport=1337, flags="S"), timeout=2)   # SYN scan/handshake
resp = sr1(IP(dst="alvo")/ICMP()/Raw(load=b"ping-payload"))
# custom protocol over UDP:
resp = sr1(IP(dst="alvo")/UDP(dport=9999)/Raw(load=b"\x01\x02flag?"))
resp.show()
```

### 3. L2 / ARP / replay
```python
send(ARP(op=2, pdst="victim", hwdst="...", psrc="gateway"))   # ARP spoof
sendp(Ether()/IP()/..., iface="eth0")                          # L2 injection
sendp(rdpcap("captura.pcap"), iface="eth0")                    # replay the whole pcap
sniff(filter="udp port 9999", prn=lambda p: p.summary(), count=10)
```

## Gotchas

- `send` (L3, uses the OS routing) vs `sendp` (L2, you build the Ether and pick `iface`). ARP/L2
  requires `sendp`.
- Raw socket/`sniff`/`sendp` need **root** (`sudo`) or capabilities. Run with privilege.
- Checksums: let scapy recompute them (don't set `chksum` by hand). Setting it wrong makes the target
  drop the packet silently.
- If the target is just "send bytes X and get the flag" over a text TCP, scapy is overkill → use
  `custom-tcp-service-scripting` (pwntools/nc), which is simpler.

## Cross-reference

- `custom-tcp-service-scripting`: text/line service over TCP (pwntools remote), more common.
- Analyzing the pcap itself (extracting files/credentials) → `pcap-extract-credentials-files` (FOR).
