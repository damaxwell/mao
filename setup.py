
from setuptools import find_packages, setup

setup(
    name="Math Assessment Oracle",
    version="9.0.1",
    author="David Maxwell",
    author_email="damaxwell@alaska.edu",
    packages=["mao"],
    test_suite="tests",
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
    ],
)