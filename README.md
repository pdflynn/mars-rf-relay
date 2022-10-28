# mars-rf-relay

RF relay using software defined radio intended for use on Ingenuity autonomous helicopter drone. Part of ECE 4805-4806, Major Design Experience, in Spring/Fall 2022.
This repository holds all of the software as well as the GNU Radio flowgraphs. The flowgraphs are heavily based on examples from the gr-ieee802-11 out of tree module.

# Transmitter Flowgraph

![TXFlowgraph](https://raw.githubusercontent.com/pdflynn/mars-rf-relay/main/interactive_wifi_tx.png)

# Receiver Flowgraph

![RXFlowgraph](https://raw.githubusercontent.com/pdflynn/mars-rf-relay/main/interactive_wifi_rx.png)

# AWGN Channel Testing Flowgraph

![LoopbackFlowgraph](https://raw.githubusercontent.com/pdflynn/mars-rf-relay/main/offline_loopback.png)

# dependencies

- GNU Radio 3.9
- gr-foo
- gr-ieee802-11
