#!/usr/bin/env python3
"""
Setup script for Consul-Vault Integration
"""
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="consul-vault-integration",
    version="1.0.0",
    author="Jessica Ahm",
    description="Integration layer between HashiCorp Consul and Vault",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jessicaahm/consul",
    py_modules=[
        "config_loader",
        "vault_client",
        "consul_client",
        "integration",
        "example",
        "cli"
    ],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "consul-vault=cli:main",
        ],
    },
)
