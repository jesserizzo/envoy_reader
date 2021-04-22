import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setup_requirements = [
    "pytest-runner>=5.2",
]

test_requirements = [
    "pytest-asyncio",
    "black>=19.10b0",
    "codecov>=2.1.4",
    "flake8>=3.8.3",
    "flake8-debugger>=3.2.1",
    "pytest>=5.4.3",
    "pytest-cov>=2.9.0",
    "pytest-raises>=0.11",
    "respx>=0.16.3",
]

dev_requirements = [
    *setup_requirements,
    *test_requirements,
    "bump2version>=1.0.1",
    "coverage>=5.1",
    "ipython>=7.15.0",
    "m2r2>=0.2.7",
    "pytest-runner>=5.2",
    "Sphinx>=3.4.3",
    "sphinx_rtd_theme>=0.5.1",
    "tox>=3.15.2",
    "twine>=3.1.1",
    "wheel>=0.34.2",
]

requirements = ["httpx>=0.12.1"]

extra_requirements = {
    "setup": setup_requirements,
    "test": test_requirements,
    "dev": dev_requirements,
    "all": [
        *requirements,
        *dev_requirements,
    ],
}


setuptools.setup(
    name="envoy_reader",
    version="0.18.5",
    author="Jesse Rizzo",
    author_email="jesse.rizzo@gmail.com",
    description="A program to read from an Enphase Envoy on the local network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jesserizzo/envoy_reader",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
