"""
Advanced Screen Share Detection & Hiding
Based on Cluely AI's approach to hide interface from screen share viewers.
Uses multiple detection methods for reliability.
"""
import logging
import subprocess
import ctypes
import threading
import time
from typing import Optional
import win32gui
import win32process

logger = logging.getLogger(__name__)


class ScreenShareDetector:
    """
    Detects when screen is being shared across various platforms:
    - Microsoft Teams
    - Zoom
    - Google Meet
    - Discord
    - OBS
    """
    
    # Known screen sharing process names
    SCREEN_SHARE_PROCESSES = {
        # Teams
        'Teams.exe',
        'TeamsHelper.exe',
        'TeamsMeetingHelper.exe',
        
        # Zoom
        'Zoom.exe',
        'ZoomAudioDevice.exe',
        
        # Google Meet / Chrome
        'chrome.exe',  # When screen sharing active
        'msedge.exe',  # Edge with screen share
        'firefox.exe',  # Firefox screen share
        
        # Discord
        'Discord.exe',
        
        # OBS / Screen capture
        'obs64.exe',
        'OBS.exe',
        'ScreenDropper.exe',
    }
    
    # Window class names that indicate screen sharing
    SCREEN_SHARE_WINDOW_CLASSES = [
        'CAAKHWndDisplayFeed',  # Teams screen share
        'ScreenShareWnd',        # Generic screen share
    ]
    
    def __init__(self):
        self.is_screen_shared = False
        self.detection_thread = None
        self.stop_detection = False
        self.callbacks = []
    
    def add_callback(self, callback):
        """Add a callback function for screen share state changes"""
        self.callbacks.append(callback)
    
    def _call_callbacks(self, is_sharing: bool):
        """Call all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(is_sharing)
            except Exception as e:
                logger.error(f"Error in screen share callback: {e}")
    
    def start_detection(self):
        """Start background detection thread"""
        if self.detection_thread is None or not self.detection_thread.is_alive():
            self.stop_detection = False
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            logger.info("Screen share detection started")
    
    def stop_detection_thread(self):
        """Stop detection thread"""
        self.stop_detection = True
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        logger.info("Screen share detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        while not self.stop_detection:
            try:
                is_sharing = self._check_screen_sharing()
                
                # Only call callbacks if state changed
                if is_sharing != self.is_screen_shared:
                    self.is_screen_shared = is_sharing
                    self._call_callbacks(is_sharing)
                    status = "ACTIVE" if is_sharing else "STOPPED"
                    logger.info(f"Screen sharing {status}")
                
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(2)
    
    def _check_screen_sharing(self) -> bool:
        """Check multiple indicators of screen sharing"""
        
        # Method 1: Check for active screen sharing processes
        if self._check_active_processes():
            return True
        
        # Method 2: Check window hierarchy
        if self._check_window_hierarchy():
            return True
        
        # Method 3: Check Windows API for display duplication
        if self._check_display_duplication():
            return True
        
        return False
    
    def _check_active_processes(self) -> bool:
        """Check if screen sharing applications are running"""
        try:
            result = subprocess.run(
                ['tasklist', '/v', '/fo', 'csv'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            process_list = result.stdout.lower()
            
            # Check for Teams
            if 'teamsmeetinghelper' in process_list or 'teamshwnd' in process_list:
                return True
            
            # Check for Zoom
            if 'zoom' in process_list:
                return True
            
            # Check for Google Meet (Chrome with specific flags)
            if 'chrome' in process_list or 'msedge' in process_list:
                # This is a heuristic - not 100% reliable
                return self._check_chromium_sharing()
            
            return False
        except Exception as e:
            logger.debug(f"Error checking processes: {e}")
            return False
    
    def _check_chromium_sharing(self) -> bool:
        """Check if Chrome/Edge is actively sharing screen"""
        try:
            # Check for specific windows that appear when sharing
            result = subprocess.run(
                ['wmic', 'process', 'list', 'brief'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Look for indicators of screen share
            return 'chrome' in result.stdout.lower() and 'screen' in result.stdout.lower()
        except:
            return False
    
    def _check_window_hierarchy(self) -> bool:
        """Check Windows for screen share windows"""
        try:
            # Get all windows
            windows = []
            
            def enum_windows(hwnd, lParam):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    cls = win32gui.GetClassName(hwnd)
                    windows.append((title, cls))
                return True
            
            win32gui.EnumWindows(enum_windows, None)
            
            # Check for screen share indicators
            for title, cls in windows:
                # Teams indicators
                if 'presenting' in title.lower() or 'screen share' in title.lower():
                    return True
                
                if cls in self.SCREEN_SHARE_WINDOW_CLASSES:
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking window hierarchy: {e}")
            return False
    
    def _check_display_duplication(self) -> bool:
        """Check using Windows Display Duplication API"""
        try:
            # This is a Windows-specific check using DirectX
            # When screen is being duplicated (captured), this returns specific values
            
            user32 = ctypes.windll.user32
            
            # Check for remote session (RDP)
            if user32.GetSystemMetrics(4096):  # SM_REMOTESESSION
                return True
            
            # Check for mirroring
            num_displays = user32.GetSystemMetrics(18)  # SM_CMONITORS
            if num_displays > 1:
                # Multiple displays might indicate mirroring
                return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking display duplication: {e}")
            return False


class HiddenOverlayManager:
    """
    Manages hiding/showing overlay based on screen share state.
    Implements Cluely AI's approach of completely hiding the interface.
    """
    
    def __init__(self, overlay_widget):
        self.overlay = overlay_widget
        self.detector = ScreenShareDetector()
        self.was_visible = False
        
        # Add callback for screen share changes
        self.detector.add_callback(self.on_screen_share_changed)
    
    def on_screen_share_changed(self, is_sharing: bool):
        """Called when screen share state changes"""
        if is_sharing:
            # Screen sharing started - hide overlay
            self.was_visible = self.overlay.isVisible()
            self.overlay.hide()
            logger.info("Overlay hidden - screen sharing detected")
        else:
            # Screen sharing stopped - restore visibility
            if self.was_visible:
                self.overlay.show()
                self.overlay.raise_()
                self.overlay.activateWindow()
                logger.info("Overlay shown - screen sharing stopped")
    
    def start(self):
        """Start monitoring screen share"""
        self.detector.start_detection()
    
    def stop(self):
        """Stop monitoring screen share"""
        self.detector.stop_detection_thread()
    
    def get_sharing_status(self) -> bool:
        """Get current screen sharing status"""
        return self.detector.is_screen_shared
