from lxml import etree
from os import path, makedirs
from crontab import CronTab
import subprocess
from datetime import datetime


def as_config(name):
    """add ending to the name"""
    return str(name) + ".xml"


def as_name(name):
    """remove ending from the name"""
    return str(name).rstrip(".xml")


class Minute(object):
    def __init__(self):
        self.root = etree.Element("Minute")
        self.value = "0"
        self.mode = "on"

    def set(self, value=0, mode="on"):
        """set minute an hour with type checking and with "*" default value"""
        if self.is_minute(value):
            self.value = str(value)

        if mode in ("every", "on"):
            self.mode = mode
        else:
            raise ValueError("Value out of range (every, on)")

    def set_value(self, value):
        if self.is_minute(value):
            self.value = str(value)

    def set_mode(self, mode):
        if mode in ("on", "every"):
            self.mode = mode
        else:
            raise ValueError("Value out of range (every, on)")

    def get_xml(self):
        """ get lxml xml instance"""
        self.root.set("value", self.value)
        self.root.set("mode", self.mode)
        return self.root

    def read_xml(self, minute_xml):
        """read lxml xml instance"""
        value = minute_xml.get('value')
        mode = minute_xml.get('mode')
        self.set(value, mode)

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


class Hour(object):
    def __init__(self):
        self.root = etree.Element("Hour")
        self.value = "1"
        self.mode = "every"

    def set(self, value=1, mode="every"):
        """set minute an hour with type checking and with "*" default value"""
        if self.is_hour(value):
            self.value = str(value)

        if mode in ("on", "every"):
            self.mode = mode
        else:
            raise ValueError("Value out of range (every, on)")

    def set_mode(self, mode):
        if mode in ("on", "every"):
            self.mode = mode
        else:
            raise ValueError("Value out of range (every, on)")

    def set_value(self, value):
        if self.is_hour(value):
            self.value = str(value)

    def get_xml(self):
        """ get lxml xml instance"""
        self.root.set("value", self.value)
        self.root.set("mode", self.mode)
        return self.root

    def read_xml(self, hour_xml):
        """read lxml xml instance"""
        value = hour_xml.get('value')
        mode = hour_xml.get('mode')
        self.set(value, mode)

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


class Spider(object):
    """single spider configuration object"""
    def __init__(self):
        self.name = None
        self.enabled = "yes"
        self.root = etree.Element("Spider")
        self.minute = Minute()
        self.hour = Hour()

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

    def set_enabled(self, enabled):
        if enabled in ("yes", "no"):
            self.enabled = enabled
        else:
            raise ValueError("Value out of range (yes, no)")

    def get(self):
        return self

    def set_minute(self, value=None, mode=None):
        """set minute via Minute interface"""
        self.minute.set(value=value, mode=mode)

    def set_hour(self, value=None, mode=None):
        """set minute via Minute interface"""
        self.hour.set(value=value, mode=mode)

    def get_xml(self):
        """return initialized lxml xml spider configuration object"""
        self.root.set("name", self.name)
        self.root.set("enabled", self.enabled)
        # root = SubElement(self.root, self.runtime.get())
        self.root.append(self.minute.get_xml())
        self.root.append(self.hour.get_xml())
        return self.root

    def read_xml(self, spider_xml):
        """initiate objects attributes from the lxml lmx instance"""
        name = spider_xml.get('name')
        enabled = spider_xml.get('enabled')
        self.set(name, enabled)
        minute = spider_xml.xpath('Minute')[0]
        hour = spider_xml.xpath('Hour')[0]
        self.minute.read_xml(minute)
        self.hour.read_xml(hour)
        return self

    def show_xml_view(self):
        print(etree.tostring(self.root, pretty_print=True, method="xml"))


class Deployment(object):
    """config class for version and project that has been deployed"""
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.root = etree.Element("Deployment")
        self.project = None
        self.version = None
        self.deploy = None

    def set(self, project, version, deploy):
        self.project = project
        self.version = version
        self.deploy = deploy

    def set_xml(self):
        """ get lxml xml instance"""
        self.root.set("project", self.project)
        self.root.set("version", self.version)
        self.root.set("deploy", self.deploy)

    def read_xml(self, hour_xml):
        """read lxml xml instance"""
        project = hour_xml.get('project')
        version = hour_xml.get('version')
        deploy = hour_xml.get('deploy')
        self.set(project, version, deploy)

    def get_xml_view(self):
        return etree.tostring(self.root, pretty_print=True, method="xml", xml_declaration=True, encoding='UTF-8')

    def write(self):
        current_project_path = path.join(self.base_dir, as_config("deployment"))
        open(current_project_path, "w").write(self.get_xml_view())


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
    def __init__(self, project_name, config):
        self.config = config
        self.base_dir = config.get("configs_dir")
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

    def make_crontab(self, version_name):
        http_port = self.config.get("http_port")
        # independent crontab maker, reed only config files
        config = self.read_config(version_name)
        cron_tab = CronTab()
        for spider in config:
            if spider.enabled == "yes":
                command = "curl http://localhost:{0}/schedule.json -d project={1} -d spider={2}".format(
                    http_port,
                    self.project_name,
                    spider.name
                )
                # print(command)
                job = cron_tab.new(command=command)
                # check mode for minute
                if spider.minute.mode == "on":
                    job.minute.on(spider.minute.value)
                elif spider.minute.mode == "every":
                    job.minute.every(spider.minute.value)
                # check mode for hour
                if spider.hour.mode == "on":
                    job.hour.on(spider.hour.value)
                elif spider.hour.mode == "every":
                    job.hour.every(spider.hour.value)

        cron_tab_path = path.join(self.project_path, version_name)
        cron_tab.write(cron_tab_path)

    def use_crontab(self, version_name, user_name):
        """write crontab to system file"""
        exec_comand = "cd {0} && crontab {1}".format(
            self.base_dir,
            path.join(self.project_name, version_name)
        )

        subprocess.Popen(exec_comand, shell=True)

        # # write deployment XML file
        # # that save information about deployed project and its version
        current_version = version_name
        current_project = self.project_name

        da = Deployment(self.base_dir)
        da.set(current_project, current_version, str(datetime.now()))
        da.set_xml()
        da.write()


if __name__ == "__main__":
    import random

    # spiders = [Spider().set("name" + str(ind), random.choice(("yes", "no"))) for ind in xrange(10)]

    # prj = ProjectConfigController("ambiencedata_app")
    # prj.make_cron_tab("1472718795")
    # prj.use_cron_tab("1472718795", "roman")

