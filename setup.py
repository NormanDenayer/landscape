#pylint: skip-file

from setuptools import setup
import landscape

with open('requirements.txt', 'r') as reqs:
    requirements = reqs.read().split('\n')

setup(name='landscape',
      author='Norman Denayer',
      author_email="denayer.norman@gmail.com",
      description='My main landing page.',
      long_description=landscape.__doc__,
      version=landscape.__version__,
      url='http://github.com/NormanDenayer/landscape',
      license='PSF',
      keywords='',
      packages=['landscape', 'test'],
      test_suite="test",
      test_loader="unittest:TestLoader",
      entry_points={
          'console_scripts': [
          ],
      },
      install_requires = requirements,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: Python Software Foundation License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries :: Python Modules']
     )
