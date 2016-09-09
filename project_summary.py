# coding: utf-8
from pkg_resources import find_distributions
from zipfile2 import ZipFile
from os import path
from re import findall
from .configstorage import ProjectConfigController, Spider


class ProjectSummary(object):
    def __init__(self,base_dir, project_name):
        self.project_path = path.join(base_dir, project_name)
        self.project_config = ProjectConfigController(project_name)
        self.project_eggs = self.get_project_eggs()


    @staticmethod
    def as_egg(string):
        return string + '.egg'

    def get_project_eggs(self):
        """search eggs in particular path"""
        dist = find_distributions(self.project_path)
        eggs = [egg.key for egg in dist]
        return sorted(eggs, reverse=True)

    def get_egg_changing_date(self, egg_name):
        egg_path = path.join(self.project_path, self.as_egg(egg_name))
        egg = ZipFile(egg_path, 'r')

        max_date_time = max([el.date_time for el in egg.infolist()])
        return max_date_time

    def get_spiders_list(self, egg_name):
        egg_path = path.join(self.project_path, self.as_egg(egg_name))
        egg = ZipFile(egg_path, 'r')
        regex = '.*spiders/(.+)\.py$'

        def get_correct_names():
            for file_name in egg.namelist():
                if findall(regex, file_name) and '__init__' not in file_name:
                    yield findall(regex, file_name)[0]

        spiders_name_list = list(get_correct_names())

        # make config files
        if not self.project_config.isexist(egg_name):
            spiders_list = [Spider().set(spider_name) for spider_name in spiders_name_list]
            self.project_config.write_config(egg_name, spiders_list)

        spiders_config_objects = self.project_config.read_config(egg_name)

        return spiders_config_objects, len(spiders_config_objects)

    def summary(self):
        for num, egg in enumerate(self.project_eggs):
            spiders = self.get_spiders_list(egg)
            summary = {
                'egg_num': num + 1,
                'egg_name': egg,
                'updated_at': self.get_egg_changing_date(egg),
                'spiders': spiders[0],
                'spiders_count': spiders[1]
            }
            # make egg buttons enable if egg is the most new inside project
            # for bootstrap
            if egg == self.project_eggs[0]:
                summary['mode'] = None
                summary['style'] = 'info'
            else:
                summary['mode'] = 'disabled'
                summary['style'] = 'warning'

            yield summary



if __name__ == "__main__":
    eggs_base_dir = '/home/roman/PycharmProjects/scrapyd_fork/scrapyd/scrapyd/scripts/eggs/ambiencedata_app'
    #
    st = ProjectSummary(eggs_base_dir).summary()
    print(list(st))

