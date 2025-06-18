
# Timed Typer

Timed Typer is a Python application that automates typing text into any application at a controlled speed. It supports various targeting methods, including current cursor position, saved click position, screen center, and image recognition. Users can configure total typing time, initial delay, repeat count, and pause between repetitions.

## Features

*   **Controlled Typing Speed:** Type text at a specified duration.
*   **Multiple Target Methods:**
    *   Current cursor position
    *   Saved click position (reusable)
    *   Center of the screen
    *   Image recognition (requires `opencv-python`)
*   **Configurable Parameters:** Set total typing time, initial delay, repeat count, and pause between repetitions.
*   **Hotkey Support:** Stop typing with `Ctrl+Shift+S`.
*   **Failsafe:** Move mouse to the top-left corner to stop typing.
*   **Text Import:** Load text from a file.
*   **Debug Mode:** Provides console output for troubleshooting.

## How to Use

1.  **Run the Application:** Execute the Python script.
2.  **Enter Text:** Type or import the text you want to type into the provided text area.
3.  **Configure Settings:** Adjust the total time, delay, repeat count, and pause between repetitions.
4.  **Choose Target:** Select how the application should determine where to type (current cursor, click position, screen center, or image).
5.  **Start Typing:** Click the "Start Typing" button.
6.  **Stop Typing:** Use the `Ctrl+Shift+S` hotkey or move your mouse to the top-left corner of the screen.

## Requirements

*   Python 3.x
*   `pyautogui`
*   `keyboard`
*   `pynput`
*   `Pillow` (for tray icon, if enabled)
*   `pystray` (for tray icon, if enabled)
*   `opencv-python` (for image targeting)

## Installation

```bash
pip install pyautogui keyboard pynput Pillow pystray opencv-python
```


