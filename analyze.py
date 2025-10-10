import os
import json
import locale
import streamlit as st
import pandas as pd
import plotly.express as px
from helper import Datenbundle, timer, create_hourly_bundles, create_weekly_bundles, create_monthly_bundles, load_and_transform_data


###########################################################################################
####           Start                                                                   ####
###########################################################################################

# Deutsche Monatsnamen etc...
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

st.set_page_config(page_title="Datenanalyse", page_icon="📊", layout="wide")

st.sidebar.header("Analyse")
st.sidebar.markdown('---')

st.title("Datenanalyse")

data_folder = "projects"
#json_files = sorted([f for f in os.listdir(data_folder) if f.endswith(".json")])

bundles = []
files = []
# List all subfolders (projects) in the data folder
project_folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]
if not project_folders:
    st.sidebar.subheader("⛓️‍💥 Projektauswahl")
    st.warning("No project folders found in the data folder.")
    st.stop()
else:
    project_folders = ["leer"] + project_folders
    st.sidebar.subheader("📁 Projektauswahl")
    selected_project = st.sidebar.selectbox("Wähle ein Projekt", project_folders, index=0)
    if selected_project == "leer":
        st.sidebar.subheader("⛓️‍💥 Datenauswahl")
        st.warning("Please select a project first.")
        st.stop()
    else:
        project_path = os.path.join(data_folder, selected_project)
        json_files = sorted([f for f in os.listdir(project_path) if f.endswith(".json")])
        data_folder = project_path

if not json_files:
    st.sidebar.subheader("⛓️‍💥 Datenauswahl")
    st.warning("No JSON files found in the data folder.")
else:
    st.sidebar.subheader("📂 Datenauswahl")
    json_files = ["leer"] + json_files
    selected_file = st.sidebar.selectbox("Wähle eine Datenreihe", json_files, index=0)
    if selected_file != "leer":
        json_files.remove(selected_file)
        files.append(selected_file)
    selected_file2 = st.sidebar.selectbox("Wähle eine zweite Datenreihe", json_files, index=0)
    if selected_file2 != "leer":
        json_files.remove(selected_file2)
        files.append(selected_file2)
    selected_file3 = st.sidebar.selectbox("Wähle eine dritte Datenreihe", json_files, index=0)
    if selected_file3 != "leer":
        files.append(selected_file3)

st.sidebar.markdown('---')
st.sidebar.subheader("🛠️ Optionen")
opt_clean_columns = st.sidebar.checkbox("Unnötige Spalten entfernen", value=True, help="Entfernt alle Spalten außer Datum/Uhrzeit und Wert")
opt_show_dataframe = st.sidebar.checkbox("Dataframes anzeigen", value=False)
opt_show_dataframe_infos = st.sidebar.checkbox("Dataframe Infos anzeigen", value=False)
opt_show_statistics = st.sidebar.checkbox("Statistiken anzeigen", value=True)
opt_calc = st.sidebar.checkbox("Berechnungen durchführen", value=False, help="Wenn Last und Erzeugung vorhanden sind, werden Eigenverbrauch, Einspeisung etc. berechnet")
opt_timer = st.sidebar.checkbox("Timer anzeigen", value=False)
options = {
    "clean_columns": opt_clean_columns,
    "show_dataframe": opt_show_dataframe,
    "show_dataframe_infos": opt_show_dataframe_infos,
    "calc": opt_calc,
    "timer": opt_timer
}

timer("", False)

for file in files:
    file_path = os.path.join(project_path, file) # type: ignore
    bundles.append(load_and_transform_data(file_path, options)) # type: ignore
    timer(f"{file} wurde geladen", opt_timer)




if len(bundles) > 0:

    # Prüfe, ob die Anzahl der Zeilen oder der erste Timestamp unterschiedlich ist
    row_counts = [bundle.df.shape[0] for bundle in bundles]
    first_timestamps = [bundle.df['datetime'].iloc[0] for bundle in bundles]

    if len(set(row_counts)) > 1:
        st.warning(f"Achtung: Die Anzahl der Zeilen unterscheidet sich zwischen den geladenen Datenreihen: {row_counts}")

    if len(set(first_timestamps)) > 1:
        st.warning(f"Achtung: Die Zeitstempel der geladenen Datenreihen sind unterschiedlich: {[ts.strftime('%Y-%m-%d %H:%M:%S') for ts in first_timestamps]}")

    bundles_hourly = create_hourly_bundles(bundles)
    bundles_weekly = create_weekly_bundles(bundles)
    bundles_monthly = create_monthly_bundles(bundles)


    if opt_show_dataframe: # type: ignore
        st.header("Dataframes")
        st.markdown("#### Übersicht der geladenen (und transformierten) Daten")
        for bundle in bundles:
            st.markdown(f"{bundle.description}")
            st.dataframe(bundle.df)
        timer("Zeit für Darstellen der Dataframes", opt_timer)

    if opt_show_statistics: # type: ignore
        st.header("Statistiken")
        cols = st.columns(len(bundles))
        for col, bundle in zip(cols, bundles):
            with col:
                st.markdown(f"#### {bundle.description}")
                st.write(f"Anzahl Zeilen: {bundle.df.shape[0]}")
                sum_value = bundle.df["kW"].sum()
                st.write(f"Summe von 'kW': {sum_value:,.2f}")
                # Jahressumme in kWh berechnen und anzeigen
                # Annahme: "kW" ist die Leistung zum jeweiligen Zeitpunkt, Intervall in Minuten
                jahressumme = sum_value * (bundle.interval / 60)
                st.write(f"Jahressumme kWh: {jahressumme:,.2f} kWh")
                min_value = bundle.df["kW"].min()
                max_value = bundle.df["kW"].max()
                mean_value = bundle.df["kW"].mean()
                min_row = bundle.df.loc[bundle.df["kW"].idxmin()]
                max_row = bundle.df.loc[bundle.df["kW"].idxmax()]
                st.write(f"Durchschnitt von 'kW': {mean_value:,.2f}")
                st.write(f"Minimum von 'kW': {min_value:,.2f} am {min_row['datetime']}")
                st.write(f"Maximum von 'kW': {max_value:,.2f} am {max_row['datetime']}")
        timer("Zeit für das Darstellen der Statistiken", opt_timer)
        st.write("---")
        cols = st.columns(len(bundles))
        for col, bundle in zip(cols, bundles_hourly):
            with col:
                st.write("**basierend auf stündlichen Werten**")
                st.write(f"Anzahl Zeilen: {bundle.df.shape[0]}")
                min_value = bundle.df["kW"].min()
                max_value = bundle.df["kW"].max()
                mean_value = bundle.df["kW"].mean()
                min_row = bundle.df.loc[bundle.df["kW"].idxmin()]
                max_row = bundle.df.loc[bundle.df["kW"].idxmax()]
                st.write(f"Durchschnitt von 'kW': {mean_value:,.2f}")
                st.write(f"Minimum von 'kW': {min_value:,.2f} am {min_row['datetime']}")
                st.write(f"Maximum von 'kW': {max_value:,.2f} am {max_row['datetime']}")
        timer("Zeit für das Darstellen der Statistiken", opt_timer)
        st.write("---")
        cols = st.columns(len(bundles))
        for col, bundle in zip(cols, bundles_weekly):
            with col:
                st.write("**basierend auf wöchentlichen Werten**")
                st.write(f"Anzahl Zeilen: {bundle.df.shape[0]}")
                min_value = bundle.df["kW"].min()
                max_value = bundle.df["kW"].max()
                mean_value = bundle.df["kW"].mean()
                min_row = bundle.df.loc[bundle.df["kW"].idxmin()]
                max_row = bundle.df.loc[bundle.df["kW"].idxmax()]
                st.write(f"Durchschnitt von 'kW': {mean_value:,.2f}")
                st.write(f"Minimum von 'kW': {min_value:,.2f} am {min_row['datetime']}")
                st.write(f"Maximum von 'kW': {max_value:,.2f} am {max_row['datetime']}")
        timer("Zeit für das Darstellen der Statistiken", opt_timer)
        st.write("---")
        cols = st.columns(len(bundles))
        for col, bundle in zip(cols, bundles_monthly):
            with col:
                st.write("**basierend auf monatlichen Werten**")
                st.write(f"Anzahl Zeilen: {bundle.df.shape[0]}")
                min_value = bundle.df["kW"].min()
                max_value = bundle.df["kW"].max()
                mean_value = bundle.df["kW"].mean()
                min_row = bundle.df.loc[bundle.df["kW"].idxmin()]
                max_row = bundle.df.loc[bundle.df["kW"].idxmax()]
                st.write(f"Durchschnitt von 'kW': {mean_value:,.2f}")
                st.write(f"Minimum von 'kW': {min_value:,.2f} am {min_row['datetime']}")
                st.write(f"Maximum von 'kW': {max_value:,.2f} am {max_row['datetime']}")
        timer("Zeit für das Darstellen der Statistiken", opt_timer)


    df_full = pd.DataFrame()
    df_full['datetime'] = bundles[0].df['datetime']
    for bundle in bundles:
        df_full[bundle.description + " (kW)"] = bundle.df['kW']

    if opt_show_dataframe: # type: ignore
        st.markdown("## Kombiniertes Dataframe")
        st.dataframe(df_full)
    timer("Zeit für das Kombinieren und Darstellen des neuen Dataframes", opt_timer)

    if opt_calc: # type: ignore
        st.header("Berechnungen")
        # Summiere "Wert (kWh)" für alle Bundles mit is_last und is_erzeugung
        last_dfs = [b.df for b in bundles if b.is_last]
        erzeugung_dfs = [b.df for b in bundles if b.is_erzeugung]

        if last_dfs:
            last_df = pd.concat(last_dfs)
            last_sum = last_df.groupby("datetime")["kW"].sum().reset_index()
            last_bundle = Datenbundle(
                df=last_sum,
                description="Last",
                interval=0,
                is_last=True,
                is_erzeugung=False,
                farbe="#1f77b4"
            )
            bundles.append(last_bundle)

        if erzeugung_dfs:
            erzeugung_df = pd.concat(erzeugung_dfs)
            erzeugung_sum = erzeugung_df.groupby("datetime")["kW"].sum().reset_index()
            erzeugung_bundle = Datenbundle(
                df=erzeugung_sum,
                description="Erzeugung",
                interval=0,
                is_last=False,
                is_erzeugung=True,
                farbe="#ff7f0e"
            )
            bundles.append(erzeugung_bundle)

        # Prüfe ob "Last" und "Erzeugung" Bundles existieren
        last_bundle = next((b for b in bundles if b.description == "Last"), None)
        erzeugung_bundle = next((b for b in bundles if b.description == "Erzeugung"), None)

        if last_bundle is not None and erzeugung_bundle is not None:
            # Merge nach datetime
            merged = pd.merge(
                last_bundle.df,
                erzeugung_bundle.df,
                on="datetime",
                suffixes=("_last", "_erzeugung")
            )
            
            # Eigenverbrauch = min(Erzeugung, Last)
            merged["Eigenverbrauch (kW)"] = merged[["kW_last", "kW_erzeugung"]].min(axis=1)
            # Einspeisung = Erzeugung - Eigenverbrauch
            merged["Einspeisung (kW)"] = merged["kW_erzeugung"] - merged["Eigenverbrauch (kW)"]
            # Fremdbezug = Last - Eigenverbrauch
            merged["Fremdbezug (kW)"] = merged["kW_last"] - merged["Eigenverbrauch (kW)"]

            if opt_show_dataframe: # type: ignore
                st.markdown("### Eigenverbrauch und Einspeisung")
                st.dataframe(merged[["datetime", "kW_last", "kW_erzeugung", "Eigenverbrauch (kW)", "Einspeisung (kW)", "Fremdbezug (kW)"]])
            timer("Zeit nach dem Berechnen von Eigenverbrauch und Darstellung des Dataframes", opt_timer)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("#### Eigenverbrauch")
                st.write(f"Summe Eigenverbrauch: {merged['Eigenverbrauch (kW)'].sum():,.2f} kW")
                st.write(f"Durchschnitt Eigenverbrauch: {merged['Eigenverbrauch (kW)'].mean():,.2f} kW")
                min_ev = merged['Eigenverbrauch (kW)'].min()
                max_ev = merged['Eigenverbrauch (kW)'].max()
                min_ev_row = merged.loc[merged['Eigenverbrauch (kW)'].idxmin()]
                max_ev_row = merged.loc[merged['Eigenverbrauch (kW)'].idxmax()]
                st.write(f"Minimum Eigenverbrauch: {min_ev:,.2f} kW am {min_ev_row['datetime']}")
                st.write(f"Maximum Eigenverbrauch: {max_ev:,.2f} kW am {max_ev_row['datetime']}")

            with col2:
                st.write("#### Einspeisung")
                st.write(f"Summe Einspeisung: {merged['Einspeisung (kW)'].sum():,.2f} kW")
                st.write(f"Durchschnitt Einspeisung: {merged['Einspeisung (kW)'].mean():,.2f} kW")
                min_ein = merged['Einspeisung (kW)'].min()
                max_ein = merged['Einspeisung (kW)'].max()
                min_ein_row = merged.loc[merged['Einspeisung (kW)'].idxmin()]
                max_ein_row = merged.loc[merged['Einspeisung (kW)'].idxmax()]
                st.write(f"Minimum Einspeisung: {min_ein:,.2f} kW am {min_ein_row['datetime']}")
                st.write(f"Maximum Einspeisung: {max_ein:,.2f} kW am {max_ein_row['datetime']}")

            with col3:
                st.write("#### Fremdbezug")
                st.write(f"Summe Fremdbezug: {merged['Fremdbezug (kW)'].sum():,.2f} kW")
                st.write(f"Durchschnitt Fremdbezug: {merged['Fremdbezug (kW)'].mean():,.2f} kW")
                min_fb = merged['Fremdbezug (kW)'].min()
                max_fb = merged['Fremdbezug (kW)'].max()
                min_fb_row = merged.loc[merged['Fremdbezug (kW)'].idxmin()]
                max_fb_row = merged.loc[merged['Fremdbezug (kW)'].idxmax()]
                st.write(f"Minimum Fremdbezug: {min_fb:,.2f} kW am {min_fb_row['datetime']}")
                st.write(f"Maximum Fremdbezug: {max_fb:,.2f} kW am {max_fb_row['datetime']}")


            for col in merged.columns:
                if col != "datetime" and col not in df_full.columns:
                    df_full[col] = merged[col]

            timer("Zeit nach dem Kombinieren der df mit Berechnungen", opt_timer)
            if opt_show_dataframe: # type: ignore
                st.dataframe(df_full)

        else:
            st.info("Für die Berechnungen werden sowohl die 'Last'- als auch die 'Erzeugung'-Datenreihen benötigt.")


    # Plotly line chart with multiple lines from individual columns
    st.header("Visualisierung der Datenreihe(n)")
    st.subheader("Gesamter Zeitraum")

    # Ensure all columns except 'datetime' are used for plotting
    columns_to_plot = [col for col in df_full.columns if col != "datetime"]
    # Farben aus den Bundles übernehmen, falls definiert
    color_discrete_map = {}
    for bundle in bundles:
        col_name = bundle.description + " (kW)"
        if col_name in columns_to_plot and bundle.farbe:
            color_discrete_map[col_name] = bundle.farbe

    # Plotly line chart mit Farbanpassung
    if columns_to_plot:
        line_chart_fig = px.line(
            df_full,
            x="datetime",
            y=columns_to_plot,
            labels={"value": "Wert (kW)", "variable": "Datenreihe"},
            title="Vergleich der Datenreihen über die Zeit",
            color_discrete_map=color_discrete_map if color_discrete_map else None
        )
        st.plotly_chart(line_chart_fig, use_container_width=True)
    else:
        st.warning("Keine Datenreihen verfügbar für die Visualisierung.")

    timer("Zeit nach dem Darstellen des Diagramms", opt_timer)

    # Selectbox für die Auswahl der Referenz-Datenreihe für Maxima
    st.subheader("Analyse der stärksten Perioden")
    if len(bundles) > 1:
        reference_options = [bundle.description for bundle in bundles]
        selected_reference = st.selectbox(
            "Wähle die Datenreihe für die Bestimmung der stärksten Perioden:",
            reference_options,
            index=0,
            help="Diese Datenreihe wird verwendet, um den stärksten Monat und die stärkste Woche zu bestimmen"
        )
        # Finde den Index der ausgewählten Datenreihe
        reference_index = next(i for i, bundle in enumerate(bundles) if bundle.description == selected_reference)
    else:
        reference_index = 0
        selected_reference = bundles[0].description if bundles else "Keine Daten"

    st.subheader(f"Der stärkste Monat (nach {selected_reference})")
    # Ermittele den stärksten Monat aus der ausgewählten Datenreihe der monatlichen Bundles
    if bundles_monthly and reference_index < len(bundles_monthly) and not bundles_monthly[reference_index].df.empty:
        # Finde den Monat mit dem höchsten Wert (kWh)
        strongest_month_row = bundles_monthly[reference_index].df.loc[bundles_monthly[reference_index].df["kW"].idxmax()]
        strongest_month = strongest_month_row["datetime"]
        st.info(f"Stärkster Monat: {strongest_month.strftime('%B %Y')} mit {strongest_month_row['kW']:,.2f} kW")

        # Filtere df_full auf den Datumsbereich dieses Monats
        mask = (df_full["datetime"].dt.to_period("M") == pd.Period(strongest_month, freq="M"))
        df_strongest_month = df_full[mask]

        # Plotly Liniendiagramm für diesen Monat
        columns_to_plot = [col for col in df_strongest_month.columns if col != "datetime"]
        if not df_strongest_month.empty and columns_to_plot:
            line_chart_fig_month = px.line(
                df_strongest_month,
                x="datetime",
                y=columns_to_plot,
                labels={"value": "Wert (kWh)", "variable": "Datenreihe"},
                title=f"Vergleich der Datenreihen im stärksten Monat: {strongest_month.strftime('%B %Y')}",
                color_discrete_map=color_discrete_map if color_discrete_map else None
            )
            st.plotly_chart(line_chart_fig_month, use_container_width=True)
        else:
            st.warning("Keine Daten für den stärksten Monat gefunden.")
    else:
        st.warning("Keine Monatsdaten verfügbar zur Ermittlung des stärksten Monats.")


    st.subheader(f"Die stärkste Woche (nach {selected_reference})")
    # Ermittele die stärkste Woche aus der ausgewählten Datenreihe der wöchentlichen Bundles
    if bundles_weekly and reference_index < len(bundles_weekly) and not bundles_weekly[reference_index].df.empty:
        # Finde die Woche mit dem höchsten Wert (kW)
        strongest_week_row = bundles_weekly[reference_index].df.loc[bundles_weekly[reference_index].df["kW"].idxmax()]
        strongest_week_start = strongest_week_row["datetime"]
        strongest_week_end = strongest_week_start + pd.Timedelta(days=7)
        st.info(f"Stärkste Woche: {strongest_week_start.strftime('%d.%m.%Y')} bis {strongest_week_end.strftime('%d.%m.%Y')} mit {strongest_week_row['kW']:,.2f} kW")

        # Filtere df_full auf den Datumsbereich dieser Woche
        mask = (df_full["datetime"] >= strongest_week_start) & (df_full["datetime"] < strongest_week_end)
        df_strongest_week = df_full[mask]

        # Plotly Liniendiagramm für diese Woche
        columns_to_plot = [col for col in df_strongest_week.columns if col != "datetime"]
        if not df_strongest_week.empty and columns_to_plot:
            line_chart_fig_week = px.line(
                df_strongest_week,
                x="datetime",
                y=columns_to_plot,
                labels={"value": "Wert (kWh)", "variable": "Datenreihe"},
                title=f"Vergleich der Datenreihen in der stärksten Woche: {strongest_week_start.strftime('%d.%m.%Y')} bis {strongest_week_end.strftime('%d.%m.%Y')}",
                color_discrete_map=color_discrete_map if color_discrete_map else None
            )
            st.plotly_chart(line_chart_fig_week, use_container_width=True)
        else:
            st.warning("Keine Daten für die stärkste Woche gefunden.")

    timer("Zeit nach dem Darstellen des Diagramms der stärksten Woche", opt_timer)
