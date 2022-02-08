# tpg26x

Library and CLI tool for the Pfeiffer TPG26x series over serial ports.

## Installation

As of now, you can install the library using `pip`, but Git is required for the installation:

```
pip install git+https://github.com/jjj999/tpg26x.git
```

## Quickstart

This package is not only a library, but also a CLI tool. You can use the CLI tool and retrieve the actual data from your TPG26x, after connecting the TPG26x and your PC:

```
python -m tpg26x [port, e.g. COM0]
```
