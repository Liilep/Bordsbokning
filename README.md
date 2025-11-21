# Bordsboknings-omvandlare (Tickster)

Ett litet webbaserat verktyg (Streamlit) som läser Ticksters placeringskorts-rapport
i Excel och skriver ut en ny fil med kolumnerna:

- `Namn`   – hämtas från kolumnen **"Efternamn, Förnamn"**
- `antal`  – alltid `1` (en rad per person / placeringskort)
- `artiklar` – alla artiklar i blocket **"Antal / Artikel"** summerade per artikel,
  t.ex. `2st TOSCAMAZARIN 40kr, 1st KAFFE 35kr`
- `bord`  – raden som börjar med `"Bord:"` ovanför namnen
- `tid`   – `"paus"` om bordsnamnet innehåller `paus`, annars `"innan"`

## Installation

1. Klona detta repo:

   ```bash
   git clone <URL-till-ditt-repo>
   cd <mappen>

