import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="envoy_reader",
    version="0.8.3",
    author="Jesse Rizzo",
    author_email="jesse.rizzo@gmail.com",
    description="A program to read from an Enphase Envoy on the local network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jesserizzo/envoy_reader",
    packages=setuptools.find_packages(),
    install_requires=[
        "asyncio == 3.4.3",
        "requests == 2.22.0",
        "requests_async == 0.6.2"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
