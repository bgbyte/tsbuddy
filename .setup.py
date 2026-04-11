from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
   name='tsbuddy',
   version='0.0.39',
   packages=find_packages(where='src'),
   package_dir={'': 'src'},
   install_requires=[
       # Add dependencies here.
       # e.g. 'numpy>=1.11.1'
       'paramiko>=2.7.0',
       'xlsxwriter>=3.2.5',
       'scapy>=2.6.1',
       'pandas>=2.3.1',
       #'argparse>=1.4.0',
       #'prompt_toolkit>=3.0.0',
       #'openai>=0.27.0',
       #'google-genai>=1.45.0',
   ],
   entry_points={
       'console_scripts': [
           'tslog2csv=tsbuddy.tslog2csv.tslog2csv:main',  # Run the main function in tsbuddy to convert tech_support.log to CSV
           'ts-extract=tsbuddy.extracttar.extract_ts_tar:main',  # Run the main function in extract_all to extract tar files
           'ts-extract-legacy=tsbuddy.extracttar.legacy.extracttar_7zip:main',  # Run the main function in extracttar to extract tar files
           'aosdl=tsbuddy.aos.aosdl:main',  # Run the main function in aosdl to download AOS
           'aosga=tsbuddy.aos.aosdl:lookup_ga_build',  # Run lookup_ga_build function
           'aosup=tsbuddy.aos.aosdl:aosup',  # Run AOS Upgrade function to prompt for directory name and reload option
           'tsbuddy=tsbuddy.tsbuddy_menu:menu',  # New menu entry point
           'ts-log=tsbuddy.log_analyzer.logparser_v2:main', # Run function to consolidate logs in current directory
           'ts-get=tsbuddy.log_analyzer.get_techsupport:main',  # Run the main function in get_techsupport to gather tech support data
           'ts-clean=utils.clean_pycache:clean_pycache_and_pyc',  # Run the clean function to remove __pycache__ directories and .pyc files
           'ts-graph-cpu=tsbuddy.hmon.graph_cpu:main',  # Entry point for HMON Graph Generator
           'ts-chat=tsbuddy.ts_chat.main_api_caller:main',  # Entry point for the chat interface
       ],
   },
   long_description=long_description,
   long_description_content_type='text/markdown',
   description = "Tech Support Buddy is a versatile Python module built to empower developers and IT professionals in resolving technical issues. It provides a suite of Python functions designed to efficiently diagnose and resolve technical issues by parsing raw text into structured data, enabling automation and data-driven decision-making.",
   include_package_data=True,
   exclude_package_data={"": [".env", ".tsbuddy_secrets", ".tsbuddy_settings"]},
)
