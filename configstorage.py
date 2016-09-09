from lxml import etree
from os import path, makedirs


def as_config(name):
    """add ending to the name"""
    return str(name) + ".xml"


def as_name(name):
    """remove ending from the name"""
    return str(name).rstrip(".xml")


class Runtime(object):
    def __init__(self):
        self.root = etree.Element("Runtime")
        self.minute = "*"
        self.hour = "*"
        self.mode = "each"

    def set(self, minute="*", hour="*"):
        """set minute an hour with type checking and with "*" default value"""
        if self.is_minute(minute):
            self.minute = str(minute)

        if self.is_hour(hour):
            self.hour = str(hour)

    def set_mode(self, mode):
        """set mode that shows wether it time of repeating(at) or interval of repeating(each)"""
        if mode in ("each", "at"):
            self.mode = mode
        else:
            raise ValueError("Value out of range (each, at)")

    def get_xml(self):
        """ get lxml xml instance"""
        self.root.set("minute", self.minute)
        self.root.set("hour", self.hour)
        self.root.set("mode", self.mode)
        return self.root

    def read_xml(self, runtime_xml):
        """read lxml xml instance"""
        minute = runtime_xml.get('minute')
        hour = runtime_xml.get('hour')
        mode = runtime_xml.get('mode')
        self.set(minute, hour)
        self.set_mode(mode)

    @staticmethod
    def is_minute(minute):
        if minute == "*":
            return True
        else:
            minute = int(minute)
            if isinstance(minute, int):
                if 0 <= minute <= 59:
                    return True
                else:
                    raise ValueError("Value out of range 0-59")
            else:
                raise TypeError("Must be integer!")

    @staticmethod
    def is_hour(hour):
        if hour == "*":
            return True
        else:
            hour = int(hour)
            if isinstance(hour, int):
                if 0 <= hour <= 23:
                    return True
                else:
                    raise ValueError("Value out of range 0-23")
            else:
                raise TypeError("Must be integer!")

    def show_xml_view(self):
        print(etree.tostring(self.root, pretty_print=True, method="xml"))


class Spider(object):
    """single spider configuration object"""
    def __init__(self):
        self.name = None
        self.enabled = "yes"
        self.root = etree.Element("Spider")
        self.runtime = Runtime()

    def set(self, name, enabled="yes"):
        """
        set name and enabled status where "yes" means must be run and
        "no" means must  be ignore
        """
        self.name = name
        if enabled in ("yes", "no"):
            self.enabled = enabled
        else:
            raise ValueError("Value out of range (yes, no)")

        return self

    def set_runtime(self, minute=None, hour=None):
        """set runtime via Runtime interface"""
        self.runtime.set(minute=minute, hour=hour)

    def set_runtime_mode(self, mode):
        """set runtime mode via Runtime interface"""
        self.runtime.set_mode(mode)

    def get_xml(self):
        """return initialized lxml xml spider configuration object"""
        self.root.set("name", self.name)
        self.root.set("enabled", self.enabled)
        # root = SubElement(self.root, self.runtime.get())
        self.root.append(self.runtime.get_xml())
        return self.root

    def read_xml(self, spider_xml):
        """initiate objects attributes from the lxml lmx instance"""
        name = spider_xml.get('name')
        enabled = spider_xml.get('enabled')
        self.set(name, enabled)
        runtime = spider_xml.xpath('Runtime')[0]
        self.runtime.read_xml(runtime)
        return self

    def show_xml_view(self):
        print(etree.tostring(self.root, pretty_print=True, method="xml"))


class SpiderConfigParser(object):
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.root = etree.Element("Spiders")
        self.spiders = None

    def get(self):
        return self.spiders

    def read(self, name):
        name = as_config(name)
        file_path = path.join(self.project_dir, name)
        xml = etree.parse(file_path)
        self.spiders = [Spider().read_xml(spider_inst) for spider_inst in xml.findall('Spider')]
        return self.get()

    def write(self, name, spiders_list):
        name = as_config(name)
        for spider in spiders_list:
            self.root.append(spider.get_xml())

        file_path = path.join(self.project_dir, name)

        open(file_path, 'w').write(self.get_xml_view())

    def get_enabled(self):
        for spider in self.spiders:
            if spider.enabled == "yes":
                print(spider.name)

    def get_xml_view(self):
        return etree.tostring(self.root, pretty_print=True, method="xml", xml_declaration=True, encoding='UTF-8')

    def show_xml_view(self):
        print(self.get_xml_view())


class ProjectConfigController(object):
    """
    generate and manipulate cron tabs regarding spiders configurations,
    manipulate projects directories and config files(make, remove, rewrite etc)
    """
    def __init__(self, project_name):
        self.base_dir = "configs"
        self.project_name = project_name
        self.project_path = path.join(self.base_dir, self.project_name)

    def __create_project(self):
        if not path.exists(self.project_path):
            makedirs(self.project_path)

    def del_project(self):
        # TODO
        pass

    def del_config(self):
        # TODO
        pass

    def write_config(self, version_name, spiders_list):
        self.__create_project()
        SpiderConfigParser(self.project_path).write(version_name, spiders_list)

    def read_config(self, version_name):
        return SpiderConfigParser(self.project_path).read(version_name)

    def isexist(self, version_name):
        version_path = path.join(self.project_path, as_config(version_name))
        if path.exists(version_path):
            return True
        else:
            return False

    def make_cron_tab(self):
        # TODO
        pass


if __name__ == "__main__":
    import random

    spiders = [Spider().set("name" + str(ind), random.choice(("yes", "no"))) for ind in xrange(10)]
    # sc = SpiderConfigParser("./")

    # sc.read("test")
    # sc.get_enabled()
    # print(sc.get())

    # sc.write("ttt", spiders_list)
    # sc2 = SpiderConfigParser("./")
    # sc2.read("ttt")
    # sc2.get_enabled()

    print(ProjectConfigController("amb_app").isexist("test"))
    # print(prj.isexist("test"))
    # print(prj.read_config("test"))isexist("test")
    # prj.write_config("ttt1", spiders)
