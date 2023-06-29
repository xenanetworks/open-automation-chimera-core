from setuptools import setup


def main() -> None:
    setup(
        version="0.0.1",
        name="chimera-core",
        description="wait to be fill",
        install_requires=["xoa_driver>=1.0.12", "pydantic", "loguru"],
    )

if __name__ == '__main__':
    main()