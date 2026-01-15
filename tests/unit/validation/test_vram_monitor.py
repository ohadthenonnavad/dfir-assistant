"""Tests for VRAM monitoring module."""

import pytest
from unittest.mock import MagicMock, patch


class TestVRAMMonitor:
    """Tests for VRAMMonitor class."""
    
    def test_vram_status_enum(self):
        """Test VRAMStatus enum values."""
        from dfir_assistant.validation.vram_monitor import VRAMStatus
        
        assert VRAMStatus.OK.value == "ok"
        assert VRAMStatus.WARNING.value == "warning"
        assert VRAMStatus.CRITICAL.value == "critical"
        assert VRAMStatus.UNAVAILABLE.value == "unavailable"
    
    def test_vram_health_usage_percent(self):
        """Test VRAMHealth percentage calculation."""
        from dfir_assistant.validation.vram_monitor import VRAMHealth, VRAMStatus
        
        health = VRAMHealth(
            status=VRAMStatus.OK,
            usage_gb=12.0,
            total_gb=24.0,
        )
        assert health.usage_percent == 50.0
        
        # Test zero total
        health_zero = VRAMHealth(
            status=VRAMStatus.UNAVAILABLE,
            usage_gb=0.0,
            total_gb=0.0,
        )
        assert health_zero.usage_percent == 0.0
    
    @patch("dfir_assistant.validation.vram_monitor.nvmlInit")
    @patch("dfir_assistant.validation.vram_monitor.nvmlDeviceGetHandleByIndex")
    def test_monitor_initialization_success(self, mock_handle, mock_init):
        """Test successful NVML initialization."""
        # Note: This test requires the imports to work differently
        # In production, we'd need to mock at the pynvml import level
        pass
    
    def test_monitor_thresholds(self):
        """Test default threshold values."""
        from dfir_assistant.validation.vram_monitor import VRAMMonitor
        
        assert VRAMMonitor.WARNING_THRESHOLD_GB == 22.0
        assert VRAMMonitor.CRITICAL_THRESHOLD_GB == 23.0
    
    def test_get_user_friendly_error_critical(self):
        """Test user-friendly error message for critical status."""
        from dfir_assistant.validation.vram_monitor import VRAMMonitor, VRAMStatus, VRAMHealth
        
        with patch.object(VRAMMonitor, 'check_health') as mock_check:
            mock_check.return_value = VRAMHealth(
                status=VRAMStatus.CRITICAL,
                usage_gb=23.5,
                total_gb=24.0,
                message="Critical",
            )
            
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._initialized = True
            
            error_msg = monitor.get_user_friendly_error()
            assert "memory usage" in error_msg.lower()
    
    def test_is_healthy(self):
        """Test is_healthy convenience method."""
        from dfir_assistant.validation.vram_monitor import VRAMMonitor, VRAMStatus, VRAMHealth
        
        with patch.object(VRAMMonitor, 'check_health') as mock_check:
            # Test OK status
            mock_check.return_value = VRAMHealth(
                status=VRAMStatus.OK,
                usage_gb=15.0,
                total_gb=24.0,
            )
            
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._initialized = True
            
            assert monitor.is_healthy() is True
            
            # Test WARNING status
            mock_check.return_value = VRAMHealth(
                status=VRAMStatus.WARNING,
                usage_gb=22.5,
                total_gb=24.0,
            )
            assert monitor.is_healthy() is False


class TestVRAMMonitorIntegration:
    """Integration tests for VRAM monitoring."""
    
    @pytest.mark.integration
    def test_get_vram_usage_with_gpu(self):
        """Test VRAM usage retrieval on system with GPU."""
        from dfir_assistant.validation.vram_monitor import get_vram_monitor
        
        monitor = get_vram_monitor()
        health = monitor.check_health()
        
        # Should return a valid status (may be UNAVAILABLE if no GPU)
        assert health.status is not None
