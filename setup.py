import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mmapf_client",
    version="0.0.2",
    author="Jonathan D�nszelmann",
    author_email="jonabent@gmail.com",
    description="client library for interaction with mapf.nl",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jonay2000/mapf_client",
    project_urls={
        "Bug Tracker": "https://github.com/jonay2000/mapf_client/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
