from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
   name='tsbuddy',
   version='0.0.3',
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
)
