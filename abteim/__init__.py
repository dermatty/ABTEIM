from .abteim import *
from importlib.metadata import version
import toml

try:
    with open("pyproject.toml", mode="r") as config:
        toml_file = toml.load(config)
    __version__ = toml_file["tool"]["poetry"]["version"]
    __appname__ = "abteim" + __version__.split(".")[0]
    __appabbr__ = "abt" + __version__.split(".")[0]
    __startmode__ = "dev"
except Exception:
    __startmode__ = "systemd"
    __appname__ = "guck4"
    __appabbr__ = "g4"
    __version__ = version(__appname__)