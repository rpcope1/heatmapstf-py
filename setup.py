__author__ = 'Robert P. Cope'
__author_email__ = 'rpcope1@gmail.com'
__version__ = '0.1.1'
__license__ = 'LGPL'

from setuptools import setup

setup(name="heatmapstf",
      keywords="team fortress steam heatmapstf",
      description="A Python wrapper on the heatmaps.tk API for mapping TF2 in game statistics",
      author=__author__,
      author_email=__author_email__,
      version=__version__,
      license=__license__,
      packages=['heatmapstf'],
      install_requires=['requests >= 2.0.0'])
