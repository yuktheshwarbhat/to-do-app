# Pi ToDo Pro 🍓

![CI](https://github.com/yuktheshwarbhat/to-do-app/actions/workflows/test.yml/badge.svg)

An interactive ToDo app built with Flask + SQLite on a Raspberry Pi, tested with pytest and guarded by GitHub Actions.

## Features
- 🔥 Priority levels (High / Medium / Low) with color badges
- ✏️ Double-click to edit any todo inline
- 🧹 Clear all completed tasks in one click
- 🌙 Dark mode (remembered per browser)
- 📊 Live stats + progress bar
- 🔀 Filter: All / Active / Done
- 🧪 27 automated tests, CI runs on every PR

## Run
    python app.py

Open http://raspberrypi.local:5000

## Test
    pytest -v