# CLAUDE.md – NeuroGuide Light

## Vad är detta?

**NeuroGuide Light** är en renodlad neuropsykologisk testversion av NeuroGuide NUS.
Körs på port **5010** för att inte krocka med huvudversionen (port 5002).

**Ingen AI, ingen Ollama, ingen läkemedelsmodul, ingen neurologisk undersökning,
ingen nutrition, ingen fysioterapi, ingen arbetsterapi, ingen BrainMap.**

## Starta applikationen

```
Dubbelklicka NeuroGuide_Light.bat
```
eller:
```powershell
cd C:\NeuroGuide_Light
python app.py
```
Öppnas på `http://127.0.0.1:5010`

## Mappstruktur

```
C:\NeuroGuide_Light\
  app.py                    ← Flask-backend, port 5010
  NeuroGuide_Light.bat      ← Startskript
  CLAUDE.md                 ← Denna fil
  patients_light.db         ← SQLite-databas (skapas automatiskt)
  templates\
    index.html              ← Enkelsidig frontend (5 sidor)
  modules\
    profiltolkning.py       ← Mönsterigenkänning (oförändrad från NeuroGuide)
```

## Arkitektur

### app.py – Flask-backend

**Normtabeller** (uppifrån i filen):
- `TMT_15B_NORM` – TMT A/B normer per åldersgrupp (15b Tabell 4.19 A-MSS)
- `_RAVLT_C` – Espenes et al. 2023 regressionskoefficienter
- `BVMT_NORMS` – (mean,sd) per åldersgrupp för total och DR
- `BLOCK_NORM`, `LIK_NORM`, `INFO_NORM`, `KOD_NORM` – WAIS-IV råpoäng→skalpoäng
- `SIFF_NORM_III` – WAIS-III normer (intentionellt)
- `FLODE_NORMS` – FAS/Djurnamn normer per utbildningsnivå
- `RCFT_NORMS` – Meyers & Meyers 1995, ålderskorrigerade (mean,sd)
- `KLOCKTEST_NORMS` – Cutoffs för Shulman och Rouleau-skalorna

**Konverteringsfunktioner:**
- `get_age_key()` – floor-matchning mot åldersnycklar
- `raw_to_scaled_wais()` – råpoäng→skalpoäng via tröskelvektor
- `tmt_to_ss()` – TMT-tid→skalpoäng (kortare tid = högre SS)
- `ss_to_t()` – SS→T med WAIS-IV formel: T=50+(SS-10)*(10/3)
- `scaled_to_t()` – WAIS skalpoäng→T (samma formel)
- `mean_sd_to_t()` – (raw-mean)/sd→T, begränsad [20,80]
- `t_color_label()` – T→(färg, etikett)

**Routes:**
| Route | Metod | Funktion |
|---|---|---|
| `/` | GET | Returnerar index.html |
| `/berakna` | POST | Beräknar T-poäng för alla test |
| `/profiltolkning` | POST | Mönsterigenkänning via profiltolkning.py |
| `/patient_spara` | POST | Sparar patientdata till patients_light.db |
| `/patient_lista` | GET | Listar alla sparade patienter |
| `/patient_hamta` | POST | Hämtar en patients data |
| `/patient_ny` | POST | Genererar nytt Patient-ID (NUS-YYYYMM-NNNN) |

### templates/index.html – Frontend

Fem sidor i sidomenyn:
1. **Patientuppgifter** – ID, födelsedata (→automatisk ålder), kön, testdatum, testledare, utbildningsår
2. **Neuropsykologiska test** – inmatning för alla test, [Beräkna T-poäng]-knapp, resultattabell
3. **Profiltolkning** – spindeldiagram (radar chart), mönsterpanel, textuell sammanfattning
4. **Bilddiagnostik** – MTA, GCA, Koedam, Fazekas-fält + automatisk tolkning + bilddiagnostik-spindel
5. **Sammanställning** – kombinerade diagram, full resultattabell, utskrift

**Spindeldiagram 1 (neuropsykologi):**
- 14 axlar: RAVLT total/DR, BVMT-R total/DR, RCFT fördröjd, TMT-A, TMT-B, Blockmönster, Kodning, Sifferrep, FAS, Djurnamn, Likheter, Information
- T-skala 20–80, referenslinjer vid T=40 (grå streckad) och T=35 (röd streckad)

**Spindeldiagram 2 (bilddiagnostik):**
- 5 axlar normaliserade 0–100%: MTA höger/vänster, GCA, Koedam, Fazekas
- Färgkodning: grön (<33%), orange (33–67%), röd (>67%)

**Utskriftslayout:**
- `@media print` döljer navigering och kontroller, visar bara sammanställningssidan
- Innehåller: patientinfo-header, resultattabell, spindeldiagram (inbäddade), profiltolkning, bilddiagnostiktolkning

## Neuropsykologiska test som ingår

- RAVLT (Trial 1–5, total, fördröjd ÅG, igenkänning)
- BVMT-R (Trial 1–3, total, fördröjd ÅG, igenkänning)
- RCFT (kopia, omedelbar ÅG, fördröjd ÅG 30 min, igenkänning)
- WAIS-IV: Blockmönster, Likheter, Information, Kodning
- Sifferrepetition framlänges/baklänges/ordningsföljd (WAIS-III normer)
- TMT-A och TMT-B med B/A-kvot
- FAS (F+A+S individuellt + total), Djurnamn
- Klocktest (Shulman 0–5 och Rouleau 0–10)
- Bilddiagnostik: MTA, GCA, Koedam, Fazekas

## Patientlagring

- `patients_light.db` – SQLite, tabell `patienter`
- Sparar JSON med patientinfo + testinmatning + bilddiagnostik + beräknade T-poäng
- Ingen kryptering, ingen lösenordsfunktion
- Patient-ID: format `NUS-YYYYMM-NNNN`

## Skillnader mot NeuroGuide NUS (huvudversion)

| Funktion | NeuroGuide NUS | NeuroGuide Light |
|---|---|---|
| Port | 5002 | 5010 |
| AI/Ollama | Ja | Nej |
| Läkemedel | Ja | Nej |
| Parkinsonanalys | Ja | Nej |
| FTD-analys | Ja | Nej |
| Neurologisk undersökning | Ja | Nej |
| Nutrition | Ja | Nej |
| Fysioterapi | Ja | Nej |
| Arbetsterapi | Ja | Nej |
| BrainMap | Ja | Nej |
| DNA-molekylen | Ja | Nej |
| RCFT-normer | Råvärden only | T-poäng (Meyers 1995) |
| Kryptering | Ja | Nej |

## Normkällor

- TMT: Tombaugh 2004, TMT 15b Tabell 4.19 A-MSS
- RAVLT: Espenes et al. 2023, The Clinical Neuropsychologist 37(6):1276-1301
- BVMT-R: Benedict 1997 (ålderskorrigerade)
- WAIS-IV: Geriatriskt Centrums Rättningsprogram, svenska normer
- WAIS-III Sifferrepetition: Wechsler 1997
- Ordflöde: Tallberg et al. 2008
- RCFT: Meyers & Meyers 1995, Professional Manual PAR Inc.
- Klocktest: Shulman 2000, Rouleau et al. 1992
