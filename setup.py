from setuptools import setup, find_packages

with open("README.md") as fp:
    long_description = fp.read()

setup(
    name="aiosteam_api",
    version="1.1.6",
    description="Async Python Client wrapper for Steam API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "async steam",
        "steam api",
        "async steam community",
        "api",
        "async"
    ],
    author="Yevhenii Havrus",
    author_email="jeygavrus@gmail.com",
    url="https://github.com/jgavrus/aiosteam-api",
    packages=find_packages(),
    install_requires=["beautifulsoup4", "aiohttp", "pydantic"],
    license="MIT",
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
    ],
)
