from setuptools import setup, find_packages

setup(
    name="your_project_name",
    version="0.1.0",
    description="Tvz enhancer",
    author="Filip Kuser",
    author_email="filipkuser2003@gmail.com",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "pytest",
        "flake8",
        "pylint",
        "black"
    ],
    python_requires='>=3.6',
)