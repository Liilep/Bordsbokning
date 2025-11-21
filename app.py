# app.py
import io
import datetime
import streamlit as st
from transformer import transform_bordsbokning
import pandas as pd


st.set_page_config(
    page_title="Bordsbokning → Placeringskort-export",
    page_icon="🍽️",
    layout="centered",
)


st.title("Bordsboknings-omvandlare 🍽️")
st.write(
    "Ladda upp Ticksters Excelrapport med placeringskort, så får du en ny fil "
    "med kolumnerna **Namn, antal, artiklar, bord, tid**."
)


uploaded_file = st.file_uploader(
    "Ladda upp rapport (.xlsx)", type=["xlsx"], accept_multiple_files=False
)

if uploaded_file is not None:
    st.info("Fil uppladdad. Klicka på knappen nedan för att omvandla.")
    if st.button("Omvandla rapport"):
        try:
            # Kör transformationen
            df_result = transform_bordsbokning(uploaded_file)

            if df_result.empty:
                st.warning(
                    "Inga rader kunde tolkas från filen. Kontrollera att strukturen "
                    "är samma som i Ticksters placeringskortsrapport."
                )
            else:
                st.success(f"Klart! Hittade {len(df_result)} rader. ✅")

                # Visa en förhandsvisning
                st.subheader("Förhandsvisning")
                st.dataframe(df_result.head(50))

                # Skapa Excel i minnet för nedladdning
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_result.to_excel(writer, index=False, sheet_name="Omstrukturerad")

                output.seek(0)

                today_str = datetime.date.today().isoformat()
                filename = f"omstrukturerad_bordsbokning_{today_str}.xlsx"

                st.download_button(
                    label="⬇️ Ladda ner omstrukturerad fil",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as e:
            st.error(
                "Något gick fel när filen skulle läsas eller tolkas.\n\n"
                f"Teknisk detalj: {e}"
            )
else:
    st.caption("Välj en .xlsx-fil ovan för att komma igång.")

