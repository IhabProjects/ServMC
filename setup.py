#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="servmc",
    version="0.1.0",
    description="Self-Hosted Minecraft Server Manager",
    author="ServMC Team",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.5",
        "requests>=2.28.2",
        "pillow>=9.5.0",
        "ttkthemes>=3.2.2",
        "mcstatus>=10.0.3"
    ],
    entry_points={
        "console_scripts": [
            "servmc=servmc.servmc:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Tk",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Games/Entertainment",
    ],
) 