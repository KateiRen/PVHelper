# ToDos

## SPOT Preise

https://www.epexspot.com/en/market-results?market_area=DE-LU&auction=MRC&trading_date=2025-10-12&delivery_date=2025-10-13&underlying_year=&modality=Auction&sub_modality=DayAhead&technology=&data_mode=table&period=&production_period=&product=15

https://api-portal.netztransparenz.de/api-documentation



## helper.py

- [ ] weekly aggregate using mean?!
- [ ] monthly aggregate using mean?!
- [x] Name der Wertespalte in Databundle ablegen - obsolet, jetzt immer "kW"
- [x] implementiere offset um datenreihen zu schieben

### 🔧 Code-Qualität & Best Practices
- [ ] **BatteryStorage `__init__` Bug beheben**: `def _init_` sollte `def __init__` sein
- [ ] **Robustes Error Handling**: Try-catch für alle kritischen Operationen (Datei-IO, DataFrame-Operationen)
- [ ] **Input Validation**: Validierung für JSON-Konfigurationsparameter vor Verarbeitung
- [ ] **Type Hints vervollständigen**: Vollständige Type Annotations für alle Funktionen
- [ ] **Docstrings hinzufügen**: Dokumentation für alle öffentlichen Funktionen
- [ ] **Logging implementieren**: Strukturiertes Logging statt print() statements
- [ ] **Konstanten definieren**: Magic Numbers in Konstanten auslagern (z.B. Intervalle, Standardfarben)
- [ ] **Exception Classes**: Benutzerdefinierte Exceptions für bessere Fehlerbehandlung
- [ ] **Konfiguration validieren**: JSON-Schema-Validierung für Konfigurationsdateien

### 🧪 Testing & Qualitätssicherung
- [ ] **Unit Tests erstellen**: Test-Suite für alle ETL-Funktionen
- [ ] **Integration Tests**: Tests für komplette Datenverarbeitungspipeline
- [ ] **Test-Daten**: Beispiel-CSV und JSON-Dateien für automatisierte Tests
- [ ] **Performance Tests**: Benchmarks für große Datensätze
- [ ] **Code Coverage**: Mindestens 80% Test-Coverage erreichen


## analyze.py

- [ ] weitere funktionen nach helper.py verlagern
- [ ] einfachere und klarere Struktur
- [ ] Daten auf Stundenbasis unterstützen
- [x] Implementierung der Simulation des Stromspeichers, d.h. Berechnung Ladung, Entnahme, Selbstentladung als eigene Datenreihe und entsprechende Anpassung von Eigenverbrauch, Einspeisung, Fremdbezug und der Diagramme
    obere LAdegrenze! -> done
    Discharge Power / Charge Power Korrekt angewendet?
        Entladung von 100kWh mit 100KW
            1. von 100 kWh auf 76,2375 kWh
            2. von 76,2375 kWh 52,47797 kWh
            3. auf 28,72141 kWh
            Wirkungsgrad scheint umgekehrt zu wirken. Weniger Entladung als Abgabe
    Plausi check Ladung / Entladung
        Leistung
        Kapazität


### 🏗️ Architektur & Wartbarkeit
- [ ] **Modularisierung**: Große Funktionen in kleinere, testbare Einheiten aufteilen
- [ ] **State Management**: Session State besser strukturieren und dokumentieren
- [ ] **Konfiguration externalisieren**: UI-Optionen in separate Konfigurationsdatei
- [ ] **Code-Duplikation reduzieren**: Wiederholte Diagramm-Erstellung abstrahieren
- [ ] **Memory Management**: DataFrame-Caching optimieren für große Datensätze
- [ ] **Error Boundaries**: Graceful Fehlerbehandlung ohne kompletten App-Crash
- [ ] **Locale Setting**: Robuste Locale-Behandlung mit Fallback

### 🎨 User Experience
- [ ] **Loading States**: Progress-Indikatoren für längere Operationen
- [ ] **Help System**: Integrierte Hilfe-Tooltips und Dokumentation
- [ ] **Export-Funktionen**: Mehr Export-Formate (Excel, Parquet)
- [ ] **Undo/Redo**: Möglichkeit Aktionen rückgängig zu machen
- [ ] **Keyboard Shortcuts**: Wichtige Funktionen per Tastatur bedienbar
- [ ] **Mobile Responsiveness**: Bessere Darstellung auf kleinen Bildschirmen


## pv_visualizer.py

### 🎯 Feature-Vervollständigung
- [ ] **Vergleichsmodus**: Mehrere Datenreihen gleichzeitig visualisieren
- [ ] **Erweiterte Filter**: Zeitbereich, Wochentage, Monate selektierbar
- [ ] **Anomalie-Erkennung**: Automatische Identifikation ungewöhnlicher Werte
- [ ] **Trend-Analyse**: Langzeit-Trends und saisonale Muster
- [ ] **Reporting**: PDF-Export von Analyse-Reports


## 🚀 Gesamtprojekt - Deployment & Operations

### 📦 Packaging & Distribution
- [ ] **Docker Container**: Containerisierung für einfache Deployment
- [ ] **Requirements.txt optimieren**: Pinning von Versionen für Reproduzierbarkeit
- [ ] **CI/CD Pipeline**: GitHub Actions für automatisierte Tests und Deployment
- [ ] **Versionierung**: Semantic Versioning und Release-Management
- [ ] **Setup.py/pyproject.toml**: Ordentliche Python Package-Struktur

### 🔒 Security & Compliance
- [ ] **Input Sanitization**: Schutz vor Path-Traversal und Code-Injection
- [ ] **File Upload Validation**: Größen- und Format-Limits für CSV-Uploads
- [ ] **Error Messages**: Keine sensiblen Daten in Fehlermeldungen preisgeben
- [ ] **Dependency Scanning**: Regelmäßige Prüfung auf Sicherheitslücken
- [ ] **Data Privacy**: DSGVO-konforme Datenverarbeitung dokumentieren

### 📊 Monitoring & Performance
- [ ] **Performance Monitoring**: Tracking von Ladezeiten und Memory-Usage
- [ ] **Error Tracking**: Automatische Erfassung und Benachrichtigung bei Fehlern
- [ ] **Usage Analytics**: (Optional) Anonyme Nutzungsstatistiken
- [ ] **Health Checks**: Automatische Systemstatus-Überwachung
- [ ] **Resource Limits**: Schutz vor Memory/CPU-Überlastung

### 📚 Dokumentation & Wartung
- [ ] **API Documentation**: Vollständige Dokumentation aller öffentlichen Funktionen
- [ ] **Deployment Guide**: Schritt-für-Schritt Anleitung für Production-Setup
- [ ] **Troubleshooting Guide**: Häufige Probleme und Lösungsansätze
- [ ] **Migration Guide**: Versionswechsel und Breaking Changes dokumentieren
- [ ] **Contributing Guidelines**: Richtlinien für externe Beiträge

### 🧬 Erweiterbarkeit
- [ ] **Plugin-System**: Erweiterbare Architektur für zusätzliche Datenquellen
- [ ] **REST API**: HTTP-API für externe Integration
- [ ] **Database Support**: Optionale Persistierung in PostgreSQL/SQLite
- [ ] **Multi-Tenancy**: Unterstützung mehrerer Nutzer/Organisationen
- [ ] **Internationalization**: Multi-Language Support (EN/DE)

## 🎯 Prioritäten (Next Sprint)

### 🔴 Critical (Sofort)
1. **BatteryStorage `__init__` Bug beheben** - Verhindert korrekte Instanziierung
2. **Robustes Error Handling** - Verhindert App-Crashes bei fehlerhaften Daten
3. **Input Validation** - Schutz vor ungültigen Konfigurationen

### 🟡 High (Nächste 2 Wochen)
1. **Unit Tests erstellen** - Grundlage für sichere Weiterentwicklung
2. **Type Hints vervollständigen** - Bessere Code-Qualität und IDE-Support
3. **Modularisierung von analyze.py** - Wartbarkeit verbessern

### 🟢 Medium (Nächster Monat)
1. **Logging implementieren** - Besseres Debugging und Monitoring
2. **Performance Monitoring** - Optimierung für große Datensätze
3. **Docker Container** - Vereinfachtes Deployment

