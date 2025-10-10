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
├── 🧪 test_kw_conversion.py # Test-Suite für Validierung
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
- **`test_kw_conversion.py`**: Test-Suite für Systemvalidierung

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