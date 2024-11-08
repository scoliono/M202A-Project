---
title: Project Proposal
type: docs
weight: 1
---

# Project Proposal

## 1. Motivation & Objective

We want to create peer-to-peer local ad-hoc file sharing software similar to bit torrent that multiple clients can use at once to deliver file updates to each other on the go, all without an internet connection.

## 2. State of the Art & Its Limitations

Currently, peer-to-peer file sharing protocols such as BitTorrent do exist, which chunks files and allows transfers from various peers at once [1]. Additonally, certain operating systems like Windows do support decentralized update delivery over LAN, through a feature called Delivery Optimization [2]. BitTorrent, though, requires a central server known as a tracker, meaning it is unusable without an internet connection [1]. Windows' Delivery Optimization requires a central router in order to discover peers over LAN. We wish to create a system that purely uses Bluetooth LE and Wi-Fi Direct to bypass the need altogether for an internet connection.

Apple AirDrop uses Bluetooth for advertisement and Wi-Fi to do peer-to-peer file transfers [3]. However, it only supports a single unidirectional connection between two devices at a time, and transfers files from start to finish rather than supporting partial chunks.

## 3. Novelty & Rationale

Our approach uses Bluetooth LE for peers to advertise which files and chunks are available for sharing, and then a Wi-Fi Direct connection between each pair of peers to do the actual file transfer. Therefore, no prior network infrastructure is required at all, and devices consume minimal power when not actively transferring files. We believe this idea has a good chance of succeeding because it builds on top of the P2P file sharing aspect of BitTorrent, while using the mesh topology that has seen widespread adoption in enterprise and home networks today.

## 4. Potential Impact

From a technical standpoint, if our project is successful, it would greatly reduce cloud computing operating costs for tech companies because most people wouldn't need to download their files directly from the companies' CDNs, so less bandwidth would be used. By taking some of the most data-consuming file transfers offline, widespread adoption of this technology would significantly reduce network congestion around the globe.

Speaking more broadly, though, our project would make technology more accessible to those in disadvantaged areas without a reliable internet connection. In certain parts of the U.S. such as Detroit, entire neighborhoods still lack high-speed internet access, and therefore the only option for receiving device updates at a reasonable speed without traveling is to download them from someone else. The proliferation of peer-to-peer mesh networks could also help disseminate information among those who live under oppressive governments. In Cuba, for example, nearly no one has access to the internet, and they distribute American media by smuggling USB drives into the country and passing around copies. With a multi-hop mesh network like ours, information could spread over a much larger area more quickly, and its decentralized nature makes it resistant to government censorship.

## 5. Challenges

Due to the wireless nature of this project, real-world tests could be negatively impacted by interference from other devices within range, especially in densely populated areas.

One challenge that we anticipate is the differences in penetration between a 2.4GHz Bluetooth signal and a 5GHz Wi-Fi signal. This could lead to a situation where two clients are able to advertise their metadata to each other, but then can't initiate the actual file transfer. This issue might be prevented by temporarily blacklisting peers which might be detectable over Bluetooth but fail to connect over Wi-Fi.

Also, the question of managing multiple peer connections simultaneously could present a challenge. It may not be possible to run multiple Wi-Fi Direct connections at the same time, meaning that a client might have to use time-division multiplexing to switch between them. If it is possible, the question remains if we should put each connection on a separate thread, or run on a single thread with coroutines, since there could potentially be thread-unsafe resources at play.

As for real-world security risks, there is a possibility of a peer "poisoning" the file chunks it transfers to other peers without a central source of truth to provide trustworthy checksums. This is a complex problem that we will not consider for the scope of this project. We also do not plan to use encryption between peers in our implementation, so the packets transferred could be sniffed by a third party.

## 6. Requirements for Success

Knowledge of the Bluetooth LE and Wi-Fi Direct protocols is necessary. The code will be written in Python, so knowledge of that language is assumed. In terms of hardware, the code should be able to run on any device supporting the aforementioned wireless protocols, but we are using 3 of Raspberry Pi Zero 2 Ws because they are cheap. Power banks are also necessary in order to do real-world on-the-go testing.

## 7. Metrics of Success

Several metrics of success that we would consider include: average file transfer speed, file trasnfer speed to flood a network, maximum number of connectable peers, power consumption when idle (not yet connected to a peer), power consumption while a file transfer is in progress, and maximum range from which a file can be successfully transferred between peers. Ideally, all of the metrics will be high except power consumption, which should be just a couple hundred milliwatts because we are using low-power devices with the Bluetooth Low Energy protocol.

## 8. Execution Plan

Describe the key tasks in executing your project, and in case of team project describe how will you partition the tasks.


For the midterm presentation, our goal is to just get two devices to advertise file chunk metadata to each other and initiate a Wi-Fi Direct connection.

The main execution steps are as follows:

1. Test BLE connection between 2 Raspberry Pis
2. test Wifi Direct between 2 Raspberry Pis
3. Develop a protocol for advertising which files, chunks, and versions a device has over BLE.
4. Implement that protocol
5. Implement the Wifi Direct handshake and file trasnfer of chunks.
6. Test the full system.


## 9. Related Work

### 9.a. Papers

List the key papers that you have identified relating to your project idea, and describe how they related to your project. Provide references (with full citation in the References section below).

### 9.b. Datasets

List datasets that you have identified and plan to use. Provide references (with full citation in the References section below).

### 9.c. Software

List softwate that you have identified and plan to use. Provide references (with full citation in the References section below).

1. bleak: Scanning & Connecting [4]
2. BlueZ’s D-Bus API: BLE Advertising [5]
3. Wifi Direct [6]

## 10. References

List references correspondign to citations in your text above. For papers please include full citation and URL. For datasets and software include name and URL.

[1] https://en.wikibooks.org/wiki/The_World_of_Peer-to-Peer_(P2P)/Networks_and_Protocols/BitTorrent

[2] https://learn.microsoft.com/en-us/windows/deployment/do/waas-delivery-optimization

[3] https://www.xda-developers.com/airdrop/

[4] https://github.com/hbldh/bleak

[5] https://www.bluez.org/

[6] https://www.wi-fi.org/discover-wi-fi/wi-fi-direct