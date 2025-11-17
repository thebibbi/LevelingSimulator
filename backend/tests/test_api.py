"""
API endpoint tests for Platform Leveling System
"""

import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints"""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "All systems operational"


class TestConfigurationEndpoints:
    """Test configuration management endpoints"""

    def test_get_configurations(self):
        response = client.get("/configurations")
        assert response.status_code == 200
        data = response.json()
        assert "configurations" in data
        configs = data["configurations"]
        assert len(configs) == 7
        assert all("id" in c for c in configs)
        assert all("name" in c for c in configs)

    def test_get_config(self):
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "base_radius" in data
        assert "platform_radius" in data
        assert "nominal_leg_length" in data

    def test_update_config(self):
        new_config = {
            "base_radius": 130.0,
            "platform_radius": 75.0,
            "nominal_leg_length": 160.0,
            "min_leg_length": 110.0,
            "max_leg_length": 210.0,
        }
        response = client.post("/config", json=new_config)
        assert response.status_code == 200
        data = response.json()
        assert data["base_radius"] == 130.0
        assert data["platform_radius"] == 75.0


class TestIKCalculation:
    """Test inverse kinematics calculation endpoints"""

    def test_calculate_neutral_pose(self):
        pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "configuration": "6-3",
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 200
        data = response.json()
        assert "leg_lengths" in data
        assert len(data["leg_lengths"]) == 6
        assert data["valid"] is True
        assert data["configuration"] == "6-3"

    def test_calculate_with_translation(self):
        pose = {
            "x": 10.0,
            "y": 5.0,
            "z": 15.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "configuration": "6-3",
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 200
        data = response.json()
        assert len(data["leg_lengths"]) == 6
        assert all(isinstance(length, float) for length in data["leg_lengths"])

    def test_calculate_with_rotation(self):
        pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "roll": 10.0,
            "pitch": -5.0,
            "yaw": 0.0,
            "configuration": "6-3",
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 200
        data = response.json()
        assert len(data["leg_lengths"]) == 6

    def test_calculate_different_configurations(self):
        configs = ["3-3", "4-4", "6-3", "6-6", "8-8"]
        expected_legs = [3, 4, 6, 6, 8]

        for config, expected in zip(configs, expected_legs):
            pose = {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "configuration": config,
            }
            response = client.post("/calculate", json=pose)
            assert response.status_code == 200
            data = response.json()
            assert len(data["leg_lengths"]) == expected

    def test_calculate_with_custom_geometry(self):
        pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "configuration": "6-3",
            "geometry": {
                "base_radius": 150.0,
                "platform_radius": 80.0,
                "nominal_leg_length": 200.0,
                "min_leg_length": 150.0,
                "max_leg_length": 250.0,
            },
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 200


class TestLevelingCalculation:
    """Test leveling calculation endpoints"""

    def test_level_neutral(self):
        params = {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "configuration": "6-3"}
        response = client.post("/level", params=params)
        assert response.status_code == 200
        data = response.json()
        assert len(data["leg_lengths"]) == 6

    def test_level_with_tilt(self):
        params = {"roll": 10.0, "pitch": 5.0, "yaw": 0.0, "configuration": "6-3"}
        response = client.post("/level", params=params)
        assert response.status_code == 200
        data = response.json()
        assert len(data["leg_lengths"]) == 6
        # Leg lengths should differ when leveling a tilted platform
        assert len(set(data["leg_lengths"])) > 1


class TestInputValidation:
    """Test input validation and error handling"""

    def test_invalid_configuration(self):
        pose = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "configuration": "invalid-config",
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        pose = {"roll": 0.0, "pitch": 0.0}  # Missing other fields
        response = client.post("/calculate", json=pose)
        # Should use defaults or return 422
        assert response.status_code in [200, 422]

    def test_invalid_data_types(self):
        pose = {
            "x": "invalid",  # Should be float
            "y": 0.0,
            "z": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "configuration": "6-3",
        }
        response = client.post("/calculate", json=pose)
        assert response.status_code == 422
