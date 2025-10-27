# 🛰️ WaveNET Project

## Project Overview

**WaveNET** is an experimental anonymous mesh network designed to enable secure, decentralized communication between nodes using unconventional physical media such as audio signlas.

The project reimplements several layers of the OSI model combining low-level protocol design with application-level file sharing and IRC-based coordination.

WaveNET allows nodes to:
- Transmit data packets using sound via Raspberry Pi.
- Route messages across multiple nodes with dynamic and anonymous mesh routing.
- Share and retrieve files through an anonymous overlay network.
- Bridge the anonymous network with the clearnet through an IRC bot and server.

This project was developed in `Python` and GNU/Linux as operating system.

---
## System Architecture
### Layer 1 - Physical Layer
The physical medium for this network is audio. It will be managed by Raspberry Pi, referred to as the *Transmission Device* which acts as a network interface between two nodes, converting digital data into audio signals and vice versa.

**Requirements:**
- Maximun frame size: 128 bytes
- Implement checksum verification
- Support protocol versioning
- Assign a unique physical address (similar to a MAC address)
- Provide a library called `DispositivoWaveNET` to handle communication between the node and the Transmission Device
---
### Layer 2 & 3 - WaveNET Core
WaveNET is an anonymous mesh network, designed to transmit packets across multiple hops without revealing the origin, similar to the Tor network.

**Communication Channels:**
- Ethernet
- Wi-Fi 802.11x
- Transmission Device (audio-based link)

**Core Functionalities:**
- Negotiated routing (dynamic routing through the mesh network)
- Node directory service (discovery and registration of active nodes)
- Anonymous packet transmission
---
### Layer 4 - Application
#### WaveNET
WaveNET acts as an anonymous file-sharing network, allowing users to exchange files securely and privately over the mesh.

#### Clearnet

A Clearnet IRC server must also be implemented to bridge communications with WaveNET.

The server should host a bot responsible for:
- Communicating with the WaveNET network
- Republishing an index of available files on WaveNET

---
