# Vision vs CAD — kaal metalen D-lus

Schaal overal: **1 vakje = 10 mm = 1 cm**.

Bronnen:
- Foto: `WhatsApp Image 2026-10-02 at 20.16.42.jpeg` (kaal metaal, geen tuinslang)
- Vision: Qwen3-VL via LM Studio → `vision_metal_loop.md`
- CAD: binnenovaal van de foto (`fitEllipse` op de papieren opening), staaf Ø 11.1 mm, omgerekend met gedetecteerde rasterafstand (~94 px / vakje)

| Onderdeel | Foto + raster (CAD) | Vision-model | Gelijk? |
|---|---|---|---|
| Silhouet | echte ovaal, gebogen lange zijden | echte ovaal, geen renbaan | ja |
| Buitenhoogte | **16.2 vakjes = 162 mm** | 14 vakjes = 140 mm | nee — vision telt te weinig vakjes |
| Buitenbreedte (zonder as) | **9.8 vakjes = 98 mm** | 8 vakjes = 80 mm | nee — vision smaller; CAD-ovaal ligt iets buiten de staaf |
| Staafdikte | **1.11 vakjes = 11.1 mm** (gemeten) | 1 vakje = 10 mm | bijna |
| Zeskant in bovenaanzicht | 6 zijden in het vlak van de lus, **~2.2 vakjes = 22 mm** over flats | 6 zijden, 3 vakjes = 30 mm | vorm ja, maat nee |
| Linkerbenen | lassen/knijpen **in** de zeskant | losse rail **naast** de hub, klink/stift | nee — vision verzint een spleet die op de foto niet zit |
| As | vierkant, **naar links** uit beeld | “verticaal 2 vakjes” | nee |
| Hub → rechterbuiten | ~5.5–6 vakjes (~57 mm, eerdere grid-meting) | 3 vakjes = 30 mm | nee |

## Wat we in CAD houden (foto + 1 cm-raster)

- Ovaal, geen renbaan.
- 1 vakje = 10 mm, geen extra stretch in X of Y.
- Zeskant als hexagon in XY op de linkerovaal.
- Vierkante asstub naar links.

## Wat we van vision weggooien

- 140 × 80 mm (te klein tegen het blad).
- Losse linkerrail naast de hub.
- Hub-tot-rechts 30 mm.
- Hex 30 mm over flats.
- As “verticaal”.

Overlay van de fit op de foto: `reference/calibrated/loop_trace_overlay.jpg` (groen = binnenovaal, oranje = staaf-centerlijn).
