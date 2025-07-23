from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
   name='tsbuddy',
   version='0.0.12',
   packages=find_packages(),
   install_requires=[
       # Add dependencies here.
       # e.g. 'numpy>=1.11.1'
       'paramiko>=2.7.0',
   ],
   entry_points={
       'console_scripts': [
           'tsbuddy-csv=src.tsbuddy:main',
           'tsbuddy-extract=src.extracttar:main',  # Run the main function in extracttar to extract tar files
           'aosdl=src.aosdl.aosdl:main',  # Run the main function in aosdl to download AOS
           'aosdl-ga=src.aosdl.aosdl:lookup_ga_build',  # Run lookup_ga_build function
           'aosdl-up=src.aosdl.aosdl:aosup',  # Run AOS Upgrade function to prompt for directory name and reload option
           'tsbuddy=src.tsbuddy_menu:menu',  # New menu entry point
           'logparser=src.logparser:main', # Run function to consolidate logs in current directory
       ],
   },
   long_description=long_description,
   long_description_content_type='text/markdown',
   description = "Tech Support Buddy is a versatile Python module built to empower developers and IT professionals in resolving technical issues. It provides a suite of Python functions designed to efficiently diagnose and resolve technical issues by parsing raw text into structured data, enabling automation and data-driven decision-making.",
   include_package_data=True,
)
