"""
Setup script for Privacy Policy Analyzer
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="privacy-policy-analyzer",
    version="2.0.0",
    author="Privacy Analyzer Team",
    author_email="contact@privacyanalyzer.com",
    description="A comprehensive Chrome extension and dashboard system for analyzing privacy policies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/Privacy-Policy-Analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "rag": [
            "sentence-transformers>=2.2.2",
            "faiss-cpu>=1.7.4",
            "openai>=1.3.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "privacy-analyzer=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.js", "*.css", "*.json"],
    },
)
