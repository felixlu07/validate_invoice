from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in validate_invoice/__init__.py
from validate_invoice import __version__ as version

setup(
	name="validate_invoice",
	version=version,
	description="Ensuring that new invoices are checked against the customer\'s account currencies",
	author="Felix",
	author_email="felix.lu07@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
