from pkgutil import iter_modules

def is_module_exists(module_name):
    return module_name in (name for loader, name, ispkg in iter_modules())


print(is_module_exists("crontab"))