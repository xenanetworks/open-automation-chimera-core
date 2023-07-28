import setuptools


def main() -> None:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

    setuptools.setup(
        name="chimera-core",
        description="Xena OpenAutomation - Chimera Core, for network impairment test configuration, integration, and development.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Frank Chen, Leonard Yu",
        author_email="fch@xenanetworks.com, hyu@xenanewtorks.com",
        maintainer="Xena Networks",
        maintainer_email="support@xenanetworks.com",
        url="https://github.com/xenanetworks/chimera-core",
        license='Apache 2.0',
        install_requires=["xoa_driver>=2.1.0", "pydantic", "loguru"],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries :: Application Frameworks",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
        ],
        python_requires=">=3.8.9",
    )


if __name__ == '__main__':
    main()
