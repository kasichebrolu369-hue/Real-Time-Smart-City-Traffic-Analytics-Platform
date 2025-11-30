"""
Setup script for the Traffic Analytics Platform
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="traffic-analytics-lambda",
    version="1.0.0",
    author="Kasi Chebrolu",
    author_email="kasichebrolu369@gmail.com.com",
    description="Real-Time Smart City Traffic Analytics Platform using Lambda Architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kasichebrolu/lambda-traffic-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "traffic-generate=scripts.generate_historical_data:main",
            "traffic-api=serving_layer.api.app:main",
        ],
    },
)
