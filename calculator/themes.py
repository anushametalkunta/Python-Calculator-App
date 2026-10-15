# calculator/themes.py
# Fonts and colors. Change them here to restyle the whole calculator.

FONT_NAME = "Segoe UI"

THEMES = {
    "light": {
        "window_bg": "#f2f2f7",
        "display_bg": "#ffffff",
        "display_fg": "#1c1c1e",
        "sub_fg": "#8e8e93",
        "number": {"bg": "#ffffff", "fg": "#1c1c1e", "active": "#e5e5ea"},
        "function": {"bg": "#d1d1d6", "fg": "#1c1c1e", "active": "#bcbcc2"},
        "operator": {"bg": "#ff9f0a", "fg": "#ffffff", "active": "#e08a00"},
        "equals": {"bg": "#0a84ff", "fg": "#ffffff", "active": "#0070e0"},
        "toggle_text": "Dark mode",
    },
    "dark": {
        "window_bg": "#1c1c1e",
        "display_bg": "#2c2c2e",
        "display_fg": "#ffffff",
        "sub_fg": "#aeaeb2",
        "number": {"bg": "#3a3a3c", "fg": "#ffffff", "active": "#505053"},
        "function": {"bg": "#636366", "fg": "#ffffff", "active": "#7a7a7e"},
        "operator": {"bg": "#ff9f0a", "fg": "#ffffff", "active": "#e08a00"},
        "equals": {"bg": "#0a84ff", "fg": "#ffffff", "active": "#0070e0"},
        "toggle_text": "Light mode",
    },
}