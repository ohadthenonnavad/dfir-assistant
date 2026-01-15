"""VRAM Monitoring for runtime memory pressure detection.

This module provides VRAM monitoring capabilities to detect and respond
to memory pressure during inference.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class VRAMStatus(Enum):
    """VRAM health status levels."""
    
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


@dataclass
class VRAMHealth:
    """VRAM health check result."""
    
    status: VRAMStatus
    usage_gb: float
    total_gb: float
    message: str | None = None
    
    @property
    def usage_percent(self) -> float:
        """Get VRAM usage as percentage."""
        if self.total_gb <= 0:
            return 0.0
        return (self.usage_gb / self.total_gb) * 100


class VRAMMonitor:
    """Monitor GPU VRAM usage and detect memory pressure.
    
    Attributes:
        WARNING_THRESHOLD_GB: VRAM usage level that triggers warnings
        CRITICAL_THRESHOLD_GB: VRAM usage level that triggers critical alerts
        
    Example:
        >>> monitor = VRAMMonitor()
        >>> health = monitor.check_health()
        >>> if health.status == VRAMStatus.CRITICAL:
        ...     # Handle memory pressure
        ...     pass
    """
    
    WARNING_THRESHOLD_GB: float = 22.0
    CRITICAL_THRESHOLD_GB: float = 23.0
    
    def __init__(
        self,
        warning_threshold: float | None = None,
        critical_threshold: float | None = None,
        on_warning: Callable[[VRAMHealth], None] | None = None,
        on_critical: Callable[[VRAMHealth], None] | None = None,
    ):
        """Initialize VRAM monitor.
        
        Args:
            warning_threshold: Custom warning threshold in GB
            critical_threshold: Custom critical threshold in GB
            on_warning: Callback for warning events
            on_critical: Callback for critical events
        """
        if warning_threshold is not None:
            self.WARNING_THRESHOLD_GB = warning_threshold
        if critical_threshold is not None:
            self.CRITICAL_THRESHOLD_GB = critical_threshold
            
        self._on_warning = on_warning
        self._on_critical = on_critical
        self._handle = None
        self._initialized = False
        
        self._init_nvml()
    
    def _init_nvml(self) -> bool:
        """Initialize NVIDIA Management Library."""
        try:
            from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex
            nvmlInit()
            self._handle = nvmlDeviceGetHandleByIndex(0)
            self._initialized = True
            logger.debug("NVML initialized successfully")
            return True
        except ImportError:
            logger.warning("pynvml not installed - VRAM monitoring unavailable")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize NVML: {e}")
            return False
    
    def get_usage_gb(self) -> float:
        """Get current VRAM usage in GB.
        
        Returns:
            VRAM usage in GB, or -1.0 if unavailable
        """
        if not self._initialized or self._handle is None:
            return -1.0
            
        try:
            from pynvml import nvmlDeviceGetMemoryInfo
            info = nvmlDeviceGetMemoryInfo(self._handle)
            return info.used / (1024 ** 3)
        except Exception as e:
            logger.error(f"Failed to get VRAM usage: {e}")
            return -1.0
    
    def get_total_gb(self) -> float:
        """Get total VRAM in GB.
        
        Returns:
            Total VRAM in GB, or -1.0 if unavailable
        """
        if not self._initialized or self._handle is None:
            return -1.0
            
        try:
            from pynvml import nvmlDeviceGetMemoryInfo
            info = nvmlDeviceGetMemoryInfo(self._handle)
            return info.total / (1024 ** 3)
        except Exception as e:
            logger.error(f"Failed to get total VRAM: {e}")
            return -1.0
    
    def check_health(self) -> VRAMHealth:
        """Check VRAM health status.
        
        Returns:
            VRAMHealth with current status and measurements
            
        Side effects:
            - Logs VRAM usage at INFO level
            - Triggers callbacks on warning/critical
        """
        usage = self.get_usage_gb()
        total = self.get_total_gb()
        
        if usage < 0 or total < 0:
            return VRAMHealth(
                status=VRAMStatus.UNAVAILABLE,
                usage_gb=0.0,
                total_gb=0.0,
                message="VRAM monitoring unavailable - no GPU or driver issue",
            )
        
        logger.info(f"VRAM usage: {usage:.2f} GB / {total:.2f} GB ({usage/total*100:.1f}%)")
        
        if usage >= self.CRITICAL_THRESHOLD_GB:
            health = VRAMHealth(
                status=VRAMStatus.CRITICAL,
                usage_gb=usage,
                total_gb=total,
                message=f"🔴 Critical VRAM pressure ({usage:.1f}GB) - service may be unstable",
            )
            logger.error(health.message)
            if self._on_critical:
                self._on_critical(health)
            return health
            
        if usage >= self.WARNING_THRESHOLD_GB:
            health = VRAMHealth(
                status=VRAMStatus.WARNING,
                usage_gb=usage,
                total_gb=total,
                message=f"⚠️ High VRAM usage ({usage:.1f}GB) - monitoring closely",
            )
            logger.warning(health.message)
            if self._on_warning:
                self._on_warning(health)
            return health
        
        return VRAMHealth(
            status=VRAMStatus.OK,
            usage_gb=usage,
            total_gb=total,
            message=None,
        )
    
    def get_user_friendly_error(self) -> str:
        """Get user-friendly error message for memory pressure.
        
        Returns:
            Friendly message suitable for displaying to users
        """
        health = self.check_health()
        
        if health.status == VRAMStatus.CRITICAL:
            return (
                "⚠️ The system is experiencing high memory usage. "
                "Your response may be delayed or incomplete. "
                "Please try again in a few moments or simplify your question."
            )
        elif health.status == VRAMStatus.WARNING:
            return (
                "Note: System resources are currently constrained. "
                "Response time may be longer than usual."
            )
        return ""
    
    def is_healthy(self) -> bool:
        """Quick check if VRAM usage is within safe limits.
        
        Returns:
            True if VRAM usage is OK, False otherwise
        """
        health = self.check_health()
        return health.status == VRAMStatus.OK


# Singleton instance for easy access
_monitor: VRAMMonitor | None = None


def get_vram_monitor() -> VRAMMonitor:
    """Get or create the global VRAM monitor instance.
    
    Returns:
        VRAMMonitor singleton instance
    """
    global _monitor
    if _monitor is None:
        _monitor = VRAMMonitor()
    return _monitor


def check_vram_health() -> VRAMHealth:
    """Convenience function to check VRAM health.
    
    Returns:
        VRAMHealth with current status
    """
    return get_vram_monitor().check_health()
