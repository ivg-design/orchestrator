"""Setup script for meta-orchestration system."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="meta-orchestrator",
    version="0.1.0",
    description="Meta-orchestration system for coordinating multiple AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Meta-Orchestration Team",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.6",
    ],
    entry_points={
        "console_scripts": [
            "orchestrate=orchestrator.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
