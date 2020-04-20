"""A Tensorflow basic function

See:
https://github.com/tygerlord/tftools
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tftools',  
    version='0.0.0', 
    description='Basic tools for tensorflow ml',
    long_description=long_description, 
    long_description_content_type='text/markdown',
    url='https://github.com/tygerlord/tftools',
    author='fleblanc50', 
    author_email='fleblanc50@gmail.com',
    classifiers=[  
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='machine learning tensorflow tools', 
    package_dir={'': 'src'}, 
    packages=['tftools'],
    python_requires='>=3.5',
    install_requires=['tensorflow', 'matplotlib', 'tqdm', 'opencv-python'],
    project_urls={  # Optional
        'Source': 'https://github.com/tygerlord/tftools/',
    },
)
