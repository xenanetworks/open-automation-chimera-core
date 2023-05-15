import setuptools

def main() -> None:
    setuptools.setup(
        name="chimera-core",
        description="wait to be fill",
        packages=setuptools.find_packages(),
        install_requires=["xoa_driver>=1.0.12", "pydatic", "loguru"],
    )