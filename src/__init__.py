import configparser
from configparser import ExtendedInterpolation

config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
config.read('/app/config/config.ini')