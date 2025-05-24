"""
Tutorial Overlay System for ServMC
Provides visual highlighting and tooltips for UI elements during tutorials
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, List, Tuple, Optional


class TutorialOverlay:
    """Visual overlay system for highlighting UI elements during tutorials"""
    
    def __init__(self, root_window):
        self.root = root_window
        self.overlays = []
        self.tooltips = []
        self.highlights = []
        
    def create_highlight_overlay(self, target_widget, message: str, position: str = "right"):
        """Create a highlight overlay on a specific widget"""
        try:
            # Get widget position and size
            x = target_widget.winfo_rootx()
            y = target_widget.winfo_rooty()
            width = target_widget.winfo_width()
            height = target_widget.winfo_height()
            
            # Create overlay window
            overlay = tk.Toplevel(self.root)
            overlay.title("")
            overlay.attributes("-topmost", True)
            overlay.attributes("-alpha", 0.8)
            overlay.overrideredirect(True)  # Remove window decorations
            
            # Position overlay around the target widget
            if position == "right":
                overlay.geometry(f"250x100+{x + width + 10}+{y}")
            elif position == "left":
                overlay.geometry(f"250x100+{x - 260}+{y}")
            elif position == "top":
                overlay.geometry(f"250x100+{x}+{y - 110}")
            else:  # bottom
                overlay.geometry(f"250x100+{x}+{y + height + 10}")
            
            # Style the overlay
            overlay.configure(bg="#2c3e50")
            
            # Add message
            msg_label = tk.Label(overlay, text=message, 
                               bg="#2c3e50", fg="white",
                               font=("Arial", 10), 
                               wraplength=230,
                               justify=tk.LEFT)
            msg_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # Add arrow pointing to target (simple version)
            if position == "right":
                arrow_label = tk.Label(overlay, text="◀", 
                                     bg="#2c3e50", fg="#3498db",
                                     font=("Arial", 16))
                arrow_label.place(x=5, y=40)
            
            # Store overlay for cleanup
            self.overlays.append(overlay)
            
            # Auto-hide after 5 seconds
            self.root.after(5000, lambda: self.remove_overlay(overlay))
            
            return overlay
            
        except Exception as e:
            print(f"Failed to create highlight overlay: {e}")
            return None
    
    def create_tooltip(self, target_widget, text: str, duration: int = 3000):
        """Create a temporary tooltip for a widget"""
        try:
            # Get widget position
            x = target_widget.winfo_rootx()
            y = target_widget.winfo_rooty()
            height = target_widget.winfo_height()
            
            # Create tooltip window
            tooltip = tk.Toplevel(self.root)
            tooltip.title("")
            tooltip.attributes("-topmost", True)
            tooltip.overrideredirect(True)
            
            # Position below the widget
            tooltip.geometry(f"+{x}+{y + height + 5}")
            
            # Style tooltip
            tooltip.configure(bg="#34495e")
            
            tooltip_label = tk.Label(tooltip, text=text,
                                   bg="#34495e", fg="white",
                                   font=("Arial", 9),
                                   padx=8, pady=4)
            tooltip_label.pack()
            
            # Store for cleanup
            self.tooltips.append(tooltip)
            
            # Auto-remove after duration
            self.root.after(duration, lambda: self.remove_tooltip(tooltip))
            
            return tooltip
            
        except Exception:
            return None
    
    def highlight_widget(self, widget, color: str = "#f39c12", duration: int = 3000):
        """Temporarily highlight a widget by changing its background"""
        try:
            # Store original background
            original_bg = widget.cget("bg")
            
            # Change to highlight color
            widget.configure(bg=color)
            
            # Restore original color after duration
            def restore_bg():
                try:
                    widget.configure(bg=original_bg)
                except Exception:
                    pass
            
            self.root.after(duration, restore_bg)
            
        except Exception:
            # Widget doesn't support background color changes
            pass
    
    def create_step_indicator(self, current_step: int, total_steps: int, 
                            title: str = "", position: Tuple[int, int] = None):
        """Create a step indicator overlay"""
        indicator = tk.Toplevel(self.root)
        indicator.title("")
        indicator.attributes("-topmost", True)
        indicator.overrideredirect(True)
        
        # Position in top-right corner if not specified
        if position is None:
            screen_width = self.root.winfo_screenwidth()
            position = (screen_width - 220, 20)
        
        indicator.geometry(f"200x80+{position[0]}+{position[1]}")
        indicator.configure(bg="#3498db")
        
        # Title
        if title:
            title_label = tk.Label(indicator, text=title, 
                                 bg="#3498db", fg="white",
                                 font=("Arial", 10, "bold"))
            title_label.pack(pady=5)
        
        # Progress
        progress_text = f"Step {current_step} of {total_steps}"
        progress_label = tk.Label(indicator, text=progress_text,
                                bg="#3498db", fg="white",
                                font=("Arial", 9))
        progress_label.pack()
        
        # Progress bar
        progress_frame = tk.Frame(indicator, bg="#3498db")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        progress_bg = tk.Frame(progress_frame, height=4, bg="#2980b9")
        progress_bg.pack(fill=tk.X)
        
        progress_fill_width = int((current_step / total_steps) * 180)
        progress_fill = tk.Frame(progress_frame, height=4, bg="white", width=progress_fill_width)
        progress_fill.place(x=0, y=0)
        
        self.overlays.append(indicator)
        return indicator
    
    def create_welcome_bubble(self, text: str, position: Tuple[int, int] = None):
        """Create a welcome speech bubble"""
        bubble = tk.Toplevel(self.root)
        bubble.title("")
        bubble.attributes("-topmost", True)
        bubble.overrideredirect(True)
        
        # Center on screen if no position given
        if position is None:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            position = (screen_width // 2 - 200, screen_height // 2 - 100)
        
        bubble.geometry(f"400x200+{position[0]}+{position[1]}")
        bubble.configure(bg="#e74c3c")
        
        # Welcome icon
        icon_label = tk.Label(bubble, text="🎉", 
                            bg="#e74c3c", fg="white",
                            font=("Arial", 24))
        icon_label.pack(pady=10)
        
        # Welcome text
        text_label = tk.Label(bubble, text=text,
                            bg="#e74c3c", fg="white",
                            font=("Arial", 12),
                            wraplength=360,
                            justify=tk.CENTER)
        text_label.pack(padx=20, pady=10)
        
        # Close button
        close_btn = tk.Button(bubble, text="Continue",
                            command=lambda: self.remove_overlay(bubble),
                            bg="white", fg="#e74c3c",
                            font=("Arial", 10, "bold"))
        close_btn.pack(pady=10)
        
        self.overlays.append(bubble)
        return bubble
    
    def create_feature_callout(self, feature_name: str, description: str, 
                             target_widget, action_text: str = "Try it!"):
        """Create a callout highlighting a specific feature"""
        try:
            # Position near the target widget
            x = target_widget.winfo_rootx()
            y = target_widget.winfo_rooty()
            width = target_widget.winfo_width()
            height = target_widget.winfo_height()
            
            callout = tk.Toplevel(self.root)
            callout.title("")
            callout.attributes("-topmost", True)
            callout.overrideredirect(True)
            
            # Position to the right of target
            callout.geometry(f"280x120+{x + width + 15}+{y}")
            callout.configure(bg="#27ae60")
            
            # Feature name
            name_label = tk.Label(callout, text=feature_name,
                                bg="#27ae60", fg="white",
                                font=("Arial", 12, "bold"))
            name_label.pack(pady=5)
            
            # Description
            desc_label = tk.Label(callout, text=description,
                                bg="#27ae60", fg="white",
                                font=("Arial", 9),
                                wraplength=260,
                                justify=tk.CENTER)
            desc_label.pack(padx=10, pady=5)
            
            # Action button
            action_btn = tk.Button(callout, text=action_text,
                                 command=lambda: self.remove_overlay(callout),
                                 bg="white", fg="#27ae60",
                                 font=("Arial", 9, "bold"))
            action_btn.pack(pady=5)
            
            # Add arrow pointing to target
            arrow_label = tk.Label(callout, text="◀", 
                                 bg="#27ae60", fg="white",
                                 font=("Arial", 14))
            arrow_label.place(x=5, y=50)
            
            self.overlays.append(callout)
            
            # Auto-remove after 10 seconds
            self.root.after(10000, lambda: self.remove_overlay(callout))
            
            return callout
            
        except Exception:
            return None
    
    def remove_overlay(self, overlay):
        """Remove a specific overlay"""
        try:
            if overlay in self.overlays:
                self.overlays.remove(overlay)
            overlay.destroy()
        except Exception:
            pass
    
    def remove_tooltip(self, tooltip):
        """Remove a specific tooltip"""
        try:
            if tooltip in self.tooltips:
                self.tooltips.remove(tooltip)
            tooltip.destroy()
        except Exception:
            pass
    
    def clear_all_overlays(self):
        """Remove all overlays and tooltips"""
        # Clear overlays
        for overlay in self.overlays[:]:
            try:
                overlay.destroy()
            except Exception:
                pass
        self.overlays.clear()
        
        # Clear tooltips
        for tooltip in self.tooltips[:]:
            try:
                tooltip.destroy()
            except Exception:
                pass
        self.tooltips.clear()
    
    def create_tutorial_navigation(self, on_next=None, on_prev=None, on_skip=None,
                                 current_step: int = 1, total_steps: int = 1):
        """Create navigation controls for tutorials"""
        nav = tk.Toplevel(self.root)
        nav.title("")
        nav.attributes("-topmost", True)
        nav.overrideredirect(True)
        
        # Position at bottom center
        screen_width = self.root.winfo_screenwidth()
        nav.geometry(f"300x60+{screen_width // 2 - 150}+{self.root.winfo_screenheight() - 100}")
        nav.configure(bg="#34495e")
        
        # Navigation buttons
        btn_frame = tk.Frame(nav, bg="#34495e")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Previous button
        if on_prev and current_step > 1:
            prev_btn = tk.Button(btn_frame, text="← Previous",
                                command=on_prev,
                                bg="#95a5a6", fg="white")
            prev_btn.pack(side=tk.LEFT)
        
        # Step indicator
        step_label = tk.Label(btn_frame, text=f"{current_step}/{total_steps}",
                            bg="#34495e", fg="white",
                            font=("Arial", 10))
        step_label.pack(side=tk.LEFT, expand=True)
        
        # Skip button
        if on_skip:
            skip_btn = tk.Button(btn_frame, text="Skip",
                               command=on_skip,
                               bg="#e74c3c", fg="white")
            skip_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Next button
        if on_next:
            next_text = "Finish" if current_step == total_steps else "Next →"
            next_btn = tk.Button(btn_frame, text=next_text,
                               command=on_next,
                               bg="#3498db", fg="white")
            next_btn.pack(side=tk.RIGHT)
        
        self.overlays.append(nav)
        return nav


class TutorialTooltipManager:
    """Manages contextual tooltips that appear when hovering over UI elements"""
    
    def __init__(self, root_window):
        self.root = root_window
        self.active_tooltips = {}
        self.tooltip_data = self._load_tooltip_data()
    
    def _load_tooltip_data(self) -> Dict:
        """Load tooltip definitions for UI elements"""
        return {
            "new_server_button": {
                "text": "Click here to create a new Minecraft server!\nChoose from Vanilla, Forge, Fabric, Paper, and more.",
                "position": "bottom"
            },
            "mod_browser": {
                "text": "Browse and install mods directly from Modrinth.\nSupports Forge, Fabric, and Quilt mods.",
                "position": "right"
            },
            "backup_button": {
                "text": "Create backups of your server worlds.\nAlways backup before installing mods!",
                "position": "top"
            },
            "network_tab": {
                "text": "Configure port forwarding and firewall settings\nto let friends connect to your server.",
                "position": "bottom"
            }
        }
    
    def add_tooltip(self, widget, tooltip_id: str):
        """Add a tooltip to a widget"""
        tooltip_data = self.tooltip_data.get(tooltip_id)
        if not tooltip_data:
            return
        
        def show_tooltip(event):
            tooltip = tk.Toplevel(self.root)
            tooltip.title("")
            tooltip.attributes("-topmost", True)
            tooltip.overrideredirect(True)
            
            # Position tooltip based on preference
            x = event.widget.winfo_rootx()
            y = event.widget.winfo_rooty()
            
            if tooltip_data["position"] == "bottom":
                y += event.widget.winfo_height() + 5
            elif tooltip_data["position"] == "top":
                y -= 60
            elif tooltip_data["position"] == "right":
                x += event.widget.winfo_width() + 5
            
            tooltip.geometry(f"+{x}+{y}")
            tooltip.configure(bg="#2c3e50")
            
            text_label = tk.Label(tooltip, text=tooltip_data["text"],
                                bg="#2c3e50", fg="white",
                                font=("Arial", 9),
                                justify=tk.LEFT,
                                padx=8, pady=6)
            text_label.pack()
            
            self.active_tooltips[widget] = tooltip
        
        def hide_tooltip(event):
            if widget in self.active_tooltips:
                try:
                    self.active_tooltips[widget].destroy()
                    del self.active_tooltips[widget]
                except Exception:
                    pass
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def clear_all_tooltips(self):
        """Remove all active tooltips"""
        for tooltip in self.active_tooltips.values():
            try:
                tooltip.destroy()
            except Exception:
                pass
        self.active_tooltips.clear()


def create_visual_tutorial_system(root_window):
    """Create and return visual tutorial components"""
    overlay_system = TutorialOverlay(root_window)
    tooltip_manager = TutorialTooltipManager(root_window)
    
    return {
        "overlay": overlay_system,
        "tooltips": tooltip_manager,
        "highlight_widget": overlay_system.highlight_widget,
        "create_callout": overlay_system.create_feature_callout,
        "clear_all": overlay_system.clear_all_overlays
    } 