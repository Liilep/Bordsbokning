# transformer.py
import re
import pandas as pd


def transform_bordsbokning(excel_file) -> pd.DataFrame:
    """
    Läser Tickster-rapporten och returnerar en DataFrame
    med kolumnerna: Namn, antal, artiklar, bord, tid.
    """

    xls = pd.ExcelFile(excel_file)
    rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        nrows, ncols = df.shape

        for r in range(nrows):

            # Leta efter "Bord:"
            cell = str(df.iat[r, 0]) if not pd.isna(df.iat[r, 0]) else ""
            if not cell.startswith("Bord:"):
                continue

            bord = cell

            # 1) Hitta NAMNET (exakt 1 namn)
            namn = None
            rr = r + 1
            while rr < nrows:
                val = df.iat[rr, 0]
                s = "" if pd.isna(val) else str(val).strip()

                if s == "":
                    rr += 1
                    continue

                # Stoppa vid "X personer"
                if re.search(r"\bpersoner\b", s, flags=re.IGNORECASE):
                    break

                # Namn måste innehålla ett komma: "Efternamn, Förnamn"
                if "," in s:
                    namn = s
                    break

                rr += 1

            # Om inget namn hittats hoppar vi över denna sektion
            if not namn:
                continue

            # 2) Hitta artikel-header ("Antal" + "Artikel")
            art_header = None
            for rr2 in range(r + 1, nrows):
                col0 = "" if pd.isna(df.iat[rr2, 0]) else str(df.iat[rr2, 0])
                col1 = "" if (pd.isna(df.iat[rr2, 1]) if 1 >= ncols else True) else str(df.iat[rr2, 1])

                if col0 == "Antal" and col1 == "Artikel":
                    art_header = rr2
                    break

            if art_header is None:
                continue

            # 3) Läs artiklarna under headern och summera
            article_counts = {}
            order = []

            rr3 = art_header + 1
            while rr3 < nrows:

                qty_val = df.iat[rr3, 0]
                art_val = df.iat[rr3, 1] if 1 < ncols else None

                s_qty = "" if pd.isna(qty_val) else str(qty_val).strip()
                s_art = "" if pd.isna(art_val) else str(art_val).strip()

                # Stopp: båda tomma
                if s_art == "" and s_qty == "":
                    break

                if s_art != "":
                    # tolka antal
                    qty = 0
                    if s_qty != "":
                        try:
                            qty = int(float(s_qty.replace(",", ".")))
                        except:
                            qty = 0

                    if s_art not in article_counts:
                        article_counts[s_art] = 0
                        order.append(s_art)
                    article_counts[s_art] += qty

                rr3 += 1

            # 4) Bygg artikelsträngen
            artiklar_str = ", ".join(f"{article_counts[a]}st {a}" for a in order)

            # 5) Paus/innan
            tid = "paus" if "paus" in bord.lower() else "innan"

            # 6) Lägg till raden
            rows.append({
                "Namn": namn,
                "antal": 1,
                "artiklar": artiklar_str,
                "bord": bord,
                "tid": tid
            })

    return pd.DataFrame(rows)
