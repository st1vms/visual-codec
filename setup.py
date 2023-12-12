"""setup.py"""
from os.path import dirname, join, abspath
from setuptools import setup, find_packages

__DESCRIPTION = """Data-to-visuals encryption codec"""

__PROJECT_NAME = "visual_codec"

with open(
    join(abspath(dirname(__file__)), "README.md"),
    "r",
    encoding="utf-8",
    errors="ignore",
) as fp:
    __LONG_DESCRIPTION = fp.read().lstrip().rstrip()

setup(
    name=__PROJECT_NAME,
    version="0.1.0",
    author="st1vms",
    author_email="stefano.maria.salvatore@gmail.com",
    description=__DESCRIPTION,
    long_description=__LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/st1vms/visual-codec",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            # vcc console script
            "vcc=visual_codec.cli.vcc:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GPL-3.0-only",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=["colorlog"],
)
