from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
   name='tsbuddy',
   version='0.0.4',
   packages=find_packages(),
   install_requires=[
       # Add dependencies here.
       # e.g. 'numpy>=1.11.1'
   ],
   entry_points={
       'console_scripts': [
           'tsbuddy=tsbuddy.tsbuddy:main',
       ],
   },
   long_description=long_description,
   long_description_content_type='text/markdown',
   description = "Tech Support Buddy is a versatile Python module built to empower developers and IT professionals in resolving technical issues. It provides a suite of Python functions designed to efficiently diagnose and resolve technical issues by parsing raw text into structured data, enabling automation and data-driven decision-making."
)
