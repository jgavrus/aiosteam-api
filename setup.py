from setuptools import setup, find_packages

with open("README.md") as fp:
    long_description = fp.read()

setup(
    name="async-python-steam-api",
    version="1.0.0",
    description="Async Python Client wrapper for Steam API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "steam",
        "steamapi",
        "steam community",
        "api",
    ],
    author="David Salazar",
    author_email="david.asal@hotmail.com",
    url="https://github.com/deivit24/steam-python-sdk",
    packages=find_packages(),
    install_requires=["beautifulsoup4", "aiohttp"],
    license="MIT",
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
    ],
)
