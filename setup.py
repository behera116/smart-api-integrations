from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-api-integrations",
    version="0.1.0",
    author="Ananda",
    author_email="behera.anand1@gmail.com",
    description="A smart way to integrate 3rd party APIs and Webhooks with minimal effort",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/behera116/smart-api-integrations",
    package_dir={"smart_api_integrations": "src"},
    packages=["smart_api_integrations"] + [f"smart_api_integrations.{pkg}" for pkg in find_packages(where="src")],
    package_data={
        "smart_api_integrations": ["py.typed", "templates/*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "django": ["django>=3.0.0"],
        "flask": ["flask>=2.0.0"],
        "fastapi": ["fastapi>=0.68.0", "uvicorn>=0.15.0"],
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "isort>=5.9.1",
            "mypy>=0.910",
        ],
    },
) 