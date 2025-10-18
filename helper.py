"""import List, json, dataclass, streamlit as st, pandas as pd, time"""

from typing import List
import time
import json
from dataclasses import dataclass, field
import streamlit as st
import pandas as pd


@dataclass
class BatteryStorage:
    """Simuliere ein Batteriespeichersystem"""

    capacity_kwh: float = 100
    self_discharge_rate: float = 0.0004
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.9
    max_charge_power_kw: float = 10
    max_discharge_power_kw: float = 10
    min_soc: float = 0.2
    max_soc: float = 1.0
    initial_soc: float = 0.5
    soc_kwh: float = field(init=False)

    def __post_init__(self):
        self.soc_kwh = self.capacity_kwh * self.initial_soc

    def apply_config(self, config: dict = None):
        """Apply configuration overrides after initialization."""
        if config:
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.soc_kwh = self.capacity_kwh * self.initial_soc

    def apply_self_discharge(self, hours: float = 0.25) -> None:
        """Wende Selbstentladung über eine gegebene Anzahl von Stunden an"""
        loss = self.soc_kwh * self.self_discharge_rate * hours
        self.soc_kwh = max(self.soc_kwh - loss, self.capacity_kwh * self.min_soc)

    def charged(self, power_kw: float, duration_h: float) -> float:
        """Lade die Batterie mit gegebener Leistung (kW) über eine Dauer (h)"""
        self.apply_self_discharge(duration_h)
        power_kw = min(power_kw, self.max_charge_power_kw)
        energy_in = power_kw * duration_h * self.charge_efficiency
        available_capacity = self.capacity_kwh * self.max_soc - self.soc_kwh
        charged_energy = min(energy_in, available_capacity)
        self.soc_kwh += charged_energy
        return charged_energy / self.charge_efficiency

    def discharged(self, power_kw: float, duration_h: float) -> float:
        """Entlade die Batterie mit gegebener Leistung (kW) über eine Dauer (h)"""
        self.apply_self_discharge(duration_h)
        power_kw = min(power_kw, self.max_discharge_power_kw)
        energy_out = power_kw * duration_h * self.discharge_efficiency
        available_energy = self.soc_kwh - self.capacity_kwh * self.min_soc
        discharged_energy = min(energy_out, available_energy)
        self.soc_kwh -= discharged_energy
        return discharged_energy / self.discharge_efficiency

    def get_state_of_charge(self) -> float:
        """Gibt den aktuellen Ladezustand als Bruchteil (0-1) zurück"""
        return self.soc_kwh / self.capacity_kwh

    def get_state_of_charge_kwh(self) -> float:
        """Gibt den aktuellen Ladezustand in kWh zurück"""
        return self.soc_kwh


@dataclass
class Datenbundle:
    """Daten und Metadaten für eine Datenreihe"""

    df: pd.DataFrame
    description: str
    interval: int
    is_last: bool
    is_erzeugung: bool
    farbe: str = "#1f77b4"  # Standardfarbe (z.B. Plotly-Default)


@st.cache_data
def read_csv_file(
    path: str, skiprows: int = 0, decimal: str = ",", sep: str = ";"
) -> pd.DataFrame:
    """Lade CSV-Datei mit benutzerdefinierten Einstellungen"""
    df = pd.read_csv(path, skiprows=skiprows, decimal=decimal, sep=sep)
    return df


@st.cache_data
def read_csv_file2(df: pd.DataFrame, settings: dict, options: dict) -> pd.DataFrame:
    """Lade CSV-Datei mit benutzerdefinierten Einstellungen"""
    df = pd.read_csv(
        settings["Datei"],
        skiprows=settings["Startzeile"],
        decimal=settings["Dezimaltrennzeichen"],
        sep=settings["Spaltentrennzeichen"],
    )

    if settings.get("Invertiert", False):
        if options.get("etl_steps", False):
            st.warning("Daten werden invertiert (negativ)")
        df[settings["Datenspalte"]] = -df[settings["Datenspalte"]]

    if settings.get("offset", 0) != 0:
        offset = settings["offset"]
        if options.get("etl_steps", False):
            st.warning(f"Daten werden um {offset} Intervalle verschoben")
        # Nur die Datenspalte verschieben, Datum-Zeit-Spalte bleibt unverändert
        df[settings["Datenspalte"]] = df[settings["Datenspalte"]].shift(offset)
        # Leere (NaN) Werte in der Datenspalte mit 0 auffüllen, Datum-Zeit bleibt erhalten
        df[settings["Datenspalte"]].fillna(0, inplace=True)
    return df


def create_datetime_index(
    df: pd.DataFrame, settings: dict, options: dict
) -> pd.DataFrame:
    """Erstelle eine datetime-Spalte basierend auf den Einstellungen"""
    if options.get("etl_steps", False):
        st.write(f"Spalten im DataFrame: {list(df.columns)}")
    # Erstelle eine datetime-Spalte aus den vorhandenen Infos
    if settings["Datum-Zeit-Spalte"] == "":
        df["datetime"] = pd.to_datetime(
            df[settings["Datumspalte"]] + " " + df[settings["Zeitspalte"]],
            format=settings["Datum-Zeit-Format"],
        )
        # df.drop(columns=[settings['Datumspalte'], settings['Zeitspalte']], inplace=True)
    else:
        df["datetime"] = pd.to_datetime(
            df[settings["Datum-Zeit-Spalte"]], format=settings["Datum-Zeit-Format"]
        )
        # df.drop(columns=[settings['Datum-Zeit-Spalte']], inplace=True)

    # Prüfe auf Null- und NaN-Werte in den relevanten Spalten
    relevant_cols = ["datetime", settings["Datenspalte"]]
    for col in relevant_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            nan_count = df[col].isna().sum()
            if null_count > 0 or nan_count > 0:
                if options.get("etl_steps", False):
                    st.warning(
                        f"Spalte '{col}' enthält {null_count} Null-Werte und {nan_count} NaN-Werte. Diese Zeilen werden entfernt."
                    )
                df = df[df[col].notnull() & df[col].notna()]

    if options["clean_columns"]:
        df = df[
            [col for col in df.columns if col in ["datetime", settings["Datenspalte"]]]
        ]
    # Entferne die Spalten nur, wenn sie existieren
    #    cols_to_drop = [settings['Datumspalte'], settings['Zeitspalte']]
    #    existing_cols = [col for col in cols_to_drop if col in df.columns]
    #    if existing_cols:
    #        df.drop(columns=existing_cols, inplace=True)
    return df


def check_and_fix_right_interval(
    df: pd.DataFrame, settings: dict, options: dict
) -> pd.DataFrame:
    """Überprüfe und korrigiere die Zeitintervalle im DataFrame."""
    # Rechtsbündige Zeitangaben auf Linksbündig shiften
    if (
        settings["Intervall"] == 15
        and df["datetime"].iloc[0].time() == pd.Timestamp("00:15:00").time()
    ):
        df["datetime"] = df["datetime"] - pd.Timedelta(minutes=15)
        if options.get("etl_steps", False):
            st.warning("Rechtsbündige 15 Minuten Intervalle um 15 Minuten reduziert")
    if (
        settings["Intervall"] == 60
        and df["datetime"].iloc[0].time() == pd.Timestamp("01:00:00").time()
    ):
        df["datetime"] = df["datetime"] - pd.Timedelta(minutes=60)
        if options.get("etl_steps", False):
            st.warning("Rechtsbündige 60 Minuten Intervalle um 60 Minuten reduziert")
    check_rowcount(df, settings, options)
    return df


def check_rowcount(df: pd.DataFrame, settings: dict, options: dict) -> pd.DataFrame:
    """Prüfe, ob die Anzahl der Zeilen zur Anzahl der Tage passt"""
    # Prüfe, ob die Anzahl der Zeilen zur Anzahl der Tage passt
    unique_days = df["datetime"].dt.date.nunique()
    if options.get("etl_steps", False):
        st.info(f"Anzahl der einzigartigen Tagesdaten: {unique_days}")
    # expected_rows = unique_days * (1440 // settings['Intervall'])
    expected_rows = unique_days * 24 * (60 // settings["Intervall"])
    # total_minutes = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 60
    # expected_rows = int(total_minutes / interval) + 1  # +1 da inkl. Start- und Endzeitpunkt
    actual_rows = df.shape[0]
    if expected_rows != actual_rows:
        if options.get("etl_steps", False):
            st.warning(
                f"Erwartete Zeilenanzahl: {expected_rows}, tatsächliche Zeilenanzahl: {actual_rows}. Es gibt eine Abweichung."
            )
    else:
        if options.get("etl_steps", False):
            st.success(
                f"Die Anzahl der Zeilen ({actual_rows}) stimmt mit der erwarteten Anzahl überein."
            )
    return df


def get_unique_kw_column_name(df: pd.DataFrame, base_name: str = "Wert-kW") -> str:
    """
    Generate a unique kW column name that doesn't conflict with existing columns.

    Args:
        df: DataFrame to check for existing columns
        base_name: Base name to use for the kW column

    Returns:
        str: Unique column name for kW data
    """
    if base_name not in df.columns:
        return base_name

    # If base name exists, try with suffixes
    counter = 1
    while f"{base_name}_{counter}" in df.columns:
        counter += 1

    return f"{base_name}_{counter}"


def check_and_convert_to_kW(
    df: pd.DataFrame, settings: dict, options: dict
) -> pd.DataFrame:
    """Überprüfe und konvertiere die Datenspalte in kW, falls nötig"""
    if settings["Einheit"].lower() == "kw":
        if options.get("etl_steps", False):
            st.info("Daten sind bereits in kW")
        if settings["Datenspalte"] != "kW":
            df.rename(columns={settings["Datenspalte"]: "kW"}, inplace=True)
        return df
    elif settings["Einheit"].lower() == "kwh":
        if options.get("etl_steps", False):
            st.info("Daten sind in kWh, werden zu kW umgerechnet")
        kw_column = get_unique_kw_column_name(df)
        hours_per_interval = settings["Intervall"] / 60
        df[kw_column] = df[settings["Datenspalte"]] / hours_per_interval
        df.drop(columns=[settings["Datenspalte"]], inplace=True)
        df.rename(columns={kw_column: "kW"}, inplace=True)
    else:
        if options.get("etl_steps", False):
            st.error(
                f"Unbekannte Einheit: {settings['Einheit']}. Erwartet 'kW' oder 'kWh'."
            )
    return df


# def calculate_kwh_from_kw(df: pd.DataFrame, interval_minutes: int, kw_column: str = "Wert-kW") -> pd.Series:
#    """
#    Calculate kWh values from kW data based on time interval.
#    Args:
#        df: DataFrame with kW power data
#        interval_minutes: Time interval in minutes (e.g., 15 for 15-minute data)
#        kw_column: Name of kW column to convert
#    Returns:
#        Series with kWh values
#    """
#    hours_per_interval = interval_minutes / 60
#    return df[kw_column] * hours_per_interval


def check_and_remove_leap_day(
    df: pd.DataFrame, settings: dict, options: dict
) -> pd.DataFrame:
    """Prüfe und entferne Daten für den 29. Februar (Schaltjahr)"""
    # Prüfe, ob es Daten für den 29. Februar gibt (Schaltjahr) und lösche diese Zeilen
    leap_day_mask = (df["datetime"].dt.month == 2) & (df["datetime"].dt.day == 29)
    if leap_day_mask.any():
        if options.get("etl_steps", False):
            st.warning(
                f"Es wurden {leap_day_mask.sum()} Zeilen mit Daten für den 29. Februar gefunden und entfernt."
            )
        df = df[~leap_day_mask]
        check_rowcount(df, settings, options)
    return df


def check_and_correct_continuity(
    df: pd.DataFrame, settings: dict, options: dict
) -> pd.DataFrame:
    """Prüfe, ob die Zeitstempel kontinuierlich sind und korrigiere sie bei Bedarf"""
    # Prüfe, ob die Zeitstempel kontinuierlich sind und ob Sommer-/Winterzeit-Umstellungen enthalten sind
    temp_df = pd.DataFrame()
    start = df["datetime"].min()
    end = df["datetime"].max()
    intervall = settings["Intervall"]
    temp_df["datetime"] = pd.date_range(start=start, end=end, freq=f"{intervall}min")
    # Finde alle abweichenden Zeitstempel
    abweichende_zeitstempel = df["datetime"][~df["datetime"].isin(temp_df["datetime"])]
    if not abweichende_zeitstempel.empty:
        if options.get("etl_steps", False):
            st.info(
                f"Abweichende Zeitstempel im DataFrame: {[dt.strftime('%Y-%m-%d %H:%M:%S') for dt in abweichende_zeitstempel[:10]]}"
            )
        idxs = df.index[~df["datetime"].isin(temp_df["datetime"])]
        expected_times = temp_df["datetime"][0 : len(idxs)].values
        df.loc[idxs, "datetime"] = expected_times
        if options.get("etl_steps", False):
            st.success(
                f"{len(idxs)} abweichende Zeitstempel wurden auf die erwarteten Werte korrigiert."
            )
    else:
        if options.get("etl_steps", False):
            st.success("Alle Zeitstempel sind korrekt und kontinuierlich.")
    return df


def scale_dataframe(df: pd.DataFrame, settings: dict, options: dict) -> pd.DataFrame:
    """Skaliere die Datenreihe auf den Zielgesamtwert (kWh) oder Zielspitzenwert (kW)"""
    # Skaliere die Datenreihe auf den Zielgesamtwert (kWh) oder Zielspitzenwert (kW)
    if "Zielgesamtwert" in settings and settings["Zielgesamtwert"] is not None:
        interval_hours = settings.get("Intervall", 15) / 60
        current_kwh_total = (df["kW"] * interval_hours).sum()
        if options.get("etl_steps", False):
            st.warning("Datenreihe wird auf Zielgesamtwert skaliert (kWh Basis)")
        scale_factor = settings["Zielgesamtwert"] / current_kwh_total
        df["kW"] = df["kW"] * scale_factor
        if options.get("etl_steps", False):
            show_dataframe_info(df, "kW")

    if "Zielspitzenwert" in settings and settings["Zielspitzenwert"] is not None:
        interval_hours = settings.get("Intervall", 15) / 60
        current_kwh_total = (df["kW"] * interval_hours).sum()
        if options.get("etl_steps", False):
            st.warning("Datenreihe wird auf Zielspitzenwert skaliert (kW Basis)")
        current_peak_kw = df["kW"].max()
        scale_factor = settings["Zielspitzenwert"] / current_peak_kw
        df["kW"] = df["kW"] * scale_factor
        if options.get("etl_steps", False):
            show_dataframe_info(df, "kW")
    return df


def show_dataframe_info(df: pd.DataFrame, col=None):
    """Zeige grundlegende Informationen über den DataFrame an"""
    # Anzahl der gefundenen und geladenen Zeilen ausgeben
    st.markdown("**High-Level Analyse der Zeitstempel**")
    st.markdown(f"- Anzahl der geladenen Zeilen: {df.shape[0]}")
    st.markdown(f"- Anzahl der Spalten: {df.shape[1]} ({', '.join(df.columns)})")
    # Gib das Datum und die Uhrzeit der ersten und letzten Zeile aus
    df["date"] = df["datetime"].dt.date
    st.markdown(f"- Erstes Datum: {df['date'].min()}")
    st.markdown(f"- Letztes Datum: {df['date'].max()}")
    unique_dates = df["date"].nunique()
    st.markdown(f"- Anzahl der einzigartigen Tage: {unique_dates}")
    first_datetime = df["datetime"].iloc[0]
    last_datetime = df["datetime"].iloc[-1]
    st.markdown(f"- Erste Uhrzeit: {first_datetime.strftime('%H:%M:%S')}")
    st.markdown(f"- Letzte Uhrzeit: {last_datetime.strftime('%H:%M:%S')}")
    if col is not None:
        total = df[col].sum()
        peak = df[col].max()
        st.markdown(f"- Spitzenwert der Datenspalte: {peak}")
        st.markdown(f"- Summe der Datenspalte: {total}")
    # Lösche die Spalte 'date', da sie nicht mehr benötigt wird
    df.drop(columns=["date"], inplace=True)


# Hilfsfunktion: Aggregiert alle Bundles stündlich
@st.cache_data
def create_hourly_bundles(bundles: List[Datenbundle]) -> List[Datenbundle]:
    """Aggregiere alle Datenbundles stündlich."""
    hourly_bundles = []
    for bundle in bundles:
        df = bundle.df.copy()
        # Stelle sicher, dass datetime Spalte vorhanden ist
        if "datetime" not in df.columns:
            continue
        value_col = "kW"

        # Gruppiere nach Stunde
        df["hour"] = df["datetime"].dt.floor("h")

        # For kW data, take mean; for kWh data, sum
        if value_col == "kW":
            agg_df = df.groupby("hour", as_index=False).agg(
                {
                    value_col: "mean",  # Average power over the hour
                }
            )
        else:
            agg_df = df.groupby("hour", as_index=False).agg(
                {
                    value_col: "sum",  # Sum energy over the hour
                }
            )

        # Übernehme weitere Metadaten
        agg_df["datetime"] = agg_df["hour"]
        agg_df["name"] = bundle.description
        # Erstelle neues Datenbundle mit aggregierten Daten
        hourly_bundle = Datenbundle(
            df=agg_df,
            description=bundle.description,
            interval=60,
            is_last=bundle.is_last,
            is_erzeugung=bundle.is_erzeugung,
            farbe=bundle.farbe,
        )
        hourly_bundles.append(hourly_bundle)
    return hourly_bundles


# Hilfsfunktion: Aggregiert alle Bundles wochentagsweise (Mo-Fr)
@st.cache_data
def create_weekly_bundles(bundles: List[Datenbundle]) -> List[Datenbundle]:
    """Aggregiere alle Datenbundles wochentagsweise (Mo-Fr)."""
    weekly_bundles = []
    for bundle in bundles:
        df = bundle.df.copy()
        if "datetime" not in df.columns:
            continue
        value_col = "kW"

        # Woche bestimmen: ISO-Woche (Montag bis Sonntag)
        df["week"] = df["datetime"].dt.to_period("W-MON").dt.start_time

        # For kW data, take mean; for kWh data, sum
        if value_col == "kW":
            agg_df = df.groupby("week", as_index=False).agg(
                {
                    value_col: "mean",  # Average power over the week
                }
            )
        else:
            agg_df = df.groupby("week", as_index=False).agg(
                {
                    value_col: "sum",  # Sum energy over the week
                }
            )

        agg_df["datetime"] = agg_df["week"]
        agg_df["name"] = bundle.description
        weekly_bundle = Datenbundle(
            df=agg_df,
            description=bundle.description,
            interval=7 * 24 * 60,  # Minuten pro Woche (Mo-So)
            is_last=bundle.is_last,
            is_erzeugung=bundle.is_erzeugung,
            farbe=bundle.farbe,
        )
        weekly_bundles.append(weekly_bundle)
    return weekly_bundles


# Hilfsfunktion: Aggregiert alle Bundles monatlich
@st.cache_data
def create_monthly_bundles(bundles: List[Datenbundle]) -> List[Datenbundle]:
    """Aggregiere alle Datenbundles monatlich."""
    monthly_bundles = []
    for bundle in bundles:
        df = bundle.df.copy()
        if "datetime" not in df.columns:
            continue
        value_col = "kW"

        # Gruppiere nach Monat
        df["month"] = df["datetime"].dt.to_period("M").dt.to_timestamp()

        # For kW data, take mean; for kWh data, sum
        if value_col == "kW":
            agg_df = df.groupby("month", as_index=False).agg(
                {
                    value_col: "mean",  # Average power over the month
                }
            )
        else:
            agg_df = df.groupby("month", as_index=False).agg(
                {
                    value_col: "sum",  # Sum energy over the month
                }
            )

        agg_df["datetime"] = agg_df["month"]
        agg_df["name"] = bundle.description
        monthly_bundle = Datenbundle(
            df=agg_df,
            description=bundle.description,
            interval=30 * 24 * 60,  # ca. Minuten pro Monat
            is_last=bundle.is_last,
            is_erzeugung=bundle.is_erzeugung,
            farbe=bundle.farbe,
        )
        monthly_bundles.append(monthly_bundle)
    return monthly_bundles


def timer(description: str = "", opt_timer: bool = False):
    """Einfache Timer-Funktion zur Messung der Ausführungszeit von Codeabschnitten."""
    if not hasattr(timer, "last_time"):
        timer.last_time = time.time()  # type: ignore
        if opt_timer:
            st.write("Timer gestartet")
        # return "0.00"
    else:
        current_time = time.time()
        elapsed = current_time - timer.last_time  # type: ignore
        timer.last_time = current_time  # type: ignore
        if opt_timer:
            st.write(f"{description}: {elapsed:.2f} Sekunden")  # type: ignore
        # return f"{elapsed:.2f}"


def get_etl_step_description(step_name: str) -> str:
    """
    Gibt eine benutzerfreundliche Beschreibung für jeden ETL-Schritt zurück.
    """
    descriptions = {
        "read_csv_file2": "📥 Extract: CSV-Datei laden und parsen",
        "create_datetime_index": "🗓️ Transform: Datetime-Index aus Zeitstempel erstellen",
        "check_and_fix_right_interval": "⏱️ Transform: Zeitintervalle validieren und korrigieren",
        "check_and_remove_leap_day": "📅 Transform: Schaltjahres-Tage entfernen für Konsistenz",
        "check_and_correct_continuity": "🔗 Transform: Datenkontinuität prüfen und korrigieren",
        "check_and_convert_to_kW": "⚡ Transform: Einheiten zu kW konvertieren und validieren",
        "scale_dataframe": "📊 Load: Daten skalieren und finale Struktur erstellen",
    }
    return descriptions.get(step_name, f"🔧 {step_name}: Datenverarbeitungsschritt")


def load_and_transform_data(config_path: str, options: dict) -> Datenbundle:
    """
    Load CSV data from file_path and apply transformations based on settings.
    """
    print(f"Lade und transformiere Daten aus: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        st.error(f"Config file not found: {config_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decoding JSON from config file: {config_path}")
        return None

    print(f"Lade und transformiere Daten aus: {settings.get('Dateipfad', '')}")

    #    df = read_csv_file(
    #        path=settings.get('Datei', ''),
    #        skiprows=settings.get('Startzeile', 0),
    #        decimal=settings.get('Dezimaltrennzeichen', ','),
    #        sep=settings.get('Spaltentrennzeichen', ';')
    #    )
    #    if settings.get('Invertiert', False):
    #        st.warning("Daten werden invertiert (negativ)")
    #        df[settings['Datenspalte']] = -df[settings['Datenspalte']]
    #    if settings.get('offset', 0) != 0:
    #        offset = settings['offset']
    #        st.warning(f"Daten werden um {offset} Intervalle verschoben")
    #        # Nur die Datenspalte verschieben, Datum-Zeit-Spalte bleibt unverändert
    #        df[settings['Datenspalte']] = df[settings['Datenspalte']].shift(offset)
    #        # Leere (NaN) Werte in der Datenspalte mit 0 auffüllen, Datum-Zeit bleibt erhalten
    #        df[settings['Datenspalte']].fillna(0, inplace=True)

    jobs = [
        read_csv_file2,
        create_datetime_index,
        check_and_fix_right_interval,
        check_and_remove_leap_day,
        check_and_correct_continuity,
        check_and_convert_to_kW,
        scale_dataframe,
    ]

    #    df = create_datetime_index(df, settings)
    #    df = check_and_fix_right_interval(df, settings)
    #    df = check_rowcount(df, settings)
    #    df = check_and_remove_leap_day(df, settings)
    #    df = check_and_correct_continuity(df, settings)
    #    df = process_power_data(df, settings)
    #    df = scale_dataframe(df, settings)

    df = pd.DataFrame()  # Initialisiere df hier
    etl_steps = []  # Liste der durchgeführten ETL-Schritte

    for job in jobs:
        step_name = job.__name__
        df = job(df, settings, options)
        timer(f"{step_name} abgeschlossen", options.get("timer", False))
        print(f"{step_name} abgeschlossen. Spalten: {list(df.columns)}")

        # ETL-Schritt verfolgen
        etl_steps.append(
            {
                "step": step_name,
                "rows": df.shape[0] if not df.empty else 0,
                "columns": list(df.columns) if not df.empty else [],
                "description": get_etl_step_description(step_name),
            }
        )

        if options.get("etl_steps", False):
            st.write(f"**ETL-Schritt:** {step_name}")
            st.write(f"  - Beschreibung: {get_etl_step_description(step_name)}")
            st.write(f"  - Resultat: {df.shape[0]} Zeilen, {df.shape[1]} Spalten")
            if not df.empty:
                st.write(f"  - Spalten: {', '.join(df.columns)}")

        if options.get("show_dataframe_infos", False):
            st.write(
                f"**Nach Schritt:** {get_etl_step_description(step_name)} - *{settings.get('Name', 'Unbekannte Datenreihe')}*"
            )
            show_dataframe_infos = st.expander("ℹ️ Infos zum Dataframe")
            with show_dataframe_infos:
                st.write(f"**Form:** {df.shape}")
                st.write("**Spalten:**")
                st.write(df.dtypes)
                st.write("**Erste 5 Zeilen:**")
                st.write(df.head())
                st.write("**Letzte 5 Zeilen:**")
                st.write(df.tail())
                st.write("**Statistik:**")
                st.write(df.describe(include="all"))

    datenbundle = Datenbundle(
        df=df,
        description=settings.get("Name", ""),
        interval=settings["Intervall"],
        is_last=settings["Typ"] == "Last",
        is_erzeugung=settings["Typ"] == "Erzeugung",
        farbe=settings.get("Farbe", "#1f77b4"),
    )
    return datenbundle
