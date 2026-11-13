---
id: transport-tracking-aircraft-ship-aprs
category: OSINT
tags: [osint, aircraft, flight, tail-number, registration, ads-b, ship, vessel, ais, imo, mmsi, aprs, callsign, ham-radio, container]
tools: []
manuals: []
title: "OSINT: identify and track an aircraft, ship, container or ham-radio station"
difficulty: medium
created: 2026-11-13
updated: 2026-11-13
related: [image-geolocation-exif, afsk-bell202-audio-demodulation]
toolsets: [osint/transport, osint/geo-maps]
---

## How to recognize this pattern

- A photo shows a plane (tail number like `N123AB`, `PR-XYZ`, `G-ABCD`), a ship (name, IMO on the
  hull), or a container (4-letter owner prefix + digits, e.g. `MSCU1234567`).
- The prompt gives a flight number, IMO/MMSI, or an amateur-radio callsign (`PY2ABC`, `W1AW-9`).
- "Where was this vehicle at date X?" or "what is the name of the operator/owner?"

## Method

1. **Identify the object** from the visible ID:
   - Aircraft registration prefix gives the country (N = USA, PR/PP/PT = Brazil, G = UK).
     Flightradar24 `data/aircraft/<reg>` gives type, operator, photos and recent flights.
   - Ship: IMO (7 digits, permanent) beats the name (ships get renamed). VesselFinder/MarineTraffic.
   - Container: the first 4 letters are the owner code, looked up on BIC.
   - Callsign: `aprs.fi/info/a/<callsign>` gives last position, path and history.
2. **Place it in time**: flight playback (Flightradar24/FlightAware history), AIS port calls,
   APRS track. Free tiers keep about 7 days of history; older data needs another clue.
3. **Combine with the photo**: livery and airport stand, port cranes, weather and sun
   (`--toolset osint/geo-maps`: SunCalc, timeanddate historical weather).

```bash
python3 scripts/arsenal_search.py --tools "<registration | imo | callsign | container>" --top 3
```

## Gotchas

- Military and blocked (LADD/PIA) aircraft don't appear on commercial trackers.
- The MMSI changes when the flag changes; the IMO doesn't.
- APRS SSIDs (`-9` mobile, `-7` handheld) are different stations of the same operator.
- APRS packets can also come as audio: decode first with `afsk-bell202-audio-demodulation`.

## Cross-reference

- `image-geolocation-exif`: for the surrounding scene.
- `afsk-bell202-audio-demodulation` (MISC): when the APRS data arrives as a WAV.
