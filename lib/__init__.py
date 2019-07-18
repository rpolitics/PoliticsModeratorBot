import pkgutil
import pendulum

ts = pendulum.now().to_datetime_string()

__path__ = pkgutil.extend_path(__path__, __name__)
for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
	__import__(modname)
	print("{} [INFO] {} imported.".format(ts, modname))
