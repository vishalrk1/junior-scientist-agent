from setuptools import setup, find_packages

setup(
    name="databuddy",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "databuddy = databuddy.cli:cli",
        ],
    },
    include_package_data=True,
    author="Vishal Karangale",
    description="AI powered Junior data scientist",
)