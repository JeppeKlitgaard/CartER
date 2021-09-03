# Introduction

The development documentation is not complete, but does contain some useful pointers
on how to set up the system as well as discussions of some common issues
around serial connections, steppers, and networking.

## Project layout

    mkdocs.yml          # Documentation configuration file.
    docs/**             # Documentation files.
    pyproject.toml      # Poetry project configuration.
    commander/**        # Commander code.
    controller/
        platformio.ini  # Platform.io project configuration.
        **              # Controller code.
    notebooks/**        # Notebooks that are helpful in debugging or studying experiment.
