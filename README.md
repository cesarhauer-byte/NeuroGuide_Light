# NeuroGuide Light

Neuropsykologiskt beslutsstöd – demo/testversion.  
Utvecklad vid Geriatriskt Centrum, NUS Umeå.

## Innehåller
- RAVLT, BVMT-R, TMT-A/B, WAIS-IV deltester (Blockmönster, Kodning, Likheter, Information, Sifferrepetition)
- RCFT, Klocktest (Shulman & Rouleau)
- Normering med T-poäng (Espenes 2023, Benedict 1997, Meyers 1995, Tombaugh 2004, m.fl.)
- Profiltolkning och spindeldiagram
- Bilddiagnostik (MTA, GCA, Koedam, Fazekas)
- Korrelationsmatris och topologisk 3D-graf
- Differentialdiagnostisk profil (17 demenssjukdomar)
- Utskriftsprofil med manuell redigering

## OBS
Denna version innehåller ingen patientdata.  
För kliniskt bruk – kontakta NUS Umeå.

## Starta lokalt

```bash
cd C:\NeuroGuide_Light
python app.py
```

Öppnas på `http://127.0.0.1:5010`

## Deploy på Render.com

1. Pusha koden till ett GitHub-repo
2. Skapa ett nytt **Web Service** på [render.com](https://render.com)
3. Koppla GitHub-repot
4. Render känner automatiskt igen `render.yaml`

Databaser (matris.db, diagnos_matris.db) skapas automatiskt vid första uppstart.

## Normkällor
- TMT: Tombaugh 2004
- RAVLT: Espenes et al. 2023, The Clinical Neuropsychologist 37(6):1276-1301
- BVMT-R: Benedict 1997
- WAIS-IV: Geriatriskt Centrums rättningsprogram (svenska normer)
- Ordflöde: Tallberg et al. 2008
- RCFT: Meyers & Meyers 1995
- Klocktest: Shulman 2000, Rouleau et al. 1992
