from setuptools import setup, find_packages
from setuptools.command.install import install


setup(
    name="laserharp",
    version="0.1.0",
    author="Amon Benson",
    description="Laserharp Python Backend",
    license="MIT",
    keywords="laser harp music midi midi-controller",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.yaml"],
    },
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "mido",
        "python-rtmidi",
        "pyserial",
        "pyyaml",
        "numpy",
        "appdirs",
        "perci",
        "flask",
        "flask-cors",
        "flask-socketio",
    ],
    python_requires=">=3.9",
)
