import setuptools

def main() -> None:
    setuptools.setup(
        name="chimera-core",
        description="wait to be fill",
        packages=['chimera_core'],
        install_requires=["xoa_driver>=1.0.12", "pydantic", "loguru"],
    )

if __name__ == '__main__':
    main()