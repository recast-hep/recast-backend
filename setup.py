from setuptools import setup,find_packages

setup(
  name = 'recast-backend',
  version = '0.0.1',
  packages = find_packages(),
  entry_points={
        'console_scripts': [
           'recast-prodsub   = recastbackend.submitcli:submit',
           'recast-localsub  = recastbackend.fromenvsubmit:submit',
           'recast-listen    = recastbackend.listener:listen',
           'recast-track     = recastbackend.tracker:track',

         ]
      },
  include_package_data = True,
  install_requires = [
    'fabric',
    'Celery',
    'Click',
    'redis',
    'recast-api',
    'socket.io-emitter',
    'requests',
  ],
  dependency_links = [
    'https://github.com/ziyasal/socket.io-python-emitter/tarball/master#egg=socket.io-emitter-0.1.3',
    'https://github.com/recast-hep/recast-api/tarball/master#egg=recast-api-0.0.1'
  ]
)
