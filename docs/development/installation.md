# Installation

This is an installation guide for getting setup with the software side of 
things.

It assumes:
- Linux Environment
- Basic knowledge of terminal environment
- Visual Studio Code installed
- Git installed
- Python 3.9+ installed

## 1 - Clone project

```sh
git clone https://github.com/JeppeKlitgaard/CartER.git
```

## 2 - Platform.io

- Open the `CartER` folder in `vscode`.
- Install `platformio` if not already installed.
- If on Linux make sure to follow [PlatformIO guide to udev setup](https://docs.platformio.org/en/latest/faq.html#platformio-udev-rules)
- Add the `CartER/controller/` folder to `vscode` (`Workspaces: Add Folder to Workspace...`)
- Restart `vscode`
- Run `pio run` in a Platform IO terminal (`PlatformIO: New Terminal`)

## 3 - Poetry

- [Install Poetry](https://python-poetry.org/docs/#installation)
- Configure `poetry` to use local `venv` by running `poetry config virtualenvs.in-project true`
- Run `poetry install` in `CartER/` directory

!!! Note "Virtual Environments"
    The rest of this guide assumes you are in a terminal with the project virtualenv activated.

    You can activate the virtualenv by running `poetry shell` in the `CartER/` directory.


## 4 - Test

Now test that you can:
- Build the `controller` source using: `PlatformIO: Build` in `vscode`.
- Upload to the microcontroller using `PlatformIO: Upload` in `vscode`.
- Perform an experiment using `carter experiment` in a virtualenv'd shell.