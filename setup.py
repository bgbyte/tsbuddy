from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
   name='tsbuddy',
   version='0.0.6',
   packages=find_packages(),
   install_requires=[
       # Add dependencies here.
       # e.g. 'numpy>=1.11.1'
       'paramiko>=2.7.0',
   ],
   entry_points={
       'console_scripts': [
           'tsbuddy=src.tsbuddy:main',
           'aosdl=src.aosdl.aosdl:main',  # Run the main function in aosdl to download AOS
           'aosdl-ga=src.aosdl.aosdl:lookup_ga_build',  # Run lookup_ga_build function
       ],
   },
   long_description=long_description,
   long_description_content_type='text/markdown',
   description = "Tech Support Buddy is a versatile Python module built to empower developers and IT professionals in resolving technical issues. It provides a suite of Python functions designed to efficiently diagnose and resolve technical issues by parsing raw text into structured data, enabling automation and data-driven decision-making.",
   include_package_data=True,
)
