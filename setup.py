from setuptools import setup, find_packages

setup(
    name='pymogilefs',
    version='0.1.0',
    description='pymogilefs',
    long_description='Python MogileFS Client',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    author='bwind',
    author_email='mailtobwind@gmail.com',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['requests==2.12.3'],
    test_suite='tests',
    include_package_data=True,
    zip_safe=False
)
