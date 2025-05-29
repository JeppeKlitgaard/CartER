# Handover

For Ananya:

- Spruce up the pyproject.toml file
- Change from flake8, black and other linters to ruff
- Fix inevitable breakage from updating
- See if it can run on Python 3.13, otherwise try Python 3.12
- Delete poetry.lock when `uv`-based system works

What Jeppe would do different second time around (don't start here though, mostly hardware related)
- Use OpenBuild eco-system for mechanical parts
- Switch to STM32 Nucleo instead of rather cursed Arduino 32-bit
  - This would use stm32duino so framework 'core' is still similar, only minor changes needed in controller firmware
- Switch to ProtoBuf protocol over home-made Plain-Ol-Datatypes binary protocol
