# transformer.py
import re
import pandas as pd


def transform_bordsbokning(excel_file) -> pd.DataFrame:
    """
    Läser Tickster-rapporten med placeringskort och returnerar en DataFrame
    med kolumnerna: Namn, antal, artiklar, bord, tid.

    - Namn  = värdet under kolumnen "Efternamn, Förnamn" (en rad per person/kund).
    - antal = 1 (en rad motsvarar en person / ett placeringskort).
    - artiklar = alla artiklar från blocket "Antal / Artikel", hopslagna till en sträng
                 som t.ex. "2st TOSCAMAZARIN 40kr, 1st KAFFE 35kr".
                 Antalet tas från kolumnen "Antal" och summeras per artikel.
    - bord = texten på raden som börjar med "Bord:" ovanför personerna.
    - tid  = "paus" om bordsnamnet innehåller ordet "paus" (skiftlägesokänsligt),
             annars "innan".
    """

    xls = pd.ExcelFile(excel_file)
    rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        nrows, ncols = df.shape

        # Leta efter alla celler som innehåller exakt "Efternamn, Förnamn"
        for r_name_header in range(nrows):
            for c in range(ncols):
                if str(df.iat[r_name_header, c]) != "Efternamn, Förnamn":
                    continue

                # 1) Hitta bordsrad ("Bord: ...") ovanför
                bord = ""
                for r in range(r_name_header - 1, -1, -1):
                    val = df.iat[r, c]
                    s = "" if pd.isna(val) else str(val)
                    if s.startswith("Bord:"):
                        bord = s
                        break

                # 2) Hämta alla namn-rader mellan "Efternamn, Förnamn" och raden med "X personer"
                guests = []
                r = r_name_header + 1
                while r < nrows:
                    val = df.iat[r, c]
                    s = "" if pd.isna(val) else str(val).strip()

                    if s == "":
                        r += 1
                        continue

                    # Stoppa när vi kommer till t.ex. "4 personer", "7 personer" etc.
                    if re.search(r"\bpersoner\b", s, flags=re.IGNORECASE):
                        break

                    guests.append(s)
                    r += 1

                # Om det inte fanns några individuella namn (bara t.ex. en grupp-rad),
                # använder vi sista icke-tomma raden innan "X personer" som "Namn".
                if not guests:
                    r = r_name_header + 1
                    last_nonempty = ""
                    while r < nrows:
                        val = df.iat[r, c]
                        s = "" if pd.isna(val) else str(val).strip()
                        if s == "":
                            r += 1
                            continue
                        if re.search(r"\bpersoner\b", s, flags=re.IGNORECASE):
                            break
                        last_nonempty = s
                        r += 1
                    if last_nonempty:
                        guests.append(last_nonempty)

                # 3) Hitta artikel-blocket: rad där det står "Antal" och "Artikel" bredvid varandra
                art_header_row = None
                for r in range(r_name_header + 1, nrows):
                    s1 = "" if pd.isna(df.iat[r, c]) else str(df.iat[r, c])
                    s2 = ""
                    if c + 1 < ncols:
                        v2 = df.iat[r, c + 1]
                        s2 = "" if pd.isna(v2) else str(v2)
                    if s1 == "Antal" and s2 == "Artikel":
                        art_header_row = r
                        break

                if art_header_row is None:
                    continue

                # 4) Läsa alla artiklar under headern och SUMMERA per artikel
                article_counts = {}   # artikel -> totalt antal (int)
                order = []            # för att behålla ursprungsordningen

                r = art_header_row + 1
                while r < nrows:
                    qty_val = df.iat[r, c]
                    art_val = df.iat[r, c + 1] if c + 1 < ncols else None

                    s_qty = "" if pd.isna(qty_val) else str(qty_val).strip()
                    s_art = "" if pd.isna(art_val) else str(art_val).strip()

                    # Om både antal och artikel är tomt -> slut på blocket
                    if s_art == "" and s_qty == "":
                        break

                    # Försök tolka antal
                    if s_art != "":
                        qty = 0
                        if s_qty != "":
                            num_txt = s_qty.replace(",", ".")
                            try:
                                qty = int(float(num_txt))
                            except ValueError:
                                qty = 0

                        if s_art not in article_counts:
                            article_counts[s_art] = 0
                            order.append(s_art)
                        article_counts[s_art] += qty

                    r += 1

                # Bygg upp artiklar-strängen, t.ex. "2st TOSCAMAZARIN 40kr, 1st KAFFE 35kr"
                parts = []
                for art in order:
                    qty = article_counts.get(art, 0)
                    if qty <= 0:
                        continue
                    parts.append(f"{qty}st {art}")
                articles_str = ", ".join(parts)

                # 5) Bestäm "tid" baserat på bordsnamnet
                tid = "paus" if "paus" in bord.lower() else "innan"

                # 6) Lägg till en rad per gäst
                for guest in guests:
                    rows.append(
                        {
                            "Namn": guest,
                            "antal": 1,  # en rad per person/kort
                            "artiklar": articles_str,
                            "bord": bord,
                            "tid": tid,
                        }
                    )

    result = pd.DataFrame(rows, columns=["Namn", "antal", "artiklar", "bord", "tid"])
    return result

