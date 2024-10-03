from setuptools import setup

setup(
    name="laserharp",
    version="0.1.0",
    author="Amon Benson",
    description="Laserharp Python Backend",
    license="MIT",
    keywords="laser harp music midi midi-controller",
    packages=["laserharp"],
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "mido",
        "python-rtmidi",
        "pyserial",
        "pyyaml",
        "numpy",
        "cv2",
        "flask",
        "flask-cors",
        "flask-socketio",
    ],
    python_requires=">=3.9",
)
