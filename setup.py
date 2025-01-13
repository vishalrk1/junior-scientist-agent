from setuptools import setup, find_packages

setup(
    name="buddy",  # Changed from databuddy
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
        "questionary",
        "PyYAML",
    ],
    entry_points={
        "console_scripts": [
            "buddy=buddy.cli:main",  # Changed from databuddy.cli:cli to buddy.cli:main
        ],
    },
    include_package_data=True,
    author="Vishal Karangale",
    description="AI powered Junior data scientist",
)