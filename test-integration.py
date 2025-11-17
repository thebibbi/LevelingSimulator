#!/usr/bin/env python3
"""
Integration test script for Platform Leveling System
Tests backend API endpoints and validates responses
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def color_print(message: str, color: str = "green"):
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")

def test_health_check() -> bool:
    """Test the health check endpoint"""
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            color_print(f"✓ Health check passed: {data.get('status')}", "green")
            return True
        else:
            color_print(f"✗ Health check failed with status {response.status_code}", "red")
            return False
    except Exception as e:
        color_print(f"✗ Health check error: {e}", "red")
        return False

def test_configurations() -> bool:
    """Test getting available configurations"""
    print("\n2. Testing Configurations Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/configurations", timeout=5)
        if response.status_code == 200:
            data = response.json()
            configs = data.get('configurations', [])
            color_print(f"✓ Found {len(configs)} configurations", "green")
            for config in configs[:3]:  # Show first 3
                print(f"   - {config['id']}: {config['name']}")
            return True
        else:
            color_print(f"✗ Configurations endpoint failed", "red")
            return False
    except Exception as e:
        color_print(f"✗ Configurations error: {e}", "red")
        return False

def test_ik_calculation() -> bool:
    """Test inverse kinematics calculation"""
    print("\n3. Testing IK Calculation...")
    try:
        pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 10.0,
            "roll": 5.0,
            "pitch": -3.0,
            "yaw": 0.0,
            "configuration": "6-3"
        }

        response = requests.post(
            f"{API_BASE_URL}/calculate",
            json=pose,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            color_print(f"✓ IK calculation successful", "green")
            print(f"   Configuration: {data['configuration']}")
            print(f"   Valid: {data['valid']}")
            print(f"   Leg lengths: {[f'{l:.2f}' for l in data['leg_lengths'][:3]]}...")
            return True
        else:
            color_print(f"✗ IK calculation failed with status {response.status_code}", "red")
            return False
    except Exception as e:
        color_print(f"✗ IK calculation error: {e}", "red")
        return False

def test_leveling_calculation() -> bool:
    """Test leveling calculation"""
    print("\n4. Testing Leveling Calculation...")
    try:
        params = {
            "roll": 10.0,
            "pitch": 5.0,
            "yaw": 0.0,
            "configuration": "6-3"
        }

        response = requests.post(
            f"{API_BASE_URL}/level",
            params=params,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            color_print(f"✓ Leveling calculation successful", "green")
            print(f"   Configuration: {data['configuration']}")
            print(f"   Valid: {data['valid']}")
            return True
        else:
            color_print(f"✗ Leveling calculation failed", "red")
            return False
    except Exception as e:
        color_print(f"✗ Leveling calculation error: {e}", "red")
        return False

def test_config_management() -> bool:
    """Test configuration get/set"""
    print("\n5. Testing Configuration Management...")
    try:
        # Get current config
        response = requests.get(f"{API_BASE_URL}/config", timeout=5)
        if response.status_code != 200:
            color_print(f"✗ Get config failed", "red")
            return False

        original_config = response.json()

        # Update config
        new_config = {
            "base_radius": 125.0,
            "platform_radius": 75.0,
            "nominal_leg_length": 155.0,
            "min_leg_length": 105.0,
            "max_leg_length": 205.0
        }

        response = requests.post(
            f"{API_BASE_URL}/config",
            json=new_config,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            color_print(f"✓ Configuration management successful", "green")
            print(f"   Base radius: {data['base_radius']} mm")
            print(f"   Platform radius: {data['platform_radius']} mm")
            return True
        else:
            color_print(f"✗ Update config failed", "red")
            return False
    except Exception as e:
        color_print(f"✗ Config management error: {e}", "red")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Platform Leveling System - Integration Tests")
    print("=" * 60)

    # Check if backend is running
    try:
        requests.get(f"{API_BASE_URL}/", timeout=2)
    except:
        color_print("\n✗ Backend is not running!", "red")
        color_print("Please start the backend first: python backend/api.py", "yellow")
        sys.exit(1)

    # Run tests
    tests = [
        test_health_check,
        test_configurations,
        test_ik_calculation,
        test_leveling_calculation,
        test_config_management,
    ]

    results = []
    for test in tests:
        results.append(test())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        color_print(f"\n✓ All {total} tests passed!", "green")
        sys.exit(0)
    else:
        color_print(f"\n✗ {passed}/{total} tests passed", "red")
        sys.exit(1)

if __name__ == "__main__":
    main()
