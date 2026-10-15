# Calculator App UI Update

This update adds a modern left navigation sidebar inspired by the reference design while keeping the existing calculator engine and feature windows.

## Run

From this project folder in VS Code, open Terminal and run:

```powershell
python main.py
```

If CustomTkinter is not installed, install it with:

```powershell
python -m pip install customtkinter
```

Then run `python main.py` again.

## Sidebar

- Standard: return to the basic keypad.
- Scientific: show/hide the scientific keypad.
- Graphing: open the existing graph window.
- Programming: open the existing programmer calculator.
- Currency / Volume / Units: open the existing unit conversion window (the current project does not yet have a separate live currency-data service).
- Settings: switch theme and view keyboard shortcuts.

## Verify existing features

```powershell
python -m pytest -q
```

The supplied ZIP had 474 tests. They pass after the UI update in the development environment. Your local copy may have additional tests; run the command above to verify all of them.
