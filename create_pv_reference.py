import os
import json
from datetime import datetime
import pandas as pd
from helper import get_unique_kw_column_name


csv_path = "sources/datafiles/Referenz/PV_series.csv"
output_dir = "processed/datafiles/Referenz"


def get_user_input():
    """Get scaling parameters from user via command prompt."""
    print("PV Reference Data Generator")
    print("=" * 40)
    print()
    
    # Ask for input method
    print("Choose input method:")
    print("1. Enter total peak power and percentages for each orientation")
    print("2. Enter peak power for each orientation directly")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    if choice == '1':
        # Method 1: Total peak power + percentages
        while True:
            try:
                total_peak_power = float(input("\nEnter total peak power in kWp: "))
                if total_peak_power > 0:
                    break
                print("Peak power must be positive")
            except ValueError:
                print("Please enter a valid number")
        
        while True:
            try:
                east_pct = float(input("Enter percentage for East orientation (0-100): "))
                south_pct = float(input("Enter percentage for South orientation (0-100): "))
                west_pct = float(input("Enter percentage for West orientation (0-100): "))
                
                total_pct = east_pct + south_pct + west_pct
                if abs(total_pct - 100) < 0.01:  # Allow small rounding errors
                    break
                print(f"Percentages must sum to 100%. Current sum: {total_pct:.1f}%")
            except ValueError:
                print("Please enter valid numbers")
        
        # Calculate individual peak powers
        east_peak = total_peak_power * east_pct / 100
        south_peak = total_peak_power * south_pct / 100
        west_peak = total_peak_power * west_pct / 100
        
    else:
        # Method 2: Direct peak powers
        while True:
            try:
                east_peak = float(input("\nEnter peak power for East orientation (kWp): "))
                south_peak = float(input("Enter peak power for South orientation (kWp): "))
                west_peak = float(input("Enter peak power for West orientation (kWp): "))
                
                if all(p >= 0 for p in [east_peak, south_peak, west_peak]):
                    total_peak_power = east_peak + south_peak + west_peak
                    break
                print("All peak powers must be non-negative")
            except ValueError:
                print("Please enter valid numbers")
    
    # Get configuration name
    name = input(f"\nEnter a name for this configuration - or press <Enter> to use default: ").strip()
    if not name:
        #name = f"PV Reference {total_peak_power:.0f}kWp"
        name = f"PV Reference {east_peak:.0f}kWpEast_{south_peak:.0f}kWpSouth_{west_peak:.0f}kWpWest"
    
    return {
        'name': name,
        'total_peak_power': total_peak_power,
        'east_peak': east_peak,
        'south_peak': south_peak,
        'west_peak': west_peak
    }


def load_and_process_data(config):
    """Load the CSV file and scale according to configuration."""
    print(f"\nProcessing data...")
    
    # Load CSV file
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path, sep=';', decimal=',')
    
    # Create datetime column
    df['datetime'] = pd.to_datetime(df['Date [UTC+1]'], format='%d.%m.%Y %H:%M')
    
    # The normalized data represents the fraction of annual energy per kWp for each 15-minute interval
    # For kW-based approach: convert normalized values to instantaneous power (kW)
    # Maximum power output should equal the peak power configuration
    
    print(f"Peak power configuration:")
    print(f"  East: {config['east_peak']:.2f} kWp")
    print(f"  South: {config['south_peak']:.2f} kWp") 
    print(f"  West: {config['west_peak']:.2f} kWp")
    print(f"  Total: {config['total_peak_power']:.2f} kWp")
    
    # Scale normalized values to achieve specified peak power for each orientation
    # Find the maximum normalized value for each orientation and scale accordingly
    east_scale = config['east_peak'] / df['PV_east_30_norm'].max() if df['PV_east_30_norm'].max() > 0 else 0
    south_scale = config['south_peak'] / df['PV_south_30_norm'].max() if df['PV_south_30_norm'].max() > 0 else 0
    west_scale = config['west_peak'] / df['PV_west_30_norm'].max() if df['PV_west_30_norm'].max() > 0 else 0
    
    # Create kW power columns (instantaneous power)
    df['PV_east_kW'] = df['PV_east_30_norm'] * east_scale
    df['PV_south_kW'] = df['PV_south_30_norm'] * south_scale  
    df['PV_west_kW'] = df['PV_west_30_norm'] * west_scale
    
    # Use unique kW column naming to avoid conflicts
    kw_column_name = get_unique_kw_column_name(df)
    df[kw_column_name] = df['PV_east_kW'] + df['PV_south_kW'] + df['PV_west_kW']
    
    # Also create kWh columns for backward compatibility and energy calculations
    interval_hours = 0.25  # 15 minutes = 0.25 hours
    df['PV_east_kWh'] = df['PV_east_kW'] * interval_hours
    df['PV_south_kWh'] = df['PV_south_kW'] * interval_hours
    df['PV_west_kWh'] = df['PV_west_kW'] * interval_hours
    df['Wert (kWh)'] = df[kw_column_name] * interval_hours
    
    # Add metadata columns
    df['date'] = df['datetime'].dt.date
    df['month_num'] = df['datetime'].dt.month
    df['month_name'] = df['datetime'].dt.strftime('%B')
    df['name'] = config['name']
    
    # Select final columns (kW columns first as primary)
    final_columns = [
        'datetime', kw_column_name, 'PV_east_kW', 'PV_south_kW', 'PV_west_kW',
        'Wert (kWh)', 'PV_east_kWh', 'PV_south_kWh', 'PV_west_kWh',
        'date', 'month_num', 'month_name', 'name'
    ]
    df_final = df[final_columns].copy()
    
    # Calculate annual yield and specific yield from kWh values
    annual_yield = df_final['Wert (kWh)'].sum()
    actual_specific_yield = annual_yield / config['total_peak_power'] if config['total_peak_power'] > 0 else 0
    
    # Find maximum power output (should match the configured peak power)
    max_power_kw = df_final[kw_column_name].max()
    
    print(f"\nResults:")
    print(f"  Annual yield: {annual_yield:,.0f} kWh")
    print(f"  Specific yield: {actual_specific_yield:.0f} kWh/kWp")
    print(f"  Maximum power output: {max_power_kw:.1f} kW ({max_power_kw/config['total_peak_power']*100:.1f}% of peak)")
    
    # Store calculated values in config for later use
    config['annual_yield'] = annual_yield
    config['specific_yield'] = actual_specific_yield
    config['max_power_kw'] = max_power_kw
    config['kw_column_name'] = kw_column_name
    
    return df_final, kw_column_name


def save_files(df, config, kw_column_name):
    """Save the processed data as parquet and JSON files."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate file names
    safe_name = "".join(c for c in config['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    parquet_path = os.path.join(output_dir, f"{safe_name}.parquet")
    json_path = os.path.join("processed", f"{safe_name}_settings.json")
    md_path = os.path.join(output_dir, f"{safe_name}_transformations.md")
    
    # Save parquet file
    df.to_parquet(parquet_path, index=False)
    print(f"\nSaved parquet file: {parquet_path}")
    
    # Create JSON configuration
    json_config = {
        "Name": config['name'],
        "Datei": parquet_path,
        "Intervall": 15,
        "Einheit": "kW",
        "Datenspalte": kw_column_name,
        "Datum-Zeit-Spalte": "datetime",
        "Typ": "Erzeugung",
        "Farbe": "#D4D100",
        "PV_Configuration": {
            "total_peak_power_kWp": config['total_peak_power'],
            "east_peak_power_kWp": config['east_peak'],
            "south_peak_power_kWp": config['south_peak'],
            "west_peak_power_kWp": config['west_peak'],
            "annual_yield_kWh": config['annual_yield'],
            "specific_yield_kWh_per_kWp": config['specific_yield'],
            "max_power_output_kW": config['max_power_kw']
        },
        "kWh_Totals_Available": True,
        "kWh_Columns": ["Wert (kWh)", "PV_east_kWh", "PV_south_kWh", "PV_west_kWh"]
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_config, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON config: {json_path}")
    
    # Create transformation documentation
    transformations = [
        "1. CSV-Datei geladen (sources/datafiles/Referenz/PV_series.csv)",
        "2. Datetime-Spalte aus 'Date [UTC+1]' erstellt",
        "3. Normalisierte PV-Werte mit Peakleistung skaliert (kW-basiert):",
        f"   - Ost: {config['east_peak']:.1f} kWp",
        f"   - Süd: {config['south_peak']:.1f} kWp", 
        f"   - West: {config['west_peak']:.1f} kWp",
        f"   - Gesamt: {config['total_peak_power']:.1f} kWp",
        "4. Leistungswerte (kW) für 15-Min-Intervalle berechnet",
        "5. kWh-Werte zusätzlich für Energieberechnungen erstellt",
        "6. Gesamtwert als unique kW-Spalte (primär) und 'Wert (kWh)' (sekundär) berechnet",
        "7. Metadaten-Spalten hinzugefügt",
        "8. Als Parquet-Datei exportiert"
    ]
    
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(f"# Transformationen für {config['name']}\n\n")
        md_file.write(f"**Erstellt am:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        md_file.write("## Verarbeitungsschritte:\n")
        for step in transformations:
            md_file.write(f"- {step}\n")
        md_file.write(f"\n## PV-Konfiguration:\n")
        md_file.write(f"- Gesamte Peakleistung: {config['total_peak_power']:.1f} kWp\n")
        md_file.write(f"- Ost-Ausrichtung: {config['east_peak']:.1f} kWp\n")
        md_file.write(f"- Süd-Ausrichtung: {config['south_peak']:.1f} kWp\n")
        md_file.write(f"- West-Ausrichtung: {config['west_peak']:.1f} kWp\n")
        md_file.write(f"- Verwendeter spezifischer Ertrag: {config['specific_annual_yield_used']} kWh/kWp/Jahr\n")
        md_file.write(f"\n## Datenqualität:\n")
        md_file.write(f"- Zeitraum: {df['datetime'].min()} bis {df['datetime'].max()}\n")
        md_file.write(f"- Anzahl Datenpunkte: {len(df):,}\n")
        md_file.write(f"- Intervall: 15 Minuten\n")
        md_file.write(f"- Jahresertrag: {config['annual_yield']:,.0f} kWh\n")
        md_file.write(f"- Spezifischer Ertrag: {config['specific_yield']:.0f} kWh/kWp\n")
        md_file.write(f"- Maximale Leistung: {config['max_power_kw']:.1f} kW ({config['max_power_kw']/config['total_peak_power']*100:.1f}% der Peakleistung)\n")
    
    print(f"Saved documentation: {md_path}")
    
    return parquet_path, json_path, md_path


def main():
    """Main function to orchestrate the PV reference data creation."""
    try:
        # Get user input
        config = get_user_input()
        
        # Process data
        df, kw_column_name = load_and_process_data(config)
        
        # Save files
        parquet_path, json_path, md_path = save_files(df, config, kw_column_name)
        
        print(f"\n{'='*50}")
        print("SUCCESS: PV reference data created!")
        print(f"{'='*50}")
        print(f"Configuration: {config['name']}")
        print(f"Total peak power: {config['total_peak_power']:,.1f} kWp")
        print(f"Annual yield: {config['annual_yield']:,.0f} kWh")
        print(f"Specific yield: {config['specific_yield']:.0f} kWh/kWp")
        print(f"Files created:")
        print(f"  - {parquet_path}")
        print(f"  - {json_path}")
        print(f"  - {md_path}")
        print("\nYou can now use this configuration in the analyze.py application.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())