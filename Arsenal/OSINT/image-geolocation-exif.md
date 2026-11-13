---
id: image-geolocation-exif
category: OSINT
tags: [osint, geolocation, geolocalizacao, exif, gps, reverse-image, exiftool, landmark, placa, shadow, metadados]
tools: []
manuals: []
title: "OSINT: geolocate a photo (EXIF + reverse image + visual clues)"
difficulty: medium
created: 2026-10-04
updated: 2026-11-13
related: [social-media-scraping-playwright, transport-tracking-aircraft-ship-aprs]
toolsets: [osint/image-reverse, osint/geo-maps]
---

## How to recognize this pattern

- The challenge gives a photo and asks "where was it taken?", the name of the place, the city, the
  coordinates, or the flag is derived from the location (street/building name).
- Also: find who/which account posted a given image, or the date/time.

## Method

### 1. Metadata first (free, often solves it)
```bash
exiftool foto.jpg | grep -iE 'gps|date|model|software|location'
# GPS present → coordinates directly → paste into Google Maps/OpenStreetMap
strings foto.jpg | grep -iE 'hik_|http|@'      # embedded comment/URL
```

### 2. Reverse image search (when there's no EXIF)
- **Yandex** (best for places/faces), **Google Lens**, **Bing Visual**, TinEye.
- Crop just the distinctive point (facade, sign, logo) and search the crop. This cuts the noise.

### 3. Visual clues (manual analysis)
- **Text/language** on signs, billboards → country/region; direction of traffic (left-hand drive?).
- **License plate** (format/color), type of lamppost/traffic light, fire hydrant, taxi.
- **Landmark/architecture** → reverse image of the landmark.
- **Shadow + time** → sun direction (hemisphere, orientation). Vegetation/climate → latitude.
- Cross-check with **Google Street View / Maps** to confirm the exact spot.

## Gotchas

- Social networks **strip EXIF** on upload. If the photo came from Instagram/Twitter, skip to step 2/3.
- EXIF GPS can be a decoy/wrong. Confirm with an independent visual clue.
- Reverse image fails on a "clean" photo with no landmark; then it's 100% visual clue + Street View.
- Mind the flag format: the location may just be the means. Validate the flag against the CTF's
  configured flag format before declaring success.

## Cross-reference

- `social-media-scraping-playwright`: when you need to find the source account/post of the image.
- EXIF of an image in a FOR/stego challenge → `file-carving-signature-repair` / `lsb-image-steganography`.
