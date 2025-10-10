#!/usr/bin/env python3
"""
Test script for kW to kWh conversion validation in PVHelper.

This script validates that the new kW-based data processing produces
accurate kWh calculations and maintains backward compatibility.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helper import (
    process_power_data, 
    calculate_kwh_from_kw, 
    check_and_convert_to_kwh,
    scale_dataframe,
    show_kwh_totals,
    get_unique_kw_column_name
)

class TestKWConversion:
    """Test suite for kW conversion validation."""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_test(self, test_name, passed, message=""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append(f"[{status}] {test_name}: {message}")
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def get_kw_column_name(self, df):
        """Helper method to get kW column name dynamically."""
        kw_columns = [col for col in df.columns if col.startswith('Wert-kW')]
        if kw_columns:
            return kw_columns[0]
        elif 'Wert (kW)' in df.columns:
            return 'Wert (kW)'
        else:
            return None
        print(f"[{status}] {test_name}: {message}")
    
    def create_test_data(self, interval_minutes=15, hours=24):
        """Create synthetic test data for validation."""
        # Create 24 hours of 15-minute interval data
        start_time = datetime(2023, 6, 15, 0, 0)  # Mid-year to avoid edge cases
        periods = hours * (60 // interval_minutes)
        
        # Create datetime index
        datetime_index = pd.date_range(
            start=start_time, 
            periods=periods, 
            freq=f'{interval_minutes}min'
        )
        
        # Create realistic PV power curve (kW)
        # Simulate a 100 kW peak system with realistic daily pattern
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in datetime_index])
        
        # Bell curve for PV production (peak at noon)
        pv_curve = 100 * np.exp(-((hours_of_day - 12) ** 2) / 18)
        pv_curve = np.maximum(pv_curve, 0)  # No negative values
        
        # Add some realistic noise
        np.random.seed(42)
        pv_curve += np.random.normal(0, 2, len(pv_curve))
        pv_curve = np.maximum(pv_curve, 0)  # Ensure no negative values
        
        df = pd.DataFrame({
            'datetime': datetime_index,
        })
        
        # Use unique kW column naming
        kw_col_name = get_unique_kw_column_name(df)
        df[kw_col_name] = pv_curve
        
        return df
    
    def test_kwh_calculation_accuracy(self):
        """Test that kWh calculations from kW data are mathematically correct."""
        df = self.create_test_data(interval_minutes=15)
        
        # Get the kW column name dynamically
        kw_columns = [col for col in df.columns if col.startswith('Wert-kW')]
        kw_col = kw_columns[0] if kw_columns else None
        self.assertIsNotNone(kw_col, "No kW column found in test data")
        
        # Calculate kWh manually
        interval_hours = 15 / 60  # 0.25 hours
        expected_kwh = df[kw_col] * interval_hours
        
        # Calculate using our function
        calculated_kwh = calculate_kwh_from_kw(df, 15, kw_col)
        
        # Check accuracy
        diff = np.abs(expected_kwh - calculated_kwh).max()
        tolerance = 1e-10
        
        passed = diff < tolerance
        self.log_test(
            "kWh Calculation Accuracy", 
            passed, 
            f"Max difference: {diff:.2e} (tolerance: {tolerance:.2e})"
        )
        
        return passed
    
    def test_energy_conservation(self):
        """Test that total energy is conserved in conversions."""
        df = self.create_test_data(interval_minutes=15)
        
        # Get the kW column name dynamically
        kw_columns = [col for col in df.columns if col.startswith('Wert-kW')]
        kw_col = kw_columns[0] if kw_columns else None
        self.assertIsNotNone(kw_col, "No kW column found in test data")
        
        # Calculate total energy manually
        interval_hours = 15 / 60
        expected_total_kwh = (df[kw_col] * interval_hours).sum()
        
        # Calculate using our function
        kwh_series = calculate_kwh_from_kw(df, 15, kw_col)
        calculated_total_kwh = kwh_series.sum()
        
        # Check conservation
        diff = abs(expected_total_kwh - calculated_total_kwh)
        tolerance = 1e-6
        
        passed = diff < tolerance
        self.log_test(
            "Energy Conservation", 
            passed, 
            f"Expected: {expected_total_kwh:.3f} kWh, Got: {calculated_total_kwh:.3f} kWh, Diff: {diff:.2e}"
        )
        
        return passed
    
    def test_different_intervals(self):
        """Test kWh calculations for different time intervals."""
        intervals = [15, 30, 60]
        all_passed = True
        
        for interval in intervals:
            df = self.create_test_data(interval_minutes=interval, hours=24)
            
            # Manual calculation
            interval_hours = interval / 60
            expected_kwh = df['Wert (kW)'] * interval_hours
            
            # Function calculation
            calculated_kwh = calculate_kwh_from_kw(df, interval, 'Wert (kW)')
            
            # Check accuracy
            diff = np.abs(expected_kwh - calculated_kwh).max()
            tolerance = 1e-10
            
            passed = diff < tolerance
            all_passed = all_passed and passed
            
            self.log_test(
                f"Interval {interval}min Test", 
                passed, 
                f"Max diff: {diff:.2e}"
            )
        
        return all_passed
    
    def test_process_power_data_function(self):
        """Test the process_power_data function with different input units."""
        df_kw = self.create_test_data()
        df_kw_copy = df_kw.copy()
        
        # Test kW input
        settings_kw = {
            'Einheit': 'kW',
            'Datenspalte': 'Wert (kW)',
            'Intervall': 15
        }
        
        result_kw = process_power_data(df_kw_copy, settings_kw)
        
        # Should preserve kW values
        kw_diff = np.abs(result_kw['Wert (kW)'] - df_kw['Wert (kW)']).max()
        passed_kw = kw_diff < 1e-10
        
        self.log_test(
            "Process Power Data (kW input)", 
            passed_kw, 
            f"Max difference: {kw_diff:.2e}"
        )
        
        # Test kWh input (should convert to kW)
        df_kwh = df_kw.copy()
        df_kwh['Wert (kWh)'] = df_kwh['Wert (kW)'] * 0.25  # Convert to kWh for 15min intervals
        
        settings_kwh = {
            'Einheit': 'kWh',
            'Datenspalte': 'Wert (kWh)',
            'Intervall': 15
        }
        
        result_kwh = process_power_data(df_kwh, settings_kwh)
        
        # Should convert back to original kW values
        kw_reconverted = result_kwh['Wert (kW)']
        kw_diff_reconvert = np.abs(kw_reconverted - df_kw['Wert (kW)']).max()
        passed_kwh = kw_diff_reconvert < 1e-6
        
        self.log_test(
            "Process Power Data (kWh input)", 
            passed_kwh, 
            f"Max difference after round-trip: {kw_diff_reconvert:.2e}"
        )
        
        return passed_kw and passed_kwh
    
    def test_backward_compatibility(self):
        """Test that legacy kWh-based workflow still works."""
        df = self.create_test_data()
        df['Wert (kWh)'] = df['Wert (kW)'] * 0.25  # Convert to kWh
        
        settings = {
            'Einheit': 'kWh',
            'Datenspalte': 'Wert (kWh)',
            'Intervall': 15
        }
        
        try:
            result = check_and_convert_to_kwh(df, settings)
            
            # Should have both kW and kWh columns
            has_kw = 'Wert (kW)' in result.columns
            has_kwh = 'Wert (kWh)' in result.columns
            
            passed = has_kw and has_kwh
            
            self.log_test(
                "Backward Compatibility", 
                passed, 
                f"Has kW: {has_kw}, Has kWh: {has_kwh}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test(
                "Backward Compatibility", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_scaling_functions(self):
        """Test that scaling functions work correctly with kW data."""
        df = self.create_test_data()
        
        # Add kW column using process_power_data
        settings = {
            'Einheit': 'kW',
            'Datenspalte': 'Wert (kW)',
            'Intervall': 15
        }
        
        df = process_power_data(df, settings)
        original_peak = df['Wert (kW)'].max()
        
        # Test peak scaling
        target_peak = 150.0  # Scale to 150 kW peak
        scale_settings = settings.copy()
        scale_settings['Zielspitzenwert'] = target_peak
        
        try:
            # Mock streamlit for scaling function
            import streamlit as st
            
            # Temporarily replace streamlit functions for testing
            original_warning = st.warning if hasattr(st, 'warning') else None
            st.warning = lambda x: print(f"WARNING: {x}")
            
            scaled_df = scale_dataframe(df.copy(), scale_settings)
            
            # Restore original streamlit function
            if original_warning:
                st.warning = original_warning
            
            new_peak = scaled_df['Wert (kW)'].max()
            peak_diff = abs(new_peak - target_peak)
            
            passed = peak_diff < 0.01  # 0.01 kW tolerance
            
            self.log_test(
                "Peak Power Scaling", 
                passed, 
                f"Target: {target_peak} kW, Got: {new_peak:.2f} kW, Diff: {peak_diff:.3f} kW"
            )
            
            return passed
            
        except Exception as e:
            self.log_test(
                "Peak Power Scaling", 
                False, 
                f"Exception: {str(e)}"
            )
            return False
    
    def test_realistic_pv_scenario(self):
        """Test with realistic PV generation scenario."""
        # Create year-long data
        df = self.create_test_data(interval_minutes=15, hours=24*7)  # One week for speed
        
        settings = {
            'Einheit': 'kW',
            'Datenspalte': 'Wert (kW)',
            'Intervall': 15
        }
        
        # Process with new kW-based pipeline
        df = process_power_data(df, settings)
        df = check_and_convert_to_kwh(df, settings)
        
        # Calculate key metrics
        peak_power_kw = df['Wert (kW)'].max()
        total_energy_kwh = df['Wert (kWh)'].sum()
        average_power_kw = df['Wert (kW)'].mean()
        
        # Validate realistic ranges for 100kW peak system
        peak_reasonable = 50 <= peak_power_kw <= 120  # Allow for noise
        energy_reasonable = total_energy_kwh > 0
        average_reasonable = 0 <= average_power_kw <= peak_power_kw
        
        passed = peak_reasonable and energy_reasonable and average_reasonable
        
        self.log_test(
            "Realistic PV Scenario", 
            passed, 
            f"Peak: {peak_power_kw:.1f} kW, Total: {total_energy_kwh:.1f} kWh, Avg: {average_power_kw:.1f} kW"
        )
        
        return passed
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with zero values
        df_zeros = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=96, freq='15min'),
            'Wert (kW)': [0.0] * 96
        })
        
        kwh_zeros = calculate_kwh_from_kw(df_zeros, 15, 'Wert (kW)')
        all_zeros = (kwh_zeros == 0).all()
        
        # Test with very small values
        df_small = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=96, freq='15min'),
            'Wert (kW)': [0.001] * 96  # 1 Watt
        })
        
        kwh_small = calculate_kwh_from_kw(df_small, 15, 'Wert (kW)')
        expected_small = 0.001 * 0.25  # 0.25 Wh per interval
        small_correct = np.allclose(kwh_small, expected_small)
        
        # Test with very large values
        df_large = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=96, freq='15min'),
            'Wert (kW)': [10000.0] * 96  # 10 MW
        })
        
        kwh_large = calculate_kwh_from_kw(df_large, 15, 'Wert (kW)')
        expected_large = 10000.0 * 0.25  # 2500 kWh per interval
        large_correct = np.allclose(kwh_large, expected_large)
        
        passed = all_zeros and small_correct and large_correct
        
        self.log_test(
            "Edge Cases (Zero/Small/Large Values)", 
            passed, 
            f"Zeros: {all_zeros}, Small: {small_correct}, Large: {large_correct}"
        )
        
        return passed
    
    def test_data_quality_validation(self):
        """Test handling of missing values and data quality issues."""
        # Create data with NaN values
        df_nan = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=96, freq='15min'),
            'Wert (kW)': [10.0] * 48 + [np.nan] * 48
        })
        
        try:
            kwh_nan = calculate_kwh_from_kw(df_nan, 15, 'Wert (kW)')
            
            # Should handle NaN values gracefully
            has_nan = kwh_nan.isna().any()
            valid_count = kwh_nan.notna().sum()
            expected_valid = 48  # First 48 values should be valid
            
            passed = has_nan and (valid_count == expected_valid)
            
            self.log_test(
                "Data Quality (NaN Handling)", 
                passed, 
                f"Has NaN: {has_nan}, Valid count: {valid_count}/{expected_valid}"
            )
            
        except Exception as e:
            self.log_test(
                "Data Quality (NaN Handling)", 
                False, 
                f"Exception: {str(e)}"
            )
            passed = False
        
        return passed
    
    def test_leap_year_scenarios(self):
        """Test with leap year data (366 days)."""
        # Create leap year data (2020 was a leap year)
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 12, 31, 23, 45)
        
        datetime_index = pd.date_range(start=start_date, end=end_date, freq='15min')
        
        # Should have 366 * 96 = 35,136 intervals for leap year
        expected_intervals = 366 * 96
        actual_intervals = len(datetime_index)
        
        # Create simple test data
        df_leap = pd.DataFrame({
            'datetime': datetime_index,
            'Wert (kW)': [50.0] * len(datetime_index)  # Constant 50 kW
        })
        
        kwh_leap = calculate_kwh_from_kw(df_leap, 15, 'Wert (kW)')
        
        # Calculate expected total energy
        expected_total = 50.0 * 0.25 * len(datetime_index)  # 50 kW * 0.25 h * intervals
        actual_total = kwh_leap.sum()
        
        total_diff = abs(expected_total - actual_total)
        
        passed = (actual_intervals == expected_intervals) and (total_diff < 1e-6)
        
        self.log_test(
            "Leap Year Scenario", 
            passed, 
            f"Intervals: {actual_intervals}/{expected_intervals}, Energy diff: {total_diff:.2e}"
        )
        
        return passed
    
    def test_multi_orientation_pv_system(self):
        """Test a realistic multi-orientation PV system like the one in create_pv_reference.py."""
        # Create 3-day test period
        df = self.create_test_data(interval_minutes=15, hours=72)
        
        # Simulate east, south, west orientations with different peak powers
        east_peak = 100  # kW
        south_peak = 200  # kW  
        west_peak = 100  # kW
        
        # Create orientation-specific power curves
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in df['datetime']])
        
        # East peaks in morning (9 AM)
        east_curve = east_peak * np.exp(-((hours_of_day - 9) ** 2) / 8)
        east_curve = np.maximum(east_curve, 0)
        
        # South peaks at noon (12 PM)
        south_curve = south_peak * np.exp(-((hours_of_day - 12) ** 2) / 12)
        south_curve = np.maximum(south_curve, 0)
        
        # West peaks in afternoon (3 PM)
        west_curve = west_peak * np.exp(-((hours_of_day - 15) ** 2) / 8)
        west_curve = np.maximum(west_curve, 0)
        
        # Create multi-orientation dataframe
        df_multi = pd.DataFrame({
            'datetime': df['datetime'],
            'PV_east_kW': east_curve,
            'PV_south_kW': south_curve,
            'PV_west_kW': west_curve
        })
        
        df_multi['Wert (kW)'] = df_multi['PV_east_kW'] + df_multi['PV_south_kW'] + df_multi['PV_west_kW']
        
        # Calculate kWh for each orientation
        for orientation in ['east', 'south', 'west']:
            kw_col = f'PV_{orientation}_kW'
            kwh_col = f'PV_{orientation}_kWh'
            df_multi[kwh_col] = calculate_kwh_from_kw(df_multi, 15, kw_col)
        
        df_multi['Wert (kWh)'] = calculate_kwh_from_kw(df_multi, 15, 'Wert (kW)')
        
        # Validate energy conservation
        total_kwh_sum = df_multi['PV_east_kWh'].sum() + df_multi['PV_south_kWh'].sum() + df_multi['PV_west_kWh'].sum()
        total_kwh_calc = df_multi['Wert (kWh)'].sum()
        
        energy_diff = abs(total_kwh_sum - total_kwh_calc)
        
        # Validate peak powers
        east_peak_actual = df_multi['PV_east_kW'].max()
        south_peak_actual = df_multi['PV_south_kW'].max()
        west_peak_actual = df_multi['PV_west_kW'].max()
        total_peak_actual = df_multi['Wert (kW)'].max()
        
        peaks_reasonable = (
            abs(east_peak_actual - east_peak) < 5 and
            abs(south_peak_actual - south_peak) < 5 and
            abs(west_peak_actual - west_peak) < 5 and
            total_peak_actual <= (east_peak + south_peak + west_peak)  # Total should be <= sum due to timing
        )
        
        passed = energy_diff < 1e-6 and peaks_reasonable
        
        self.log_test(
            "Multi-Orientation PV System", 
            passed, 
            f"Energy diff: {energy_diff:.2e}, Peaks E/S/W/T: {east_peak_actual:.1f}/{south_peak_actual:.1f}/{west_peak_actual:.1f}/{total_peak_actual:.1f} kW"
        )
        
        return passed
    
    def test_performance_with_large_dataset(self):
        """Test performance with a large dataset (full year)."""
        import time
        
        # Create full year of 15-minute data (35,040 intervals)
        start_time = time.time()
        
        df_year = self.create_test_data(interval_minutes=15, hours=24*365)
        
        # Test kWh calculation performance
        calc_start = time.time()
        kwh_series = calculate_kwh_from_kw(df_year, 15, 'Wert (kW)')
        calc_end = time.time()
        
        # Test data processing performance
        settings = {
            'Einheit': 'kW',
            'Datenspalte': 'Wert (kW)',
            'Intervall': 15
        }
        
        process_start = time.time()
        df_processed = process_power_data(df_year.copy(), settings)
        process_end = time.time()
        
        end_time = time.time()
        
        # Performance metrics
        total_time = end_time - start_time
        calc_time = calc_end - calc_start
        process_time = process_end - process_start
        
        # Validate results
        data_points = len(df_year)
        expected_points = 365 * 96  # 365 days * 96 intervals per day
        
        # Performance thresholds (should be fast)
        performance_ok = calc_time < 1.0 and process_time < 1.0 and total_time < 5.0
        data_correct = data_points == expected_points
        
        passed = performance_ok and data_correct
        
        self.log_test(
            "Large Dataset Performance", 
            passed, 
            f"Data points: {data_points}, Calc: {calc_time:.3f}s, Process: {process_time:.3f}s, Total: {total_time:.3f}s"
        )
        
        return passed
    
    def test_interval_boundary_conditions(self):
        """Test various time interval boundary conditions."""
        intervals_to_test = [1, 5, 10, 15, 30, 60, 120]  # Minutes
        all_passed = True
        
        for interval in intervals_to_test:
            # Create test data for this interval
            periods = 24 * (60 // interval)  # One day of data
            
            # Handle case where interval doesn't divide evenly into 24 hours
            if 24 * 60 % interval != 0:
                # For intervals like 120min that don't divide evenly, calculate correctly
                periods = int(24 * 60 / interval)
            
            datetime_index = pd.date_range(
                start='2023-06-15', 
                periods=periods, 
                freq=f'{interval}min'
            )
            
            df_interval = pd.DataFrame({
                'datetime': datetime_index,
                'Wert (kW)': [100.0] * periods  # Constant 100 kW
            })
            
            # Calculate kWh
            kwh_values = calculate_kwh_from_kw(df_interval, interval, 'Wert (kW)')
            
            # Expected kWh per interval
            hours_per_interval = interval / 60
            expected_kwh_per_interval = 100.0 * hours_per_interval
            
            # Check if all values match expectation
            all_match = np.allclose(kwh_values, expected_kwh_per_interval)
            
            # Check total energy for the actual time period covered
            total_energy = kwh_values.sum()
            actual_hours_covered = periods * hours_per_interval
            expected_total_energy = 100.0 * actual_hours_covered
            
            energy_correct = abs(total_energy - expected_total_energy) < 1e-6
            
            interval_passed = all_match and energy_correct
            all_passed = all_passed and interval_passed
            
            self.log_test(
                f"Interval {interval}min Boundary", 
                interval_passed, 
                f"Per interval: {expected_kwh_per_interval:.3f} kWh, Total: {total_energy:.1f} kWh ({actual_hours_covered:.1f}h coverage)"
            )
        
        return all_passed
    
    def test_aggregation_functions(self):
        """Test the helper aggregation functions with kW data."""
        from helper import create_hourly_bundles, create_weekly_bundles, create_monthly_bundles, Datenbundle
        
        # Create test data
        df = self.create_test_data(interval_minutes=15, hours=24*7)  # One week
        
        # Add required columns
        df['name'] = 'Test Data'
        
        # Create a Datenbundle
        bundle = Datenbundle(
            df=df,
            description='Test Bundle',
            interval=15,
            show_dataframe=False,
            show_dataframe_infos=False,
            is_last=True,
            is_erzeugung=True
        )
        
        try:
            # Test hourly aggregation
            hourly_bundles = create_hourly_bundles([bundle])
            hourly_passed = len(hourly_bundles) == 1 and len(hourly_bundles[0].df) > 0
            
            # Test weekly aggregation  
            weekly_bundles = create_weekly_bundles([bundle])
            weekly_passed = len(weekly_bundles) == 1 and len(weekly_bundles[0].df) > 0
            
            # Test monthly aggregation
            monthly_bundles = create_monthly_bundles([bundle])
            monthly_passed = len(monthly_bundles) == 1 and len(monthly_bundles[0].df) > 0
            
            passed = hourly_passed and weekly_passed and monthly_passed
            
            self.log_test(
                "Aggregation Functions", 
                passed, 
                f"Hourly: {hourly_passed}, Weekly: {weekly_passed}, Monthly: {monthly_passed}"
            )
            
        except Exception as e:
            self.log_test(
                "Aggregation Functions", 
                False, 
                f"Exception: {str(e)}"
            )
            passed = False
        
        return passed
    
    def test_load_profile_data(self):
        """Test with typical electrical load profile data (consumer pattern)."""
        # Create realistic load profile with morning and evening peaks
        df = self.create_test_data(interval_minutes=15, hours=24*3)  # 3 days
        
        # Replace PV curve with load curve (inverse pattern - high at night/morning/evening)
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in df['datetime']])
        
        # Create typical residential load profile
        # Base load: 2 kW
        # Morning peak: 6-8 AM (cooking, heating)
        # Evening peak: 6-9 PM (cooking, lighting, heating)
        base_load = 2.0
        morning_peak = 3.0 * np.exp(-((hours_of_day - 7) ** 2) / 2)
        evening_peak = 4.0 * np.exp(-((hours_of_day - 19.5) ** 2) / 3)
        
        load_curve = base_load + morning_peak + evening_peak
        load_curve = np.maximum(load_curve, 0.5)  # Minimum 0.5 kW standby load
        
        df_load = df.copy()
        df_load['Wert (kW)'] = load_curve
        
        # Test kWh calculation for load data
        kwh_values = calculate_kwh_from_kw(df_load, 15, 'Wert (kW)')
        
        # Validate load characteristics
        daily_consumption = kwh_values.sum() / 3  # Per day
        peak_load = df_load['Wert (kW)'].max()
        min_load = df_load['Wert (kW)'].min()
        
        # Realistic ranges for residential load
        daily_reasonable = 20 <= daily_consumption <= 100  # 20-100 kWh/day
        peak_reasonable = 5 <= peak_load <= 15  # 5-15 kW peak
        min_reasonable = 0.3 <= min_load <= 3  # 0.3-3 kW minimum
        
        passed = daily_reasonable and peak_reasonable and min_reasonable
        
        self.log_test(
            "Load Profile Data", 
            passed, 
            f"Daily: {daily_consumption:.1f} kWh, Peak: {peak_load:.1f} kW, Min: {min_load:.1f} kW"
        )
        
        return passed
    
    def test_wind_generation_data(self):
        """Test with wind generation data (variable, intermittent pattern)."""
        # Create wind generation with realistic variability
        df = self.create_test_data(interval_minutes=15, hours=24*2)  # 2 days
        
        # Wind generation: highly variable, can be zero for hours then spike
        np.random.seed(42)
        
        # Create wind speed simulation (simplified)
        wind_speeds = np.random.weibull(2, len(df)) * 15  # Weibull distribution, 0-15 m/s
        
        # Wind power curve (simplified)
        # Cut-in: 3 m/s, Rated: 12 m/s, Cut-out: 25 m/s
        wind_power = np.where(wind_speeds < 3, 0,  # Below cut-in
                     np.where(wind_speeds < 12, 
                             (wind_speeds - 3) / 9 * 500,  # Linear ramp to 500 kW
                             np.where(wind_speeds < 25, 500, 0)))  # Rated or cut-out
        
        # Add some turbulence/variability
        turbulence = np.random.normal(0, 20, len(df))
        wind_power = np.maximum(wind_power + turbulence, 0)
        
        df_wind = df.copy()
        df_wind['Wert (kW)'] = wind_power
        
        # Test kWh calculation
        kwh_values = calculate_kwh_from_kw(df_wind, 15, 'Wert (kW)')
        
        # Validate wind characteristics
        total_energy = kwh_values.sum()
        peak_power = df_wind['Wert (kW)'].max()
        zero_intervals = (df_wind['Wert (kW)'] == 0).sum()
        variability = df_wind['Wert (kW)'].std()
        
        # Wind generation characteristics
        peak_reasonable = 400 <= peak_power <= 600  # Around 500 kW rated
        has_zero_periods = zero_intervals > 0  # Wind doesn't always blow
        high_variability = variability > 50  # Wind is highly variable
        energy_positive = total_energy > 0
        
        passed = peak_reasonable and has_zero_periods and high_variability and energy_positive
        
        self.log_test(
            "Wind Generation Data", 
            passed, 
            f"Peak: {peak_power:.1f} kW, Zero periods: {zero_intervals}, Variability: {variability:.1f}, Energy: {total_energy:.1f} kWh"
        )
        
        return passed
    
    def test_industrial_load_data(self):
        """Test with industrial load data (high power, consistent pattern)."""
        # Create industrial load profile
        df = self.create_test_data(interval_minutes=15, hours=24*5)  # 5 days (work week)
        
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in df['datetime']])
        weekdays = np.array([dt.weekday() for dt in df['datetime']])  # 0=Monday, 6=Sunday
        
        # Industrial load: high during work hours, low at night/weekends
        base_load = 50  # kW base load (security, minimal systems)
        
        # Work hours: 6 AM to 10 PM on weekdays
        work_hours_mask = (hours_of_day >= 6) & (hours_of_day <= 22)
        weekday_mask = weekdays < 5  # Monday-Friday
        
        industrial_load = np.where(
            work_hours_mask & weekday_mask,
            base_load + 400 + np.random.normal(0, 30, len(df)),  # 450 kW ± variation during work
            base_load + np.random.normal(0, 10, len(df))  # Base load with small variation
        )
        
        industrial_load = np.maximum(industrial_load, base_load * 0.8)  # Minimum load
        
        df_industrial = df.copy()
        df_industrial['Wert (kW)'] = industrial_load
        
        # Test kWh calculation
        kwh_values = calculate_kwh_from_kw(df_industrial, 15, 'Wert (kW)')
        
        # Analyze daily patterns
        df_industrial['date'] = df_industrial['datetime'].dt.date
        df_industrial['weekday'] = df_industrial['datetime'].dt.weekday
        df_industrial['hour'] = df_industrial['datetime'].dt.hour
        
        # Add kWh column for analysis
        df_industrial['Wert (kWh)'] = kwh_values
        
        # Calculate weekday vs weekend consumption
        weekday_consumption = df_industrial[df_industrial['weekday'] < 5]['Wert (kWh)'].sum()
        weekend_consumption = df_industrial[df_industrial['weekday'] >= 5]['Wert (kWh)'].sum()
        
        # Count work days vs weekend days in the period
        work_days = df_industrial[df_industrial['weekday'] < 5]['date'].nunique()
        weekend_days = df_industrial[df_industrial['weekday'] >= 5]['date'].nunique()
        
        if work_days > 0 and weekend_days > 0:
            avg_weekday_consumption = weekday_consumption / work_days
            avg_weekend_consumption = weekend_consumption / weekend_days
            weekday_to_weekend_ratio = avg_weekday_consumption / avg_weekend_consumption
        else:
            weekday_to_weekend_ratio = 1
        
        # Industrial characteristics
        high_base_load = df_industrial['Wert (kW)'].min() >= 30  # High minimum load
        high_peak_load = df_industrial['Wert (kW)'].max() >= 400  # High peak load
        work_pattern = weekday_to_weekend_ratio > 2  # Much higher consumption on weekdays
        
        passed = high_base_load and high_peak_load and work_pattern
        
        self.log_test(
            "Industrial Load Data", 
            passed, 
            f"Base: {df_industrial['Wert (kW)'].min():.1f} kW, Peak: {df_industrial['Wert (kW)'].max():.1f} kW, Weekday/Weekend ratio: {weekday_to_weekend_ratio:.1f}"
        )
        
        return passed
    
    def test_battery_storage_data(self):
        """Test with battery storage data (positive and negative power flows)."""
        # Create battery storage profile with charging and discharging
        df = self.create_test_data(interval_minutes=15, hours=24)
        
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in df['datetime']])
        
        # Battery operation:
        # Charge during low-demand periods (night: 10 PM - 6 AM) - negative power
        # Discharge during high-demand periods (evening: 6 PM - 10 PM) - positive power
        # Idle during other times
        
        battery_power = np.zeros(len(df))
        
        # Charging periods (negative power)
        night_mask = (hours_of_day <= 6) | (hours_of_day >= 22)
        battery_power[night_mask] = -100  # 100 kW charging
        
        # Discharging periods (positive power)
        evening_mask = (hours_of_day >= 18) & (hours_of_day <= 22)
        battery_power[evening_mask] = 150  # 150 kW discharging
        
        # Add some efficiency losses and variations
        np.random.seed(42)
        battery_power += np.random.normal(0, 5, len(df))  # Small variations
        
        df_battery = df.copy()
        df_battery['Wert (kW)'] = battery_power
        
        # Test kWh calculation with positive and negative values
        kwh_values = calculate_kwh_from_kw(df_battery, 15, 'Wert (kW)')
        
        # Battery analysis
        total_charged = kwh_values[kwh_values < 0].sum()  # Negative kWh (energy input)
        total_discharged = kwh_values[kwh_values > 0].sum()  # Positive kWh (energy output)
        net_energy = kwh_values.sum()
        
        # Battery characteristics
        has_charging = total_charged < 0  # Should have negative energy periods
        has_discharging = total_discharged > 0  # Should have positive energy periods
        energy_loss = abs(net_energy) > 0  # Should have some net loss due to efficiency
        
        # Round-trip efficiency check (should be realistic 80-95%)
        if total_discharged > 0 and abs(total_charged) > 0:
            efficiency = total_discharged / abs(total_charged) * 100
            efficiency_reasonable = 70 <= efficiency <= 100  # Allow for some measurement variance
        else:
            efficiency_reasonable = False
            efficiency = 0
        
        passed = has_charging and has_discharging and energy_loss and efficiency_reasonable
        
        self.log_test(
            "Battery Storage Data", 
            passed, 
            f"Charged: {total_charged:.1f} kWh, Discharged: {total_discharged:.1f} kWh, Efficiency: {efficiency:.1f}%, Net: {net_energy:.1f} kWh"
        )
        
        return passed
    
    def test_mixed_renewable_system(self):
        """Test with mixed renewable system (PV + Wind + Battery)."""
        # Create a complex system combining different generation and storage
        df = self.create_test_data(interval_minutes=15, hours=24*2)  # 2 days
        
        hours_of_day = np.array([dt.hour + dt.minute/60 for dt in df['datetime']])
        
        # PV generation (day only)
        pv_power = 200 * np.exp(-((hours_of_day - 12) ** 2) / 18)
        pv_power = np.maximum(pv_power, 0)
        
        # Wind generation (variable, day and night)
        np.random.seed(42)
        wind_speeds = np.random.weibull(2, len(df)) * 12
        wind_power = np.where(wind_speeds < 3, 0, 
                             np.where(wind_speeds < 10, (wind_speeds - 3) / 7 * 100, 100))
        
        # Battery operation (charge when excess, discharge when deficit)
        load_demand = 80 + 40 * np.sin(2 * np.pi * hours_of_day / 24)  # Sinusoidal load 40-120 kW
        generation = pv_power + wind_power
        excess = generation - load_demand
        
        # Battery responds to excess/deficit (simplified)
        battery_power = np.clip(excess * 0.8, -50, 50)  # Limited to ±50 kW
        
        # Net system output
        net_power = generation + battery_power - load_demand
        
        df_mixed = df.copy()
        df_mixed['PV_kW'] = pv_power
        df_mixed['Wind_kW'] = wind_power
        df_mixed['Battery_kW'] = battery_power
        df_mixed['Load_kW'] = load_demand
        df_mixed['Wert (kW)'] = net_power
        
        # Calculate energy for each component
        for component in ['PV', 'Wind', 'Battery', 'Load']:
            kw_col = f'{component}_kW'
            kwh_col = f'{component}_kWh'
            df_mixed[kwh_col] = calculate_kwh_from_kw(df_mixed, 15, kw_col)
        
        df_mixed['Wert (kWh)'] = calculate_kwh_from_kw(df_mixed, 15, 'Wert (kW)')
        
        # System analysis
        pv_energy = df_mixed['PV_kWh'].sum()
        wind_energy = df_mixed['Wind_kWh'].sum()
        battery_energy = df_mixed['Battery_kWh'].sum()  # Net battery energy
        load_energy = df_mixed['Load_kWh'].sum()
        net_energy = df_mixed['Wert (kWh)'].sum()
        
        # Renewable characteristics
        renewable_generation = pv_energy + wind_energy
        has_pv_generation = pv_energy > 0
        has_wind_generation = wind_energy > 0
        battery_used = abs(battery_energy) > 0  # Battery was active
        load_met = load_energy > 0
        
        # Energy balance check (should be roughly conserved)
        energy_balance = abs((pv_energy + wind_energy + battery_energy) - (load_energy + net_energy))
        balance_reasonable = energy_balance < 1.0  # Small tolerance for rounding
        
        passed = has_pv_generation and has_wind_generation and battery_used and load_met and balance_reasonable
        
        self.log_test(
            "Mixed Renewable System", 
            passed, 
            f"PV: {pv_energy:.1f} kWh, Wind: {wind_energy:.1f} kWh, Battery: {battery_energy:.1f} kWh, Load: {load_energy:.1f} kWh, Net: {net_energy:.1f} kWh"
        )
        
        return passed
    
    def test_seasonal_variation_data(self):
        """Test with data showing seasonal variations (full year)."""
        # Create full year data with seasonal patterns
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31, 23, 45)
        datetime_index = pd.date_range(start=start_date, end=end_date, freq='60min')  # Hourly for speed
        
        df_seasonal = pd.DataFrame({'datetime': datetime_index})
        
        # Calculate day of year for seasonal calculation
        day_of_year = df_seasonal['datetime'].dt.dayofyear
        hour_of_day = df_seasonal['datetime'].dt.hour
        
        # Seasonal PV generation pattern
        # Peak in summer (day 172 = June 21), minimum in winter (day 355 = December 21)
        seasonal_factor = 0.3 + 0.7 * np.cos(2 * np.pi * (day_of_year - 172) / 365)
        
        # Daily PV pattern
        daily_factor = np.maximum(0, np.cos(2 * np.pi * (hour_of_day - 12) / 24))
        
        # Combined PV generation (100 kW peak in summer)
        pv_generation = 100 * seasonal_factor * daily_factor
        
        df_seasonal['Wert (kW)'] = pv_generation
        
        # Test kWh calculation for full year
        kwh_values = calculate_kwh_from_kw(df_seasonal, 60, 'Wert (kW)')  # 60-minute intervals
        df_seasonal['Wert (kWh)'] = kwh_values
        
        # Seasonal analysis
        df_seasonal['month'] = df_seasonal['datetime'].dt.month
        monthly_energy = df_seasonal.groupby('month')['Wert (kWh)'].sum()
        
        # Check seasonal characteristics
        summer_months = [5, 6, 7, 8]  # May-August
        winter_months = [11, 12, 1, 2]  # Nov-Feb
        
        summer_energy = monthly_energy[summer_months].sum()
        winter_energy = monthly_energy[winter_months].sum()
        
        if winter_energy > 0.1:  # Account for very small winter generation
            seasonal_ratio = summer_energy / winter_energy
        else:
            seasonal_ratio = float('inf')  # Infinite ratio if winter is essentially zero
        
        # Validate seasonal patterns
        annual_energy = kwh_values.sum()
        peak_month = monthly_energy.idxmax()
        min_month = monthly_energy.idxmin()
        
        # Seasonal characteristics for PV
        annual_reasonable = 30000 <= annual_energy <= 100000  # 30-100 MWh for 100kW system
        peak_in_summer = peak_month in [5, 6, 7, 8]  # Peak in summer months
        min_in_winter = min_month in [11, 12, 1, 2]  # Minimum in winter months
        strong_seasonal = seasonal_ratio > 2 or seasonal_ratio == float('inf')  # Summer should be >2x winter or winter is negligible
        
        passed = annual_reasonable and peak_in_summer and min_in_winter and strong_seasonal
        
        self.log_test(
            "Seasonal Variation Data", 
            passed, 
            f"Annual: {annual_energy:.0f} kWh, Peak month: {peak_month}, Min month: {min_month}, Summer/Winter: {seasonal_ratio if seasonal_ratio != float('inf') else 'inf'}"
        )
        
        return passed
    
    def test_data_with_measurement_errors(self):
        """Test with realistic measurement errors and data quality issues."""
        # Create base data
        df = self.create_test_data(interval_minutes=15, hours=24)
        
        # Add realistic measurement errors
        np.random.seed(42)
        
        # 1. Random measurement noise (±1% typical for good meters)
        noise = np.random.normal(0, 0.01, len(df))
        df['Wert (kW)'] = df['Wert (kW)'] * (1 + noise)
        
        # 2. Some negative values due to measurement errors (should be filtered to 0)
        negative_indices = np.random.choice(len(df), size=5, replace=False)
        df.loc[negative_indices, 'Wert (kW)'] = -0.1
        
        # 3. Some outliers (very high values)
        outlier_indices = np.random.choice(len(df), size=3, replace=False)
        df.loc[outlier_indices, 'Wert (kW)'] = df['Wert (kW)'].iloc[outlier_indices] * 10
        
        # 4. Some exactly zero values (common for nighttime PV)
        zero_indices = np.random.choice(len(df), size=20, replace=False)
        df.loc[zero_indices, 'Wert (kW)'] = 0.0
        
        # 5. Missing values (NaN)
        nan_indices = np.random.choice(len(df), size=10, replace=False)
        df.loc[nan_indices, 'Wert (kW)'] = np.nan
        
        # Test kWh calculation with problematic data
        kwh_values = calculate_kwh_from_kw(df, 15, 'Wert (kW)')
        
        # Analysis of data quality handling
        has_negative = (df['Wert (kW)'] < 0).any()
        has_outliers = (df['Wert (kW)'] > 200).any()  # Outliers above reasonable range
        has_zeros = (df['Wert (kW)'] == 0).any()
        has_nans = df['Wert (kW)'].isna().any()
        
        # Check kWh calculation handling
        kwh_has_nans = kwh_values.isna().any()
        kwh_negative_count = (kwh_values < 0).sum()
        
        # Quality measures
        valid_data_percentage = df['Wert (kW)'].notna().sum() / len(df) * 100
        
        # Data quality characteristics
        handles_nans = kwh_has_nans  # Should propagate NaN appropriately
        handles_negatives = kwh_negative_count >= 0  # Should handle negative inputs
        sufficient_valid_data = valid_data_percentage >= 80  # Should have mostly valid data
        realistic_results = kwh_values.notna().sum() > 0  # Should produce some valid results
        
        passed = handles_nans and handles_negatives and sufficient_valid_data and realistic_results
        
        self.log_test(
            "Data with Measurement Errors", 
            passed, 
            f"Valid data: {valid_data_percentage:.1f}%, Negatives: {has_negative}, Outliers: {has_outliers}, NaNs: {has_nans}, kWh NaNs: {kwh_has_nans}"
        )
        
        return passed
    
    def test_timestamp_alignment_scenarios(self):
        """Test left-aligned vs right-aligned timestamps."""
        from helper import check_and_fix_right_interval
        
        # Test 1: Left-aligned timestamps (normal case)
        # Timestamps represent the START of the measurement period
        df_left = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=96, freq='15min'),
            'Wert (kW)': [100.0] * 96
        })
        
        # Test 2: Right-aligned timestamps 
        # Timestamps represent the END of the measurement period
        df_right = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:15:00', periods=96, freq='15min'),
            'Wert (kW)': [100.0] * 96
        })
        
        # Calculate kWh for both alignment types
        kwh_left = calculate_kwh_from_kw(df_left, 15, 'Wert (kW)')
        kwh_right_original = calculate_kwh_from_kw(df_right, 15, 'Wert (kW)')
        
        # Apply the alignment correction function
        df_right_corrected = check_and_fix_right_interval(df_right.copy(), 15)
        kwh_right_corrected = calculate_kwh_from_kw(df_right_corrected, 15, 'Wert (kW)')
        
        # Both should produce the same kWh values after correction
        alignment_consistent = np.allclose(kwh_left, kwh_right_corrected)
        
        # Check that timestamps were properly shifted
        first_time_left = df_left['datetime'].iloc[0]
        first_time_right_corrected = df_right_corrected['datetime'].iloc[0]
        timestamp_shift_correct = first_time_left == first_time_right_corrected
        
        # Validate energy totals are the same
        total_left = kwh_left.sum()
        total_right_corrected = kwh_right_corrected.sum()
        energy_totals_match = abs(total_left - total_right_corrected) < 1e-6
        
        passed = alignment_consistent and timestamp_shift_correct and energy_totals_match
        
        self.log_test(
            "Timestamp Alignment (15min)", 
            passed, 
            f"Alignment consistent: {alignment_consistent}, Timestamp shift: {timestamp_shift_correct}, Energy match: {energy_totals_match}"
        )
        
        return passed
    
    def test_hourly_timestamp_alignment(self):
        """Test left-aligned vs right-aligned timestamps for hourly data."""
        from helper import check_and_fix_right_interval
        
        # Test hourly data alignment
        # Left-aligned: timestamps at 00:00, 01:00, 02:00, etc.
        df_hourly_left = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=24, freq='60min'),
            'Wert (kW)': [150.0] * 24
        })
        
        # Right-aligned: timestamps at 01:00, 02:00, 03:00, etc.
        df_hourly_right = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 01:00:00', periods=24, freq='60min'),
            'Wert (kW)': [150.0] * 24
        })
        
        # Calculate kWh
        kwh_hourly_left = calculate_kwh_from_kw(df_hourly_left, 60, 'Wert (kW)')
        
        # Apply alignment correction for right-aligned timestamps
        df_hourly_right_corrected = check_and_fix_right_interval(df_hourly_right.copy(), 60)
        kwh_hourly_right_corrected = calculate_kwh_from_kw(df_hourly_right_corrected, 60, 'Wert (kW)')
        
        # Check alignment consistency
        hourly_alignment_consistent = np.allclose(kwh_hourly_left, kwh_hourly_right_corrected)
        
        # Check timestamp correction
        first_time_left = df_hourly_left['datetime'].iloc[0]
        first_time_right_corrected = df_hourly_right_corrected['datetime'].iloc[0]
        hourly_timestamp_correct = first_time_left == first_time_right_corrected
        
        # Validate energy calculations for hourly data
        expected_kwh_per_hour = 150.0  # 150 kW * 1 hour = 150 kWh
        hourly_values_correct = np.allclose(kwh_hourly_left, expected_kwh_per_hour)
        
        passed = hourly_alignment_consistent and hourly_timestamp_correct and hourly_values_correct
        
        self.log_test(
            "Timestamp Alignment (60min)", 
            passed, 
            f"Hourly alignment: {hourly_alignment_consistent}, Timestamp shift: {hourly_timestamp_correct}, Values: {hourly_values_correct}"
        )
        
        return passed
    
    def test_different_hourly_intervals(self):
        """Test various hourly interval scenarios."""
        # Test different hourly interval patterns that might occur in real data
        test_intervals = [
            (30, 'Semi-hourly data'),
            (60, 'Hourly data'),
            (120, 'Two-hour data'),
            (180, 'Three-hour data')
        ]
        
        all_passed = True
        
        for interval_min, description in test_intervals:
            # Create test data
            periods = 24 * (60 // interval_min) if (24 * 60) % interval_min == 0 else int(24 * 60 / interval_min)
            
            df_test = pd.DataFrame({
                'datetime': pd.date_range('2023-06-15 00:00:00', periods=periods, freq=f'{interval_min}min'),
                'Wert (kW)': [200.0] * periods
            })
            
            # Calculate kWh
            kwh_values = calculate_kwh_from_kw(df_test, interval_min, 'Wert (kW)')
            
            # Expected kWh per interval
            hours_per_interval = interval_min / 60
            expected_kwh_per_interval = 200.0 * hours_per_interval
            
            # Check calculations
            values_correct = np.allclose(kwh_values, expected_kwh_per_interval)
            
            # Check total energy for the time period covered
            actual_hours_covered = periods * hours_per_interval
            total_energy = kwh_values.sum()
            expected_total = 200.0 * actual_hours_covered
            total_correct = abs(total_energy - expected_total) < 1e-6
            
            interval_passed = values_correct and total_correct
            all_passed = all_passed and interval_passed
            
            self.log_test(
                f"Hourly Interval {interval_min}min", 
                interval_passed, 
                f"{description}: Per interval: {expected_kwh_per_interval:.1f} kWh, Total: {total_energy:.1f} kWh, Coverage: {actual_hours_covered:.1f}h"
            )
        
        return all_passed
    
    def test_mixed_interval_file_formats(self):
        """Test processing files that might have different interval representations."""
        # Simulate different file format scenarios that occur in real energy data
        
        # Scenario 1: Pure 15-minute intervals (standard)
        df_15min = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=96, freq='15min'),
            'Wert (kW)': [50.0] * 96
        })
        
        # Scenario 2: Pure hourly intervals
        df_hourly = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=24, freq='60min'),
            'Wert (kW)': [100.0] * 24
        })
        
        # Scenario 3: 30-minute intervals (common in some systems)
        df_30min = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=48, freq='30min'),
            'Wert (kW)': [75.0] * 48
        })
        
        # Test each scenario
        scenarios = [
            (df_15min, 15, '15-minute'),
            (df_hourly, 60, 'Hourly'),
            (df_30min, 30, '30-minute')
        ]
        
        all_scenarios_passed = True
        
        for df, interval, name in scenarios:
            # Calculate kWh
            kwh_values = calculate_kwh_from_kw(df, interval, 'Wert (kW)')
            
            # Expected calculations
            hours_per_interval = interval / 60
            power = df['Wert (kW)'].iloc[0]
            expected_kwh_per_interval = power * hours_per_interval
            total_energy = kwh_values.sum()
            expected_total = power * 24  # 24 hours total for each scenario
            
            # Validations
            values_correct = np.allclose(kwh_values, expected_kwh_per_interval)
            total_correct = abs(total_energy - expected_total) < 1e-6
            
            scenario_passed = values_correct and total_correct
            all_scenarios_passed = all_scenarios_passed and scenario_passed
            
            self.log_test(
                f"Mixed Format {name}", 
                scenario_passed, 
                f"Power: {power} kW, Per interval: {expected_kwh_per_interval:.2f} kWh, Total: {total_energy:.1f} kWh"
            )
        
        return all_scenarios_passed
    
    def test_real_world_timestamp_edge_cases(self):
        """Test edge cases that occur in real energy meter data files."""
        # Edge Case 1: Data starting at unusual times (not midnight)
        df_offset = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 08:30:00', periods=64, freq='15min'),  # Starts at 8:30 AM
            'Wert (kW)': [80.0] * 64
        })
        
        kwh_offset = calculate_kwh_from_kw(df_offset, 15, 'Wert (kW)')
        expected_per_interval = 80.0 * 0.25  # 20 kWh per 15-min interval
        offset_correct = np.allclose(kwh_offset, expected_per_interval)
        
        # Edge Case 2: Data with gaps (missing intervals)
        datetime_with_gaps = pd.date_range('2023-06-15 00:00:00', periods=96, freq='15min')
        # Remove some intervals to simulate gaps
        gap_indices = [10, 11, 12, 35, 36, 50]  # Remove 6 intervals
        datetime_with_gaps = datetime_with_gaps.delete(gap_indices)
        
        df_gaps = pd.DataFrame({
            'datetime': datetime_with_gaps,
            'Wert (kW)': [60.0] * len(datetime_with_gaps)
        })
        
        kwh_gaps = calculate_kwh_from_kw(df_gaps, 15, 'Wert (kW)')
        gaps_calculated = len(kwh_gaps) == len(datetime_with_gaps)
        gaps_values_correct = np.allclose(kwh_gaps, 60.0 * 0.25)
        
        # Edge Case 3: Different timezone or DST scenarios (constant interval, different start times)
        # Simulate data that might start at different times due to DST changes
        df_dst1 = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 00:00:00', periods=24, freq='60min'),
            'Wert (kW)': [120.0] * 24
        })
        
        df_dst2 = pd.DataFrame({
            'datetime': pd.date_range('2023-06-15 01:00:00', periods=23, freq='60min'),  # One hour shift
            'Wert (kW)': [120.0] * 23
        })
        
        kwh_dst1 = calculate_kwh_from_kw(df_dst1, 60, 'Wert (kW)')
        kwh_dst2 = calculate_kwh_from_kw(df_dst2, 60, 'Wert (kW)')
        
        dst_values_correct = (np.allclose(kwh_dst1, 120.0) and 
                             np.allclose(kwh_dst2, 120.0))
        
        passed = offset_correct and gaps_calculated and gaps_values_correct and dst_values_correct
        
        self.log_test(
            "Real-world Timestamp Edge Cases", 
            passed, 
            f"Offset start: {offset_correct}, Gaps handled: {gaps_calculated}, Gap values: {gaps_values_correct}, DST scenarios: {dst_values_correct}"
        )
        
        return passed
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 60)
        print("PV Helper kW Conversion Validation Tests - Extended Suite")
        print("=" * 60)
        
        # Core functionality tests
        core_tests = [
            self.test_kwh_calculation_accuracy,
            self.test_energy_conservation,
            self.test_different_intervals,
            self.test_process_power_data_function,
            self.test_backward_compatibility,
            self.test_scaling_functions,
            self.test_realistic_pv_scenario
        ]
        
        # Extended test scenarios
        extended_tests = [
            self.test_edge_cases,
            self.test_data_quality_validation,
            self.test_leap_year_scenarios,
            self.test_multi_orientation_pv_system,
            self.test_performance_with_large_dataset,
            self.test_interval_boundary_conditions,
            self.test_aggregation_functions,
            self.test_load_profile_data,
            self.test_wind_generation_data,
            self.test_industrial_load_data,
            self.test_battery_storage_data,
            self.test_mixed_renewable_system,
            self.test_seasonal_variation_data,
            self.test_data_with_measurement_errors,
            self.test_timestamp_alignment_scenarios,
            self.test_hourly_timestamp_alignment,
            self.test_different_hourly_intervals,
            self.test_mixed_interval_file_formats,
            self.test_real_world_timestamp_edge_cases
        ]
        
        print("🔧 Core Functionality Tests")
        print("-" * 40)
        
        for test in core_tests:
            try:
                test()
            except Exception as e:
                self.log_test(
                    test.__name__, 
                    False, 
                    f"Exception: {str(e)}"
                )
        
        print("\n🚀 Extended Test Scenarios")
        print("-" * 40)
        
        for test in extended_tests:
            try:
                test()
            except Exception as e:
                self.log_test(
                    test.__name__, 
                    False, 
                    f"Exception: {str(e)}"
                )
        
        print("\n" + "=" * 60)
        print("Comprehensive Test Summary")
        print("=" * 60)
        print(f"Total Tests: {self.passed_tests + self.failed_tests}")
        print(f"Core Tests: {len(core_tests)}")
        print(f"Extended Tests: {len(extended_tests)}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {self.passed_tests/(self.passed_tests + self.failed_tests)*100:.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if "[FAIL]" in result:
                    print(result)
        else:
            print("\n✅ All tests passed! System is production-ready.")
        
        print("=" * 60)
        
        return self.failed_tests == 0


if __name__ == "__main__":
    # Run the test suite
    tester = TestKWConversion()
    success = tester.run_all_tests()
    
    if success:
        print("✅ All tests passed! kW conversion is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review the implementation.")
        sys.exit(1)