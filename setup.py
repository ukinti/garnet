import pathlib

from setuptools import find_packages, setup

WORK_DIR = pathlib.Path(__file__).parent


with (WORK_DIR / "readme.rst").open(mode="r", encoding="utf-8") as f:
    description = f.read()


setup(
    name="garnet",
    version="0.2.1",  # major.minor.chore(fix,etc.)
    packages=find_packages(exclude=("examples.*", "static.*")),
    url="https://github.com/uwinx/garnet",
    license="MIT",
    author="Martin Winks",
    author_email="mpa@snejugal.ru",
    description="Garnet is a telethon add-on",
    long_description=description,
    classifiers=(
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ),
    install_requires=("Telethon>=1.10.8,<2.0",),
    include_package_data=False,
    keywords="asyncio add-on telethon fsm filters router contextvars telegram",
)
