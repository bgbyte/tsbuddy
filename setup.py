from setuptools import setup, find_packages

setup(
   name='tsbuddy',
   version='0.0.1',
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
)
