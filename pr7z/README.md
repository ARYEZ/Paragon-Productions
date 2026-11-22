# Paragon PR7-Z (working name)

A personal archive manager that works like 7-Zip File Manager, in the Paragon family's OBSIDIAN look
(the PR7 plugins / Paragon Photo: `docs/paragon-finish-spec.md` in Paragon-Photo).

**Status: mock-up for approval.** The window and the Add to Archive dialog are real PySide6 code, but
nothing is wired to an engine yet. Screenshots: `docs/mockup/`.

- `pr7z/theme.py`: the family palette, gradient and Qt style sheet.
- `pr7z/widgets.py`: the PR7-Z mark, header, piano-black toolbar keys, line icons.
- `pr7z/main_window.py`, `pr7z/add_dialog.py`: the screens.
- `pr7z/fonts/`: Inter (SIL OFL 1.1), from the PR7 plugins.

Render the screenshots: `QT_SCALE_FACTOR=2 python tools/mockup.py docs/mockup`
