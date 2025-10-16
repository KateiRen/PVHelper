import os
import json
import locale
import streamlit as st
import pandas as pd
import plotly.express as px
from helper import Datenbundle, timer, create_hourly_bundles, create_weekly_bundles, create_monthly_bundles, load_and_transform_data, check_and_remove_leap_day
import yaml
from helper import BatteryStorage


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

# PV Simulation Bereich
with st.sidebar.expander("🌞 PV Simulation"):
    enable_pv_simulation = st.toggle("Simulation PV", value=False)
    
    # Eingabefelder werden immer angezeigt, unabhängig vom Toggle
    pv_west = st.number_input(
        "West (kWp)", 
        min_value=0.0, 
        max_value=1000.0, 
        value=0.0, 
        step=0.1,
        help="Installierte Leistung West-Ausrichtung",
        disabled=not enable_pv_simulation
    )
    pv_sued = st.number_input(
        "Süd (kWp)", 
        min_value=0.0, 
        max_value=1000.0, 
        value=0.0, 
        step=0.1,
        help="Installierte Leistung Süd-Ausrichtung",
        disabled=not enable_pv_simulation
    )
    pv_ost = st.number_input(
        "Ost (kWp)", 
        min_value=0.0, 
        max_value=1000.0, 
        value=0.0, 
        step=0.1,
        help="Installierte Leistung Ost-Ausrichtung",
        disabled=not enable_pv_simulation
    )
    
    pv_total = pv_west + pv_sued + pv_ost
    if pv_total > 0:
        status_text = "✅ Aktiviert" if enable_pv_simulation else "⚫ Deaktiviert"
        st.info(f"Gesamt: {pv_total:.1f} kWp ({status_text})")
    
    # Download-Button für PV-Simulationsdaten
    if enable_pv_simulation and pv_total > 0:
        if st.button("📥 PV-Daten als CSV/JSON speichern", help="Speichert die generierte PV-Simulation im Projektordner"):
            st.session_state.export_pv_data = True

st.sidebar.markdown('---')

# Stromspeicher Bereich
with st.sidebar.expander("🔋 Stromspeicher"):
    enable_battery = st.toggle("Stromspeicher aktivieren", value=False)
    
    # Lade verfügbare YAML-Dateien aus dem batteries-Ordner
    batteries_folder = "batteries"
    battery_files = []
    if os.path.exists(batteries_folder):
        battery_files = [f for f in os.listdir(batteries_folder) if f.endswith(".yaml")]
    
    if battery_files:
        selected_battery = st.selectbox(
            "Batteriekonfiguration wählen",
            options=["Keine"] + battery_files,
            index=0,
            help="Wähle eine Batteriekonfiguration aus dem batteries-Ordner",
            disabled=not enable_battery
        )
        
        if enable_battery and selected_battery != "Keine":
            battery_path = os.path.join(batteries_folder, selected_battery)
            st.info(f"✅ Batterie: {selected_battery}")
        elif enable_battery:
            st.warning("⚡ Stromspeicher aktiviert, aber keine Konfiguration gewählt")
    else:
        selected_battery = "Keine"
        st.warning("Keine Batteriekonfigurationen im 'batteries' Ordner gefunden")

st.sidebar.markdown('---')
st.sidebar.subheader("🛠️ Optionen")
opt_clean_columns = st.sidebar.checkbox("Unnötige Spalten entfernen", value=True, help="Entfernt alle Spalten außer Datum/Uhrzeit und Wert")
opt_etl_steps = st.sidebar.checkbox("Zeige ETL Schritte", value=False, help="Zeigt die Extract-Transform-Load Verarbeitungsschritte für jede Datenreihe")
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
    "timer": opt_timer,
    "etl_steps": opt_etl_steps,
    "pv_simulation": {
        "enabled": enable_pv_simulation,
        "west": pv_west,
        "sued": pv_sued,
        "ost": pv_ost,
        "total": pv_west + pv_sued + pv_ost
    },
    "battery": {
        "enabled": enable_battery,
        "config_file": selected_battery if enable_battery and selected_battery != "Keine" else None,
        "config_path": os.path.join(batteries_folder, selected_battery) if enable_battery and selected_battery != "Keine" else None
    }
}

timer("", False)

for file in files:
    file_path = os.path.join(project_path, file) # type: ignore
    bundles.append(load_and_transform_data(file_path, options)) # type: ignore
    timer(f"{file} wurde geladen", opt_timer)

if options["pv_simulation"]["enabled"] and options["pv_simulation"]["total"] > 0:
    # PV Daten laden und zum Bundle hinzufügen
    pv_file_path = os.path.join("reference", "PV_series.csv")
    if os.path.exists(pv_file_path):
        df = pd.read_csv(pv_file_path, skiprows=0, decimal=",", sep=";", encoding="utf-8")
        st.write(f"Anzahl Zeilen in df: {df.shape[0]}")
        st.write(f"Spalten in df: {df.columns.tolist()}")

        # Skaliere die PV-Norm-Spalten mit den jeweiligen Peak-Werten
        factor_east=  options["pv_simulation"]["ost"] / df["PV_east_30_norm"].max()
        factor_south= options["pv_simulation"]["sued"] / df["PV_south_30_norm"].max()
        factor_west=  options["pv_simulation"]["west"] / df["PV_west_30_norm"].max()
        # Addiere die Werte zu einer neuen Spalte "PV-Simulation"
        df["kW"] = df["PV_east_30_norm"]*factor_east + df["PV_south_30_norm"]*factor_south + df["PV_west_30_norm"]*factor_west
        df["datetime"] = pd.to_datetime(df["Date [UTC+1]"], format="%d.%m.%Y %H:%M")
        df = df[["datetime", "kW"]]
        
        # Bereinige die PV-Daten um Schaltjahr-Einträge (29. Februar), BEVOR das Bundle erstellt wird
        df = check_and_remove_leap_day(df, {"Intervall": 15}, options)
        
        # Erzeuge ein Datenbundle für die PV-Simulation
        pv_bundle = Datenbundle(
            df=df,
            description=f"PV Simulation ({options['pv_simulation']['total']:.1f} kWp)",
            interval=15,  # Passe ggf. das Intervall an
            is_last=False,
            is_erzeugung=True,
            farbe="#AF9500"
        )


        bundles.append(pv_bundle)
        timer("PV Simulationsdaten wurden geladen und skaliert", opt_timer)
        
        # Export der PV-Simulationsdaten, wenn gewünscht
        if st.session_state.get("export_pv_data", False):
            # CSV Export
            pv_filename = f"PV_Simulation_{options['pv_simulation']['west']:.1f}W_{options['pv_simulation']['sued']:.1f}S_{options['pv_simulation']['ost']:.1f}O"
            csv_filename = f"{pv_filename}.csv"
            json_filename = f"{pv_filename}.json"
            
            # Stelle sicher, dass der data-Unterordner existiert
            data_path = os.path.join(project_path, "data") # type: ignore
            os.makedirs(data_path, exist_ok=True)
            
            # CSV-Datei im data-Unterordner speichern
            csv_path = os.path.join(data_path, csv_filename)
            df.to_csv(csv_path, index=False, encoding="utf-8", sep=";", decimal=",")
            
            # Pfad für JSON-Datei (nach dem Muster: projects\\<projektordner>\\data\\<csv>)
            json_csv_path = f"projects\\\\{selected_project}\\\\data\\\\{csv_filename}"
            
            # JSON-Konfigurationsdatei erstellen
            json_config = {
                "Name": f"PV Simulation ({options['pv_simulation']['total']:.1f} kWp)",
                "Datei": json_csv_path,
                "Startzeile": 0,
                "Intervall": 15,
                "Einheit": "kW",
                "Spaltentrennzeichen": ";",
                "Dezimaltrennzeichen": ",",
                "Datenspalte": "kW",
                "Datum-Zeit-Spalte": "datetime",
                "Datumspalte": "",
                "Zeitspalte": "",
                "Datum-Zeit-Format": "%Y-%m-%d %H:%M:%S",
                "Typ": "Erzeugung",
                "Farbe": "#AF9500",
                "pv_konfiguration": {
                    "west_kwp": options["pv_simulation"]["west"],
                    "sued_kwp": options["pv_simulation"]["sued"],
                    "ost_kwp": options["pv_simulation"]["ost"],
                    "gesamt_kwp": options["pv_simulation"]["total"],
                    "generiert_am": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            json_path = os.path.join(project_path, json_filename) # type: ignore
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_config, f, indent=4, ensure_ascii=False)
            
            st.success("✅ PV-Simulationsdaten gespeichert:")
            st.write(f"📄 CSV: `data/{csv_filename}`")
            st.write(f"⚙️ JSON: `{json_filename}`")
            
            # Reset des Export-Flags
            st.session_state.export_pv_data = False
            
    else:
        st.warning("PV Simulationsdatei nicht gefunden. Bitte sicherstellen, dass 'data/pv_simulation.csv' existiert.")


# Lade Batterie-Konfiguration, wenn aktiviert und ausgewählt
battery = None
if options["battery"]["enabled"] and options["battery"]["config_file"]:
    with open(options["battery"]["config_path"], "r", encoding="utf-8") as f:
        battery_config = yaml.safe_load(f)
    battery = BatteryStorage(battery_config)
#    for key, value in battery_config.items():
#        setattr(battery, key, value)
    # Zeige Batterie-Konfiguration, falls geladen
    if battery is not None:
        battery_info = {k: v for k, v in vars(battery).items() if not k.startswith('_')}
        st.info(f"Batteriespeicher geladen:\n{json.dumps(battery_info, indent=2, ensure_ascii=False)}")



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
        # Prüfe, ob datetime-Spalten identisch sind
        if not df_full['datetime'].equals(bundle.df['datetime']):
            st.warning(f"Achtung: datetime-Spalte von '{bundle.description}' unterscheidet sich vom ersten Bundle. Merge wird durchgeführt.")
            # Verwende merge statt direkte Zuweisung für sichere Alignment
            temp_df = pd.DataFrame({
                'datetime': bundle.df['datetime'],
                bundle.description + " (kW)": bundle.df['kW']
            })
            df_full = pd.merge(df_full, temp_df, on="datetime", how="outer")
        else:
            df_full[bundle.description + " (kW)"] = bundle.df['kW']

    if opt_show_dataframe: # type: ignore
        st.markdown("## Kombiniertes Dataframe")
        st.dataframe(df_full)
    timer("Zeit für das Kombinieren und Darstellen des neuen Dataframes", opt_timer)

    # Berechnungen ohne Batteriespeicher
    if opt_calc and not options["battery"]["enabled"]: # type: ignore
        st.header("Berechnungen")
        # Summiere "Wert (kWh)" für alle Bundles mit is_last und is_erzeugung
        last_dfs = [b.df for b in bundles if b.is_last]
        erzeugung_dfs = [b.df for b in bundles if b.is_erzeugung]

        if last_dfs:
            last_df = pd.concat(last_dfs)
            last_sum = last_df.groupby("datetime")["kW"].sum().reset_index()
            # Sortiere nach datetime um korrekte Reihenfolge sicherzustellen
            last_sum = last_sum.sort_values("datetime").reset_index(drop=True)
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
            # Sortiere nach datetime um korrekte Reihenfolge sicherzustellen
            erzeugung_sum = erzeugung_sum.sort_values("datetime").reset_index(drop=True)
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
                suffixes=("_Last", "_Erzeugung")
            )
            
            # Eigenverbrauch = min(Erzeugung, Last)
            merged["Eigenverbrauch (kW)"] = merged[["kW_Last", "kW_Erzeugung"]].min(axis=1)
            # Einspeisung = Erzeugung - Eigenverbrauch
            merged["Einspeisung (kW)"] = merged["kW_Erzeugung"] - merged["Eigenverbrauch (kW)"]
            # Fremdbezug = Last - Eigenverbrauch
            merged["Fremdbezug (kW)"] = merged["kW_Last"] - merged["Eigenverbrauch (kW)"]
            #merged["Differenz (kW)"] = merged["kW_Erzeugung"] - merged["kW_Last"]
            # Auswahlbox für Export
            export_columns = ["Eigenverbrauch (kW)", "Einspeisung (kW)", "Fremdbezug (kW)", "Differenz (kW)"]
            export_selection = st.selectbox(
                "Wähle eine berechnete Datenreihe zum Exportieren als CSV:",
                export_columns,
                index=0
            )
            export_df = merged[["datetime", export_selection]].copy()
            export_df.columns = ["datetime", export_selection]

            csv_data = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"CSV herunterladen: {export_selection}",
                data=csv_data,
                file_name=f"{export_selection.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            if opt_show_dataframe: # type: ignore
                st.markdown("### Eigenverbrauch und Einspeisung")
                st.dataframe(merged[["datetime", "kW_Last", "kW_Erzeugung", "Eigenverbrauch (kW)", "Einspeisung (kW)", "Fremdbezug (kW)"]])
            timer("Zeit nach dem Berechnen von Eigenverbrauch und Darstellung des Dataframes", opt_timer)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("#### Eigenverbrauch")
                st.write(f"Summe Eigenverbrauch: {merged['Eigenverbrauch (kW)'].sum():,.2f} kW")
                # Summe als kWh anzeigen (Intervall in Minuten, geteilt durch 60)
                sum_ev_kwh = merged['Eigenverbrauch (kW)'].sum() * (bundles[0].interval / 60)
                st.write(f"Summe Eigenverbrauch: {sum_ev_kwh:,.2f} kWh")
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
                sum_ein_kwh = merged['Einspeisung (kW)'].sum() * (bundles[0].interval / 60)
                st.write(f"Summe Einspeisung: {sum_ein_kwh:,.2f} kWh")
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
                sum_fb_kwh = merged['Fremdbezug (kW)'].sum() * (bundles[0].interval / 60)
                st.write(f"Summe Fremdbezug: {sum_fb_kwh:,.2f} kWh")
                st.write(f"Durchschnitt Fremdbezug: {merged['Fremdbezug (kW)'].mean():,.2f} kW")
                min_fb = merged['Fremdbezug (kW)'].min()
                max_fb = merged['Fremdbezug (kW)'].max()
                min_fb_row = merged.loc[merged['Fremdbezug (kW)'].idxmin()]
                max_fb_row = merged.loc[merged['Fremdbezug (kW)'].idxmax()]
                st.write(f"Minimum Fremdbezug: {min_fb:,.2f} kW am {min_fb_row['datetime']}")
                st.write(f"Maximum Fremdbezug: {max_fb:,.2f} kW am {max_fb_row['datetime']}")

                # Gesamtautarkiegrad berechnen und anzeigen
                # Autarkiegrad = Eigenverbrauch / Last
                gesamt_eigenverbrauch = merged["Eigenverbrauch (kW)"].sum()
                gesamt_last = merged["kW_Last"].sum()
                if gesamt_last > 0:
                    autarkiegrad = gesamt_eigenverbrauch / gesamt_last * 100
                    st.success(f"**Gesamtautarkiegrad:** {autarkiegrad:,.2f} %")
                else:
                    st.warning("Gesamtautarkiegrad kann nicht berechnet werden (Summe Last = 0).")

            for col in merged.columns:
                if col != "datetime" and col not in df_full.columns:
                    # Merge df_full mit merged basierend auf datetime um korrekte Ausrichtung zu gewährleisten
                    df_full = pd.merge(df_full, merged[["datetime", col]], on="datetime", how="left")

            timer("Zeit nach dem Kombinieren der df mit Berechnungen", opt_timer)
            if opt_show_dataframe: # type: ignore
                st.dataframe(df_full)

        else:
            st.info("Für die Berechnungen werden sowohl die 'Last'- als auch die 'Erzeugung'-Datenreihen benötigt.")

    # Berechnungen mit Batteriespeicher
    if opt_calc and options["battery"]["enabled"] and selected_battery != "Keine": # type: ignore
        st.header("Berechnungen")
        # Summiere "Wert (kWh)" für alle Bundles mit is_last und is_erzeugung
        last_dfs = [b.df for b in bundles if b.is_last]
        erzeugung_dfs = [b.df for b in bundles if b.is_erzeugung]

        if last_dfs:
            last_df = pd.concat(last_dfs)
            last_sum = last_df.groupby("datetime")["kW"].sum().reset_index()
            # Sortiere nach datetime um korrekte Reihenfolge sicherzustellen
            last_sum = last_sum.sort_values("datetime").reset_index(drop=True)
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
            # Sortiere nach datetime um korrekte Reihenfolge sicherzustellen
            erzeugung_sum = erzeugung_sum.sort_values("datetime").reset_index(drop=True)
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
                suffixes=("_Last", "_Erzeugung")
            )            


            st.header("Berechnungen mit Batteriespeicher")
            st.info("Die Berechnung mit Batteriespeicher ist noch in Arbeit und wird in einer zukünftigen Version verfügbar sein.")
            # Hier würde die Logik für die Berechnung mit dem Batteriespeicher implementiert werden.
            # Dies könnte die Simulation von Lade- und Entladezyklen basierend auf Last- und Erzeugungsdaten umfassen.
            # Aktuell wird nur eine Info angezeigt.


            interval_hours = bundles[0].interval / 60  # z.B. 15min = 0.25h

            # Iteriere über die Zeitreihe und simuliere den Batteriebetrieb
            for index, row in merged.iterrows():
                # Hole Werte aus DataFrame, falls vorhanden, sonst 0
                last = row.get("kW_Last", 0)
                erzeugung = row.get("kW_Erzeugung", 0)

                # Initialisiere Variablen
                charge_amount = 0
                discharge_amount = 0
                einspeisung = 0
                fremdbezug = 0

                # PV-Erzeugung zuerst für Lastdeckung
                pv_for_load = min(erzeugung, last)
                rest_pv = max(erzeugung - last, 0)
                rest_load = max(last - erzeugung, 0)

                if erzeugung > last:
                    # Überschüssige PV-Energie vorhanden - Batterie laden
                    charge_amount = battery.charged(rest_pv, interval_hours)
                    einspeisung = rest_pv - charge_amount  # Restliche PV nach Ladung
                elif last > erzeugung:
                    # Zusätzliche Last - Batterie entladen
                    discharge_amount = battery.discharged(rest_load, interval_hours)
                    fremdbezug = rest_load - discharge_amount   # Restliche Last nach Entladung


                battery_soc = battery.get_state_of_charge_kwh()


                # Ergebnisse im DataFrame speichern
                df_full.at[index, "Speicher SOC (kWh)"] = battery_soc
                df_full.at[index, "Eigenverbrauch mit Speicher (kW)"] = pv_for_load + (discharge_amount / interval_hours)
                df_full.at[index, "Einspeisung mit Speicher (kW)"] = einspeisung
                df_full.at[index, "Fremdbezug mit Speicher (kW)"] = fremdbezug
                df_full.at[index, "Speicher Ladung (kW)"] = charge_amount * interval_hours
                df_full.at[index, "Speicher Entladung (kW)"] = discharge_amount * interval_hours

            timer("Zeit nach dem Batteriespeicher-Berechnungsabschnitt", opt_timer)



        else:
            st.info("Für die Berechnungen mit Batteriespeicher werden sowohl die 'Last'- als auch die 'Erzeugung'-Datenreihen benötigt.")
            st.stop()



 


    # Plotly line chart with multiple lines from individual columns
    st.header("Visualisierung der Datenreihe(n)")
    st.subheader("Gesamter Zeitraum")

    # Ensure all columns except 'datetime' are used for plotting
    columns_to_plot = [col for col in df_full.columns if col != "datetime" and col not in ["kW_Last", "kW_Erzeugung"]]
    # Farben aus den Bundles übernehmen, falls definiert
    color_discrete_map = {}
    for bundle in bundles:
        col_name = bundle.description + " (kW)"
        if col_name in columns_to_plot and bundle.farbe:
            color_discrete_map[col_name] = bundle.farbe
    
    # Spezifische Farben für berechnete Kategorien
    color_discrete_map.update({
        "Eigenverbrauch (kW)": "#00AA00",  # Grün
        "Einspeisung (kW)": "#0066CC",     # Blau
        "Fremdbezug (kW)": "#CC0000",      # Rot
        "Differenz (kW)": "#666666"        # Grau für Differenz
    })

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
        columns_to_plot = [col for col in df_strongest_month.columns if col != "datetime" and col not in ["kW_Last", "kW_Erzeugung"]]
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
        columns_to_plot = [col for col in df_strongest_week.columns if col != "datetime" and col not in ["kW_Last", "kW_Erzeugung"]]
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
