import re
import pandas as pd


def cell_str(val) -> str:
    """Hjälpfunktion: gör om cell till sträng, tom om NaN/None."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def transform_bordsbokning(excel_file) -> pd.DataFrame:
    """
    Läser Ticksters placeringskorts-rapport och returnerar en DataFrame med:

    - Namn    : ett namn per placeringskort (mellan 'Bord:' och '... personer')
    - antal   : alltid 1 (en rad per placeringskort)
    - artiklar: summerade artiklar per bord, t.ex. '4st Vuxen, 2st KAFFE 35kr'
    - bord    : text som börjar med 'Bord:'
    - tid     : 'paus' om bordsnamnet innehåller 'paus', annars 'innan'
    """

    # excel_file kan vara antingen filstig (str) eller en fil-liknande stream (Streamlit-upload)
    xls = pd.ExcelFile(excel_file)
    rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        nrows, ncols = df.shape

        # Leta efter alla "Antal" / "Artikel"-block i arket
        for r in range(nrows):
            for c in range(ncols - 1):
                v_ant = cell_str(df.iat[r, c])
                v_art = cell_str(df.iat[r, c + 1])

                if v_ant != "Antal" or v_art != "Artikel":
                    continue

                header_row = r
                col_ant = c
                col_art = c + 1

                # 1) Hitta raden med "X personer" ovanför headern i samma kolumn
                persons_row = None
                for rr in range(header_row - 1, -1, -1):
                    s = cell_str(df.iat[rr, col_ant])
                    if not s:
                        continue
                    if re.search(r"\bpersoner\b", s, flags=re.IGNORECASE):
                        persons_row = rr
                        break

                if persons_row is None:
                    # Hittade inget "X personer" -> hoppa över blocket
                    continue

                # 2) Hitta bordsrad ("Bord: ...") ovanför persons_row
                bord = None
                for rr in range(persons_row - 1, -1, -1):
                    s = cell_str(df.iat[rr, col_ant])
                    if s.startswith("Bord:"):
                        bord = s
                        break

                if bord is None:
                    continue

                # 3) Hitta namnet mellan "Bord:" och "X personer"
                namn = None
                for rr in range(persons_row - 1, -1, -1):
                    s = cell_str(df.iat[rr, col_ant])
                    if not s:
                        continue
                    if s.startswith("Bord:"):
                        # Då har vi kommit upp till bordsraden – sluta leta
                        break
                    # Ett namn ser ut som "Efternamn, Förnamn"
                    if "," in s:
                        namn = s
                        break

                if not namn:
                    # Om inget namn hittas för detta bord/placering hoppar vi över blocket
                    continue

                # 4) Läs artiklarna under "Antal/Artikel"-headern och summera per artikel
                article_counts = {}
                order = []

                rr = header_row + 1
                while rr < nrows:
                    s_qty = cell_str(df.iat[rr, col_ant])
                    s_art = cell_str(df.iat[rr, col_art])

                    # Stoppa när både antal och artikel är tomma
                    if not s_qty and not s_art:
                        break

                    if s_art:
                        qty = 0
                        if s_qty:
                            txt = s_qty.replace(",", ".")
                            try:
                                qty = int(float(txt))
                            except ValueError:
                                qty = 0

                        if s_art not in article_counts:
                            article_counts[s_art] = 0
                            order.append(s_art)
                        article_counts[s_art] += qty

                    rr += 1

                # Bygg artikelsträngen: "4st Vuxen, 2st KAFFE 35kr"
                parts = []
                for art in order:
                    qty = article_counts.get(art, 0)
                    if qty > 0:
                        parts.append(f"{qty}st {art}")
                artiklar_str = ", ".join(parts)

                # 5) Bestäm tid: "paus" eller "innan"
                tid = "paus" if "paus" in bord.lower() else "innan"

                # 6) Lägg till en rad i resultatet
                rows.append(
                    {
                        "Namn": namn,
                        "antal": 1,
                        "artiklar": artiklar_str,
                        "bord": bord,
                        "tid": tid,
                    }
                )

    result = pd.DataFrame(rows, columns=["Namn", "antal", "artiklar", "bord", "tid"])
    return result
