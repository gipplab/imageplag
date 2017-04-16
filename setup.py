from setuptools import setup


setup(name='image_plag_api',
      version='0.1',
      packages=['API',
                'image_plag/pytesser',
                'image_plag/DNN_pure_no_pure',
                'image_plag/DNN_bar_no_bar'],
      entry_points={
          'console_scripts': [
              'image_plag = image_plag.__main__:main'
          ]
      },
      package_data={
          '' : ['*.txt'],
          'image_plag/img' : ['*'],
          'image_plag/DNN_pure_no_pure' : ['*'],
          'image_plag/DNN_bar_no_bar' : ['*'],
      }, install_requires=['colorama',
                           'glob2',
                           'Image',
                           'pandas',
                           'numpy',
                           'matplotlib',
                           'scipy',
                           'tqdm']
      )
