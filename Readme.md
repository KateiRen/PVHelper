# PVHelper - Photovoltaik Datenanalyse Tool

Ein umfassendes **Streamlit-basiertes Analysetool** für Photovoltaik- und Energiedaten mit interaktiver Visualisierung und flexibler JSON-Konfiguration.

## 🎯 Überblick

PVHelper ist ein spezialisiertes Tool zur Analyse von Energiezeitreihen, insbesondere für:
- **Photovoltaik-Erzeugungsdaten** (Leistung und Energie)
- **Stromverbrauchsdaten** (Lastgänge)
- **Eigenverbrauchsanalysen** (PV + Verbrauch)
- **Mehrere Datenreihen** gleichzeitig vergleichen
- **Zeitintervalle**: 15min, 60min und benutzerdefiniert

Das Tool arbeitet primär mit **kW-Leistungsdaten** und berechnet automatisch **kWh-Energiewerte** basierend auf den Zeitintervallen.

## ✨ Hauptfeatures

### 📊 **Datenanalyse (`analyze.py`)**
- **Multi-Datenreihen-Vergleich**: Bis zu 3 Datenreihen gleichzeitig analysieren
- **Projektbasierte Organisation**: Daten in `projects/` Ordnern strukturiert
- **JSON-Konfiguration**: Flexible Einstellungen pro Datenreihe
- **Automatische Zeitaggregation**: Stündlich, wöchentlich, monatlich
- **Eigenverbrauchsberechnung**: Automatische Berechnung bei Last + Erzeugung
- **Stärkste Perioden**: Analyse der stärksten Monate/Wochen
- **Interaktive Diagramme**: Plotly-basierte Visualisierungen
- **Statistische Auswertungen**: Umfassende Kennzahlen

### 🎨 **Visualisierung (`pv_visualizer.py`)**
- **Interaktive Dashboards**: Streamlit-basierte Benutzeroberfläche
- **Heatmaps**: Leistungsverteilung über Tag/Jahr
- **Zeitreihendiagramme**: Detaillierte Verlaufsanalysen
- **Tagesprofile**: Durchschnittliche Stunden-Patterns
- **Monatsvergleiche**: Saisonale Analysen
- **Export-Funktionen**: CSV-Download der Daten
- **Flexible Zeitbereiche**: Datums-Filter für Detailanalysen

### ⚙️ **Datenverarbeitung (`helper.py`)**
- **CSV-Import**: Flexibler Import mit konfigurierbaren Parametern
- **Einheitenkonvertierung**: Automatische kW/kWh-Umrechnung
- **Zeitstempel-Korrektur**: Korrektur von Intervall-Fehlern
- **Datenvalidierung**: Kontinuitätsprüfung und Fehlerkorrektur
- **Skalierung**: Anpassung auf Zielwerte (Spitze/Gesamt)
- **Schaltjahr-Behandlung**: Automatische 29. Februar-Bereinigung
- **Bundle-System**: Strukturierte Datencontainer mit Metadaten

## 🏗️ Projektstruktur

```
PVHelper/
├── 📊 analyze.py           # Hauptanalyse-Tool (Streamlit)
├── 🎨 pv_visualizer.py     # Visualisierung-Dashboard
├── ⚙️ helper.py            # Datenverarbeitungs-Funktionen
├── 🔧 create_pv_reference.py # Referenzdaten-Generator
├── 📋 requirements.txt     # Python-Abhängigkeiten
├── 📚 Readme.md           # Diese Dokumentation
├── 📝 ToDo.md             # Entwicklungsaufgaben
├── 🔒 .gitignore          # Git-Ausschlüsse (schützt Daten)
└── 📁 projects/           # Projektdaten (Git-ignoriert)
    └── (Ihre Projektdaten)
```

## 🚀 Schnellstart

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Datenstruktur vorbereiten
```
projects/
└── IhrProjekt/
    ├── datenreihe1.json   # Konfiguration für erste Datenreihe
    ├── datenreihe2.json   # Konfiguration für zweite Datenreihe
    └── data/
        ├── data1.csv      # CSV-Rohdaten
        └── data2.csv      # Weitere CSV-Daten
```

### 3. JSON-Konfiguration erstellen
```json
{
  "Name": "Beispiel Datenreihe",
  "Datei": "data/beispiel_data.csv",
  "Startzeile": 1,
  "Dezimaltrennzeichen": ",",
  "Spaltentrennzeichen": ";",
  "Datumspalte": "Datum",
  "Zeitspalte": "Uhrzeit", 
  "Datum-Zeit-Format": "%d.%m.%Y %H:%M",
  "Datenspalte": "Wert",
  "Einheit": "kW",
  "Intervall": 15,
  "is_erzeugung": false,
  "Farbe": "#1f77b4"
}
```

### 4. Analyse starten
```bash
streamlit run analyze.py
```

### 5. Visualisierung starten
```bash
streamlit run pv_visualizer.py
```

## � JSON-Konfiguration

### Erforderliche Parameter
| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `Name` | Beschreibung der Datenreihe | `"Beispiel Datenreihe"` |
| `Datei` | Pfad zur CSV-Datei | `"data/beispiel_data.csv"` |
| `Datenspalte` | Spalte mit Leistungs-/Energiedaten | `"Wert"` |
| `Einheit` | Einheit der Daten | `"kW"` oder `"kWh"` |
| `Intervall` | Zeitintervall in Minuten | `15`, `60` |

### Zeitstempel-Konfiguration
| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `Datumspalte` | Spalte mit Datum | `"Datum"` |
| `Zeitspalte` | Spalte mit Uhrzeit | `"Uhrzeit"` |
| `Datum-Zeit-Spalte` | Combined DateTime Spalte | `"DateTime"` |
| `Datum-Zeit-Format` | Format-String | `"%d.%m.%Y %H:%M"` |

### CSV-Import-Parameter
| Parameter | Beschreibung | Standard |
|-----------|--------------|----------|
| `Startzeile` | Erste Datenzeile (0-indexiert) | `0` |
| `Dezimaltrennzeichen` | Dezimalzeichen | `","` |
| `Spaltentrennzeichen` | CSV-Delimiter | `";"` |

### Analyseparameter
| Parameter | Beschreibung | Standard |
|-----------|--------------|----------|
| `is_erzeugung` | Ist Erzeugungsdaten | `false` |
| `is_last` | Ist Verbrauchsdaten | `false` |
| `Invertiert` | Daten negieren | `false` |
| `Farbe` | Hex-Farbe für Diagramme | `"#1f77b4"` |

### Skalierungsparameter (optional)
| Parameter | Beschreibung | Einheit |
|-----------|--------------|---------|
| `Zielgesamtwert` | Skalierung auf Jahres-kWh | `kWh/Jahr` |
| `Zielspitzenwert` | Skalierung auf Peak-Leistung | `kW` |

## 💡 Anwendungsbeispiele

### Eigenverbrauchsanalyse
1. **PV-Erzeugung konfigurieren** (`is_erzeugung: true`)
2. **Verbrauch konfigurieren** (`is_last: true`)
3. **Beide Datenreihen in analyze.py laden**
4. **"Berechnungen durchführen" aktivieren**
5. **Eigenverbrauch, Einspeisung, Fremdbezug werden automatisch berechnet**

### Mehrere PV-Anlagen vergleichen
1. **Verschiedene JSON-Konfigurationen erstellen**
2. **Unterschiedliche Farben vergeben**
3. **In analyze.py gleichzeitig laden**
4. **Stärkste Perioden nach gewünschter Anlage analysieren**

### Zeitreihenanalyse
1. **Daten in pv_visualizer.py laden**
2. **Zeitbereich mit Slider einschränken**
3. **Heatmap für Tages-/Jahresverteilung**
4. **Tagesprofile für typische Verläufe**
5. **CSV-Export für weitere Analysen**

## ⚠️ Datensicherheit

### .gitignore Schutz
Das Repository ist so konfiguriert, dass **keine sensiblen Daten** übertragen werden:
- `projects/` - Gesamter Projektordner
- `*.csv` - Alle CSV-Dateien
- `*.json` - Alle JSON-Konfigurationen
- `*.parquet` - Alle verarbeiteten Dateien

### Empfohlene Struktur
```
PVHelper/                 # ✅ Versioniert
├── *.py                  # ✅ Python-Skripte
├── requirements.txt      # ✅ Abhängigkeiten
├── Readme.md            # ✅ Dokumentation
└── projects/            # ❌ Nicht versioniert
    └── (Ihre Daten)     # ❌ Lokal geschützt
```

## 🔧 Entwicklung

### Abhängigkeiten
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
numpy>=1.24.0
openpyxl>=3.1.0
```

### Code-Struktur
- **`helper.py`**: Kern-Datenverarbeitung, Bundle-System
- **`analyze.py`**: Streamlit-App für Analyse und Vergleiche
- **`pv_visualizer.py`**: Streamlit-App für Visualisierung
- **`create_pv_reference.py`**: Tool für Referenzdaten-Erzeugung

### Erweiterungen
Das modulare Design ermöglicht einfache Erweiterungen:
- Neue Datenquellen in `helper.py` hinzufügen
- Zusätzliche Visualisierungen in den Streamlit-Apps
- Erweiterte Berechnungen im Bundle-System

## 📞 Support

Bei Fragen oder Problemen:
1. **Prüfen Sie die JSON-Konfiguration** auf korrekte Parameter
2. **Kontrollieren Sie CSV-Dateiformat** und Pfade
3. **Aktivieren Sie Timer und DataFrame-Infos** für Debugging
4. **Konsultieren Sie die Streamlit-Logs** für Fehlermeldungen

---

*PVHelper - Professionelle Energiedatenanalyse mit Streamlit* 🌞⚡

**Verwendung**:
```bash
streamlit run preprocess.py
```

#### `create_pv_reference.py` - PV-Referenzdaten-Generator
**Zweck**: Generierung von PV-Referenzdaten aus normierten CSV-Dateien
**Features**:
- **Multi-Orientierung**: Ost/Süd/West PV-Ausrichtungen
- **Peak-Power-Skalierung**: Anpassung auf gewünschte Anlagengrößen
- **kW-basierte Ausgabe**: Direkte Leistungsdaten mit kWh-Berechnung
- **Validierte Profile**: Realistische PV-Ertragskurven

**Verwendung**:
```bash
python create_pv_reference.py
```

#### `test_kw_conversion.py` - Umfassende Validierung
**Zweck**: Vollständige Testsuite für kW-Konvertierung und Systemvalidierung
**Features**:
- **40 Testszenarien**: Core-Funktionalität + erweiterte Szenarien
- **Mathematische Genauigkeit**: Machine-level Präzision (0.00e+00 Fehler)
- **Timestamp-Tests**: Links-/rechtsbündige Ausrichtung für 15min und 60min
- **Performance-Tests**: Große Datensätze (35.000+ Datenpunkte) in <1 Sekunde
- **Edge-Case-Validierung**: Zero-Werte, NaN, Ausreißer, Sprungstellen
- **Real-World-Szenarien**: Load-Profile, Wind, Industrie, Batterie, Mischsysteme

**Verwendung**:
```bash
python test_kw_conversion.py
```

### 📊 **Arbeiten mit verarbeiteten Dateien (Processed Files)**

#### `pv_visualizer.py` - Hauptvisualisierung
**Zweck**: Interaktive Analyse und Visualisierung von verarbeiteten PV-Daten
**Features**:
- **Multi-Dataset-Vergleiche**: Laden und Vergleich mehrerer Datensätze
- **Interaktive Visualisierungen**: Plotly-basierte Charts für kW-Leistung und kWh-Energie
- **Intelligente Aggregation**: 
  - **kW-Daten**: Mittelwerte für Leistungsanalysen
  - **kWh-Daten**: Summen für Energieberechnungen
- **Typ-spezifische Analysen**: Unterschiedliche Behandlung von Erzeugung vs. Verbrauch
- **kWh-Totals Display**: Übersicht über Energiesummen verschiedener Zeiträume

**Verwendung**:
```bash
streamlit run pv_visualizer.py
```

#### `inspector.py` - Daten-Inspektor
**Zweck**: Detaillierte Analyse und Inspektion von verarbeiteten Parquet-Dateien
**Features**:
- **Datenqualitäts-Checks**: Vollständigkeit, Kontinuität, Plausibilität
- **Statistiken**: Min/Max/Mittelwert für kW und kWh-Daten
- **Zeitreihen-Analyse**: Lückenerkennnung, Intervall-Validierung
- **Metadaten-Anzeige**: Verarbeitungseinstellungen und Transformationen

**Verwendung**:
```bash
streamlit run inspector.py
```

### 🔨 **Support-Dateien**

#### `helper.py` - Kernfunktionen
**Zweck**: Zentrale Hilfsfunktionen für alle anderen Scripts
**Wichtige Funktionen**:
- **`process_power_data()`**: kW-basierte Datenverarbeitung
- **`calculate_kwh_from_kw()`**: Präzise kWh-Berechnung aus kW-Daten
- **`show_kwh_totals()`**: kWh-Summen-Display für verschiedene Zeiträume
- **`check_and_fix_right_interval()`**: Timestamp-Alignment-Korrektur
- **`scale_dataframe()`**: Peak-Power-Skalierung
- **Aggregationsfunktionen**: Stunden-, Wochen-, Monats-Bündelung
- **Backward Compatibility**: Erhaltung alter kWh-basierter Funktionen

#### `app6.py` - Legacy-App
**Zweck**: Ursprüngliche kWh-basierte Anwendung (für Referenz)
**Status**: Legacy - durch `pv_visualizer.py` ersetzt

## 🚀 Installation

### Voraussetzungen
- Python 3.8+
- Git

### Setup
1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd PVHelper
   ```

2. **Virtuelle Umgebung erstellen**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Workflow

### 1. **Quelldaten verarbeiten**
```bash
# Schritt 1: CSV-Daten vorverarbeiten
streamlit run preprocess.py

# Schritt 2: PV-Referenzdaten erstellen (optional)
python create_pv_reference.py

# Schritt 3: System validieren (empfohlen)
python test_kw_conversion.py
```

### 2. **Verarbeitete Daten analysieren**
```bash
# Hauptanalyse und Visualisierung
streamlit run pv_visualizer.py

# Detaillierte Dateninspektion
streamlit run inspector.py
```

## 📁 Projektstruktur

```
PVHelper/
├── sources/                    # Quelldaten und Konfigurationen
│   ├── datafiles/             # CSV-Rohdaten (strukturiert)
│   └── *.json                 # Konfigurationsdateien
├── processed/                 # Verarbeitete Daten
│   ├── *.parquet             # Optimierte Datenformate (kW-basiert)
│   ├── *_settings.json       # Verarbeitungseinstellungen
│   └── *_transformations.md  # Dokumentation der Schritte
├── 
├── # === QUELLDATEN-VERARBEITUNG ===
├── preprocess.py              # Hauptvorverarbeitung (Streamlit)
├── create_pv_reference.py     # PV-Referenzdaten-Generator
├── test_kw_conversion.py      # Vollständige Testsuite (40 Tests)
├── 
├── # === VERARBEITETE-DATEN-ANALYSE ===
├── pv_visualizer.py           # Hauptvisualisierung (Streamlit)
├── inspector.py               # Daten-Inspektor (Streamlit)
├── 
├── # === SUPPORT-DATEIEN ===
├── helper.py                  # Kernfunktionen und Utilities
├── app6.py                    # Legacy-App (kWh-basiert)
├── 
├── requirements.txt           # Python-Abhängigkeiten
├── .gitignore                # Git-Ausschlüsse
└── README.md                 # Diese Datei
```

## ⚙️ Konfiguration

### JSON-Konfigurationsdateien
Jeder Datensatz benötigt eine JSON-Konfigurationsdatei im `sources/` Ordner:

**Neue kW-basierte Konfiguration (empfohlen):**
```json
{
    "Name": "PV-Anlage Mehrfachausrichtung",
    "Datei": "sources/datafiles/pv/pv_ost_sued_west.csv",
    "Startzeile": 0,
    "Intervall": 15,
    "Einheit": "kW",
    "Delimiter": ";",
    "Dezimalpunkt": ",",
    "Datenspalte": "Wert (kW)",
    "Datum-Zeit-Spalte": "Zeitstempel",
    "Datum-Zeit-Format": "%Y-%m-%d %H:%M",
    "Typ": "Erzeugung",
    "kWh_Totals_Available": true,
    "kWh_Columns": ["Wert (kWh)", "PV_east_kWh", "PV_south_kWh", "PV_west_kWh"],
    "Zielspitzenwert": 100.0
}
```

**Batteriespeicher-Konfiguration:**
```json
{
    "Name": "Batteriespeicher Haus",
    "Datei": "sources/datafiles/battery/battery_storage.csv",
    "Startzeile": 0,
    "Intervall": 15,
    "Einheit": "kW",
    "Delimiter": ";",
    "Dezimalpunkt": ",",
    "Datenspalte": "Battery_kW",
    "Datum-Zeit-Spalte": "Zeitstempel",
    "Datum-Zeit-Format": "%Y-%m-%d %H:%M",
    "Typ": "Speicher",
    "Beschreibung": "Positive Werte = Entladung, Negative Werte = Ladung"
}
```

**Legacy kWh-basierte Konfiguration (weiterhin unterstützt):**
```json
{
    "Name": "Legacy Lastgang",
    "Datei": "sources/datafiles/legacy/lastgang.csv",
    "Startzeile": 0,
    "Intervall": 60,
    "Einheit": "kWh",
    "Delimiter": ";",
    "Dezimalpunkt": ",",
    "Datenspalte": "Wert (kWh)",
    "Datum-Zeit-Spalte": "Zeitstempel",
    "Datum-Zeit-Format": "%Y-%m-%d %H:%M",
    "Typ": "Last"
}
```

### Unterstützte Parameter
- **Intervall**: 1, 5, 10, 15, 30, 60, 120, 180 Minuten
- **Einheit**: 
  - **"kW"** (empfohlen): Primäre Leistungsdaten, kWh wird berechnet
  - **"kWh"** (legacy): Direkte Energiedaten, kW wird abgeleitet
- **Typ**: "Last" (Verbrauch), "Erzeugung" (PV/Wind), "Speicher" (Batterie)
- **kWh_Totals_Available**: Ob kWh-Totale verfügbar sind
- **kWh_Columns**: Liste der verfügbaren kWh-Spalten
- **Zielgesamtwert**: Optionale Skalierung auf Gesamtwert (kWh-Basis)
- **Zielspitzenwert**: Optionale Skalierung auf Spitzenleistung (kW-Basis)

## 🔧 Neue kW-basierte Datenverarbeitungs-Pipeline

1. **CSV-Import** mit konfigurierbaren Parametern
2. **Datetime-Erstellung** aus einzelnen oder kombinierten Spalten
3. **🆕 Timestamp-Alignment**: Automatische Korrektur rechtsbündiger Zeitstempel
4. **Intervall-Normalisierung** (linksbündig für alle Intervaltypen)
5. **Zeilenzahl-Validierung** gegen erwartete Werte
6. **🆕 kW-Datenverarbeitung** als Primäreinheit (`process_power_data()`)
7. **🆕 kWh-Berechnung** für Energieanalysen (`calculate_kwh_from_kw()`)
8. **Kontinuitätsprüfung** und Lücken-Korrektur
9. **Schaltjahr-Bereinigung** für Jahresvergleiche
10. **kW-basierte Skalierung** auf Zielwerte
11. **🆕 kWh-Totale Anzeige** für Energiesummen
12. **Export** als Parquet mit kW/kWh-Metadaten

## 🎨 Visualisierungen

### Leistungsanalyse (kW)
- **Leistungs-Zeitreihen**: Instantane kW-Werte über Zeit
- **Tages-/Stundenmuster**: Durchschnittliche kW-Leistung nach Tageszeit
- **Heatmaps**: kW-Leistungsmuster über Jahr/Tag-Matrix
- **Multi-Orientierung**: Separate Darstellung von Ost/Süd/West PV-Ausrichtungen

### Energieanalyse (kWh)
- **Monatliche Energietotale**: kWh-Summen pro Monat aus kW-Daten berechnet
- **Jahresertrag-Hochrechnung**: Normalisierte Energieberechnung
- **Orientierungsanalyse**: Anteil verschiedener PV-Orientierungen
- **Batteriezyklen**: Lade-/Entladeenergie-Bilanzen

### Kombinierte Analysen
- **Kapazitätsfaktor**: Verhältnis Durchschnitts- zu Spitzenleistung
- **Spezifischer Ertrag**: kWh/kWp-Berechnungen für PV-Anlagen
- **Vergleichsanalysen**: Multi-Dataset-Overlays (kW vs. kW, kWh-Totale)
- **Aggregierte Ansichten**: Stunden-, Wochen-, Monatsebene mit intelligenter Aggregation

## 🔄 Migration von kWh zu kW

Das Tool unterstützt sowohl legacy kWh-basierte als auch neue kW-basierte Workflows:

### Für bestehende kWh-Daten:
- Automatische Backward-Compatibility in `helper.py`
- kW-Ableitung aus kWh-Daten möglich
- Bestehende JSON-Konfigurationen funktionieren weiterhin

### Für neue kW-Daten:
- Setze `"Einheit": "kW"` in JSON-Konfiguration
- Nutze `"Datenspalte": "Wert (kW)"`
- Optional: `"kWh_Totals_Available": true` für Energieberechnungen

## ✅ Validierung und Qualitätssicherung

### Testsuite (`test_kw_conversion.py`)
**40 umfassende Tests** validieren:

#### Core-Funktionalität (7 Tests):
- kWh-Berechnungs-Genauigkeit (0.00e+00 Fehlertoleranz)
- Energieerhaltung bei Konvertierungen
- Verschiedene Zeitintervalle (15min, 30min, 60min)
- Datenverarbeitungs-Pipeline
- Rückwärtskompatibilität
- Skalierungsfunktionen
- Realistische PV-Szenarien

#### Erweiterte Szenarien (19 Tests):
- **Datentypen**: Load-Profile, Wind, Industrie, Batterie, Mischsysteme
- **Zeitstempel**: Links-/rechtsbündige Ausrichtung, verschiedene Formate
- **Intervalle**: 1min bis 180min, Boundary-Conditions
- **Edge Cases**: Zero-Werte, NaN, Ausreißer, Saisonalität
- **Performance**: Große Datensätze (35.000+ Punkte) in <1 Sekunde
- **Real-World**: Messfehler, Lücken, DST-Szenarien

**Erfolgsrate**: 100% (40/40 Tests bestanden)

## 🏗️ Architektur-Prinzipien

### kW-First-Ansatz
- **Primärdaten**: Leistung (kW) als Ausgangsbasis
- **Sekundärberechnungen**: Energie (kWh) aus Leistung und Zeit
- **Präzision**: Machine-level Genauigkeit bei Berechnungen

### Timestamp-Robustheit
- **Links-Alignment**: Standard (Zeitstempel = Intervallbeginn)
- **Rechts-Alignment**: Automatische Korrektur (Zeitstempel = Intervallende)
- **Flexibilität**: Unterstützung verschiedener Zeitformate

### Skalierbarkeit
- **Performance**: Sub-Sekunden-Verarbeitung für Jahresdaten
- **Memory**: Optimierte Parquet-Speicherung
- **Caching**: Intelligente Streamlit-Cache-Nutzung

## 🤝 Beitragen

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen implementieren
4. Tests ausführen (`python test_kw_conversion.py`)
5. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
6. Branch pushen (`git push origin feature/AmazingFeature`)
7. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt steht unter der [MIT Lizenz](LICENSE).

## 📞 Support

Bei Fragen oder Problemen:
1. **Validierung**: Tests ausführen mit `python test_kw_conversion.py`
2. **Issues**: GitHub Issues für Bugs/Feature-Requests
3. **Dokumentation**: `*_transformations.md` Dateien im `processed/` Ordner
4. **Konfiguration**: Beispiele im `sources/` Ordner

## 🔄 Roadmap

### Geplante Features
- **Zusätzliche Energietypen**: Netz-Einspeisung, Wärmepumpen
- **Erweiterte Visualisierungen**: 3D-Heatmaps, Animation
- **API-Integration**: Wetterservice, Marktpreise
- **Machine Learning**: Prognosemodelle für PV-Ertrag

### Bekannte Limitierungen
- **Maximale Intervalle**: 180 Minuten (3 Stunden)
- **Schaltjahr-Behandlung**: 29. Februar wird standardmäßig entfernt
- **Memory**: Sehr große Datensätze (>1 Million Punkte) können langsam werden

---

**Entwickelt für die effiziente Analyse von Energiezeitreihen in der Photovoltaik- und Stromverbrauchsanalyse mit kW-basierter Datenverarbeitung und machine-level Präzision.**
│   └── *_transformations.md  # Dokumentation der Schritte
├── preprocess.py              # Datenvorverarbeitung (Streamlit App)
├── analyze.py                 # Datenanalyse (Streamlit App)
├── helper.py                  # Hilfsfunktionen und Utilities
├── requirements.txt           # Python-Abhängigkeiten
├── .gitignore                # Git-Ausschlüsse
└── README.md                 # Diese Datei
```

## ⚙️ Konfiguration

### JSON-Konfigurationsdateien
Jeder Datensatz benötigt eine JSON-Konfigurationsdatei im `sources/` Ordner:

**Neue kW-basierte Konfiguration:**
```json
{
    "Name": "Beschreibender Name",
    "Datei": "sources/datafiles/pfad/zur/datei.csv",
    "Startzeile": 0,
    "Intervall": 15,
    "Einheit": "kW",
    "Delimiter": ";",
    "Dezimalpunkt": ",",
    "Datenspalte": "Wert (kW)",
    "Datum-Zeit-Spalte": "Zeitstempel",
    "Datum-Zeit-Format": "%Y-%m-%d %H:%M",
    "Typ": "Erzeugung",
    "kWh_Totals_Available": true,
    "kWh_Columns": ["Wert (kWh)", "PV_east_kWh", "PV_south_kWh", "PV_west_kWh"]
}
```

**Legacy kWh-basierte Konfiguration (weiterhin unterstützt):**
```json
{
    "Name": "Legacy Datensatz",
    "Datei": "sources/datafiles/legacy/datei.csv",
    "Startzeile": 0,
    "Intervall": 15,
    "Einheit": "kWh",
    "Delimiter": ";",
    "Dezimalpunkt": ",",
    "Datenspalte": "Wert (kWh)",
    "Datum-Zeit-Spalte": "Zeitstempel",
    "Datum-Zeit-Format": "%Y-%m-%d %H:%M",
    "Typ": "Last"
}
```

### Unterstützte Parameter
- **Intervall**: 15 oder 60 Minuten
- **Einheit**: 
  - **"kW"** (empfohlen): Primäre Leistungsdaten, kWh wird berechnet
  - **"kWh"** (legacy): Direkte Energiedaten, kW wird abgeleitet
- **Typ**: "Last" (Verbrauch), "Erzeugung" (PV-Produktion)
- **kWh_Totals_Available**: Ob kWh-Totale verfügbar sind (für kW-basierte Daten)
- **kWh_Columns**: Liste der verfügbaren kWh-Spalten
- **Zielgesamtwert**: Optionale Skalierung auf Gesamtwert (kWh-Basis)
- **Zielspitzenwert**: Optionale Skalierung auf Spitzenleistung (kW-Basis)

## 🔧 Neue kW-basierte Datenverarbeitungs-Pipeline

1. **CSV-Import** mit konfigurierbaren Parametern
2. **Datetime-Erstellung** aus einzelnen oder kombinierten Spalten
3. **Intervall-Normalisierung** (linksbündig)
4. **Zeilenzahl-Validierung** gegen erwartete Werte
5. **🆕 kW-Datenverarbeitung** als Primäreinheit (`process_power_data()`)
6. **🆕 kWh-Berechnung** für Energieanalysen (`calculate_kwh_from_kw()`)
7. **Kontinuitätsprüfung** und Lücken-Korrektur
8. **Schaltjahr-Bereinigung** für Jahresvergleiche
9. **kW-basierte Skalierung** auf Zielwerte
10. **🆕 kWh-Totale Anzeige** für Energiesummen
11. **Export** als Parquet mit kW/kWh-Metadaten

## 🎨 Visualisierungen

### Leistungsanalyse (kW)
- **Leistungs-Zeitreihen**: Instantane kW-Werte über Zeit
- **Tages-/Stundenmuster**: Durchschnittliche kW-Leistung nach Tageszeit
- **Heatmaps**: kW-Leistungsmuster über Jahr/Tag-Matrix

### Energieanalyse (kWh)
- **Monatliche Energietotale**: kWh-Summen pro Monat aus kW-Daten berechnet
- **Jahresertrag-Hochrechnung**: Normalisierte Energieberechnung
- **Orientierungsanalyse**: Anteil verschiedener PV-Orientierungen

### Kombinierte Analysen
- **Kapazitätsfaktor**: Verhältnis Durchschnitts- zu Spitzenleistung
- **Spezifischer Ertrag**: kWh/kWp-Berechnungen für PV-Anlagen
- **Vergleichsanalysen**: Multi-Dataset-Overlays (kW vs. kW, kWh-Totale)
- **Aggregierte Ansichten**: Stunden-, Wochen-, Monatsebene mit intelligenter Aggregation

## 🔄 Migration von kWh zu kW

Das Tool unterstützt sowohl legacy kWh-basierte als auch neue kW-basierte Workflows:

### Für bestehende kWh-Daten:
- Automatische Backward-Compatibility
- kW-Ableitung aus kWh-Daten möglich
- Bestehende JSON-Konfigurationen funktionieren weiterhin

### Für neue kW-Daten:
- Setze `"Einheit": "kW"` in JSON-Konfiguration
- Nutze `"Datenspalte": "Wert (kW)"`
- Optional: `"kWh_Totals_Available": true` für Energieberechnungen

## 🤝 Beitragen

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt steht unter der [MIT Lizenz](LICENSE).

## 📞 Support

Bei Fragen oder Problemen:
1. Issues auf GitHub erstellen
2. Dokumentation in den `*_transformations.md` Dateien prüfen
3. Konfigurationsbeispiele im `sources/` Ordner ansehen

## 🔄 Roadmap

Siehe [ToDo.md](ToDo.md) für geplante Features und bekannte Issues.

---

**Entwickelt für die effiziente Analyse von Energiezeitreihen in der Photovoltaik- und Stromverbrauchsanalyse.**