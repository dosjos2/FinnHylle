# Billyjakt

Billyjakt er en liten, lokal webapp som finner brukte Billy-hyller på FINN i Oslo og Akershus. Den henter søketreff med FINNs filtre for minst 200 cm høyde og 80 cm bredde, leser annonsene og viser resultatene i en liste og på et kart.

## Funksjoner

- Søker etter «billy hylle» i Oslo og Akershus med FINNs kategori- og målfiltre.
- Viser tittel, pris, sted, antall, annonsealder og estimert avstand fra Bjerke.
- Plasserer annonser med tilgjengelige koordinater på et Leaflet-kart med OpenStreetMap-kartfliser.
- Sorterer etter anbefalt rekkefølge, annonsealder, pris eller avstand.
- Lar deg skjule annonser som ikke er aktuelle. Skjulte annonser lagres i nettleserens lokale lagring og kan vises igjen.
- Strømmer treffene inn mens annonsene leses, i stedet for å vente på at hele søket blir ferdig.

## Krav

- Python 3. Ingen ekstra Python-pakker er nødvendige.
- Internettforbindelse for FINN-søket og kartflisene fra OpenStreetMap.
- En moderne nettleser med JavaScript aktivert.

## Kjør lokalt

Åpne en terminal i prosjektmappen og start den innebygde Python-serveren:

```powershell
python server.py
```

Åpne deretter [http://localhost:8000](http://localhost:8000) i nettleseren. Appen starter søket automatisk. Trykk **Oppdater søk** for å hente treff på nytt. Stopp serveren med `Ctrl+C` i terminalen.

På systemer der Python 3 startes med `python3`, bruk:

```sh
python3 server.py
```

Serveren lytter kun på `127.0.0.1:8000`, så den er beregnet for bruk på din egen maskin.

## Prosjektfiler

- `server.py` – lokal HTTP-server og API-et som henter søketreff og annonsedata fra FINN.
- `index.html` – sidens struktur.
- `app.js` – søkeflyt, resultatkort, sortering, skjuling og kart.
- `style.css` – utseende og responsiv layout.

## Datakilder og begrensninger

FINN kan endre HTML-strukturen sin. Hvis det skjer, kan appen vise en feilmelding eller unnlate å lese enkelte annonser. Data som ikke er tilgjengelig i annonsen, for eksempel koordinater eller alder, vises som ukjent. Avstandene er rettlinjede estimater fra Bjerke, ikke reiseavstander. Kontroller alltid mål og opplysninger i den opprinnelige annonsen før kjøp.

Appen logger ikke inn på FINN og forsøker ikke å omgå tilgangskontroller. Den leser maksimalt én annonse per sekund. Kartet bruker OpenStreetMap; behold nettleserens Referer-header og caching aktivert.
