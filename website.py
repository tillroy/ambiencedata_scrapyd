from datetime import datetime

import socket

from twisted.web import resource, static
from twisted.web.resource import NoResource, Resource
from twisted.application.service import IServiceCollection

from scrapy.utils.misc import load_object

from .interfaces import IPoller, IEggStorage, ISpiderScheduler

from urlparse import urlparse

# INFO updated
from jinja2 import Environment, FileSystemLoader
import cgi
from os import path, remove, makedirs

from re import findall
import shutil
from cStringIO import StringIO
from .project_summary import ProjectSummary
import uuid
from .configstorage import ProjectConfigController, Spider


class Root(Resource):
    def __init__(self, config, app):
        Resource.__init__(self)
        self.config = config
        self.debug = config.getboolean('debug', False)
        self.runner = config.get('runner')
        logsdir = config.get('logs_dir')
        itemsdir = config.get('items_dir')

        local_items = itemsdir and (urlparse(itemsdir).scheme.lower() in ['', 'file'])
        self.app = app
        self.nodename = config.get('node_name', socket.gethostname())

        self.__connect_static_files()

        self.env = Environment(loader=FileSystemLoader(path.join(path.dirname(__file__), "templates")))

        self.summary = self.get_main_summary()

        # add additional directories
        if logsdir:
            self.putChild('logs', static.File(logsdir, 'text/plain'))
        if local_items:
            self.putChild('items', static.File(itemsdir, 'text/plain'))

        # add webservices API
        services = config.items('services', ())
        for servName, servClsName in services:
            servCls = load_object(servClsName)
            self.putChild(servName, servCls(self))

        self.update_projects()

    def __connect_static_files(self):
        srtatic_dir = path.join(path.dirname(__file__), "static")
        gui_files = (
            "bootstrap.min.css",
            "bootstrap-theme.min.css",
            "bootstrap-switch.css",
            "ie10-viewport-bug-workaround.css",
            "starter-template.css",
            "bootstrap-toggle.min.css",
            "bootstrap-select.min.css",
            "theme.css",
            "styles.css",
            "jquery.min.js",
            "bootstrap.min.js",
            "ie10-viewport-bug-workaround.js",
            "ie-emulation-modes-warning.js",
            "bootstrap-filestyle.min.js",
            "bootstrap-checkbox.min.js",
            "bootstrap-switch.min.js",
            "bootstrap-toggle.min.js",
            "bootstrap-select.min.js",
            "modal_windows.js",
            "logo.png",
        )

        for g_file in gui_files:
            self.putChild(g_file, static.File(path.join(srtatic_dir, g_file)))

    def get_main_info(self):
        """make statistics of projects, versions and spiders"""
        projects = self.scheduler.list_projects()
        versions_count = [len(self.eggstorage.list(x)) for x in projects]
        versions = [self.eggstorage.list(x) for  x in projects]
        main_info = zip(projects, versions_count, versions)
        return main_info

    def get_main_summary(self):
        base_dir = self.eggstorage.basedir
        projects = self.scheduler.list_projects()
        for project_name in projects:
            summary = {
                'project_name': project_name,
                'project_summary': list(ProjectSummary(project_name, self.config).summary()),
                'eggs_count': len(list(ProjectSummary(project_name, self.config).summary()))
            }
            yield summary

    def getChild(self, path, request):
        """switch between pages"""
        if path == "home" or path == "":
            return self
        elif path in self.scheduler.list_projects():
            return Project(self, path)
        elif path == "jobs":
            return Jobs(self, path)
        else:
            return NoResource()

    def render_GET(self, request):
        template_dir = path.join(path.dirname(__file__), "templates")
        request.args = dict()
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('projects_list.html')

        msg = dir(self.runner)

        return template.render(projects_list=list(enumerate(self.get_main_info()))).encode('utf-8')

    def render_POST(self, request):
        del_project = request.args.get("del_project")
        if del_project:
            project_name = request.args.get("del_project")
            if project_name:
                folder_path = path.join(self.eggstorage.basedir, request.args["del_project"][0])
                if path.exists(folder_path):
                    shutil.rmtree(folder_path)
                    self.scheduler.update_projects()
                    request.redirect('/')
                    return ""

        add_project = request.args.get("add_project")
        if add_project:
            project_name = request.args.get("project_name")
            if project_name:
                folder_path = path.join(self.eggstorage.basedir, request.args["project_name"][0])
                if not path.exists(folder_path):
                    makedirs(folder_path)
                    # print(request.args)
                    self.scheduler.update_projects()
                    request.redirect('/')
                    return ""

        print(request.args)

    def update_projects(self):
        self.poller.update_projects()
        self.scheduler.update_projects()

    @property
    def launcher(self):
        app = IServiceCollection(self.app, self.app)
        return app.getServiceNamed('launcher')

    @property
    def scheduler(self):
        return self.app.getComponent(ISpiderScheduler)

    @property
    def eggstorage(self):
        return self.app.getComponent(IEggStorage)

    @property
    def poller(self):
        return self.app.getComponent(IPoller)


class HomePage(Resource):

    def __init__(self, root, local_items):
        Resource.__init__(self)
        self.root = root
        self.local_items = local_items

    def __get_main_info(self):
        projects = self.root.scheduler.list_projects()
        versions_count = [len(self.root.eggstorage.list(x)) for x in projects]
        versions = [self.root.eggstorage.list(x) for x in projects]
        main_info = zip(projects, versions_count, versions)
        return main_info

    def render_GET(self, request):
        template_dir = path.join(path.dirname(__file__), "templates")
        request.args = dict()
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('projects_list.html')
        # convert from dict to list for Jinja2 tamplate
        projects = self.root.scheduler.list_projects()
        versions_count = [len(self.root.eggstorage.list(x)) for x in projects]
        versions = [self.root.eggstorage.list(x) for x in projects]
        proj_ver = zip(projects, versions_count, versions)
        # msg = self.root.eggstorage._eggpath("test","vt1")
        res = self.root.eggstorage.list("amb_app")
        msg = (dir(res), type(res), res)
        # msg = msg
        # msg = ""

        return template.render(eggs_list=res, projects_list=proj_ver, msg=msg).encode('utf-8')

    def add_egg(self, req):
        form = cgi.FieldStorage(
            fp=req.content,
            headers=req.getAllHeaders(),
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': req.getAllHeaders()['content-type'],
                     }
        )

        file_name = form["filename"].filename

        out = open(self.dirs["eggs_dir"] + "/" + file_name, "wb")
        out.write(form["filename"].value)
        out.close()

    @staticmethod
    def parse_del_name(del_name):
        """have to return int NOT string"""
        regex = "name_del(\d+)$"
        res = findall(regex, del_name)
        return int(res)

    def render_POST(self, request):
        # name of the submit button
        add_egg = request.args.get("load_egg")
        del_egg = request.args.get("del_egg")
        update_projects = request.args.get("update_projects")

        if update_projects:

            # self.root.update_projects()
            self.root.scheduler.update_projects()
            print("update", request.args)
            request.redirect('#')
            return ""


        add_project = request.args.get("add_project")
        if add_project:
            project_name = request.args.get("project_name")
            if project_name:
                folder_path = os.path.join(self.root.eggstorage.basedir, request.args["project_name"][0])
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    # print(request.args)
                    self.root.scheduler.update_projects()
                    request.redirect('#')
                    return ""

        del_project = request.args.get("del_project")
        if del_project:
            print(request.args)
            project_name = request.args.get("del_project")
            if project_name:
                folder_path = os.path.join(self.root.eggstorage.basedir, request.args["del_project"][0])
                if os.path.exists(folder_path):
                    pass
                    shutil.rmtree(folder_path)
                    self.root.scheduler.update_projects()
                    request.redirect('#')
                    return ""

        if add_egg:
            # form = cgi.FieldStorage(
            #     fp=request.content,
            #     headers=request.getAllHeaders(),
            #     environ={'REQUEST_METHOD': 'POST',
            #              'CONTENT_TYPE': request.getAllHeaders()['content-type'],
            #              }
            # )
            #
            #
            # file_name = form["filename"].filename
            #
            # out = open(self.dirs["eggs_dir"] + "/" + file_name, "wb")
            # out.write(form["filename"].value)
            # out.close()
            # print(request.args)
            print("add", request.args)
            self.add_egg(request)
            request.redirect('#')
            return ""
        elif del_egg:
            print("dell", request.args)
            eggs_dir = self.dirs["eggs_dir"]
            egg_id = int(del_egg[0])
            eggs = self.get_eggs_dict()
            egg_name = eggs[egg_id][0]
            # print(os.path.join(eggs_dir, egg_name))
            os.remove(os.path.join(eggs_dir, egg_name))
            # print("dasdasd", egg)
            request.redirect('#')
            return ""
        else:
            print("smth else", request.args)
            request.redirect('#')
            return ""


class Project(Resource):
    def __init__(self, root, path):
        Resource.__init__(self)
        self.root = root
        self.path = path
        self.root_info = self.root.get_main_info()
        self.main_summary = self.root.get_main_summary()
        self.project_summary = self.get_project_summary()

    def get_page_data(self):
        """get data only for particular project"""
        for item in self.root_info:
            if item[0] == self.path:
                return item

    def get_project_summary(self):
        """get data only for particular project"""
        for item in self.main_summary:
            if item['project_name'] == self.path:
                return item

    def get_version_summary(self, version_name):
        summary = self.project_summary
        project_summary = summary.get("project_summary")
        for version in project_summary:
            if version.get("egg_name") == version_name:
                return version

    def get_status(self):
        pending = sum(q.count() for q in self.root.poller.queues.values())
        running = len(self.root.launcher.processes)
        finished = len(self.root.launcher.finished)
        res = {
            'pending': pending,
            'running': running,
            'finished': finished
        }
        return res

    def render_GET2(self, request):
        # FIXME to summary dict
        projects_list = list(enumerate(self.root_info))
        page = self.get_project_summary()

        the_newest_prj = self.root.eggstorage.list(self.path)

        project_config = self.root.configstorage.get(self.path)
        print(project_config)

        template = self.root.env.get_template('project.html')
        return template.render(
            project_name=page['project_name'],
            # versions_list=versions_list,
            versions_list=page['project_summary'],
            projects_list=projects_list,
            # msg=str(self.get_status()) + str(sorted(the_newest_prj)[-1])
            msg=self.root.configstorage.get(page.get("project_name"))
        ).encode('utf-8')

    def render_GET(self, request):
        # FIXME to summary dict
        projects_list = list(enumerate(self.root_info))
        page = self.project_summary

        template = self.root.env.get_template('project.html')
        return template.render(
            project_name=page.get("project_name"),
            projects_list=projects_list,
            versions_list=page.get("project_summary"),
            msg=str(self.get_status())
        ).encode('utf-8')

    def save_config(self, req):
        save_config = req.args.get("save_config")
        if save_config:
            version_name = save_config[0]
            version_summary = self.get_version_summary(version_name)

            spiders_all = version_summary.get("spiders")
            spiders_enabled = req.args.get("spider_enabled")
            updated_spiders_list1 = list()

            # update enable mode
            for spider in spiders_all:
                if spiders_enabled is None:
                    spider.set_enabled("no")
                    updated_spiders_list1.append(spider)

                else:
                    if spider.name in spiders_enabled:
                        spider.set_enabled("yes")
                        # print(
                        #     """
                        #     {0},
                        #     {1},
                        #     {2}
                        #     """.format(
                        #         spider.name,
                        #         spider.enabled,
                        #         spider.minute.value
                        #     )
                        # )
                        updated_spiders_list1.append(spider)
                    else:
                        spider.set_enabled("no")
                        # print("NOOOO")
                        # print(
                        #     """
                        #     {0},
                        #     {1},
                        #     {2}
                        #     """.format(
                        #         spider.name,
                        #         spider.enabled,
                        #         spider.minute.value
                        #     )
                        # )
                        updated_spiders_list1.append(spider)

            # update minute mode
            updated_spiders_list2 = list()
            spiders_deploy_minute_mode = req.args.get("deploy_minute_mode")
            spiders_deploy_minute_mode = {i[1]: i[0] for i in [x.split("|") for x in spiders_deploy_minute_mode]}
            # split value on |
            for spider in updated_spiders_list1:
                if spiders_deploy_minute_mode.get(spider.name) is not None:
                    hour_mode = str(spiders_deploy_minute_mode.get(spider.name)).lower()
                    spider.minute.set_mode(hour_mode)

                    updated_spiders_list2.append(spider)

            # update hour mode
            updated_spiders_list3 = list()
            spiders_deploy_hour_mode = req.args.get("deploy_hour_mode")
            spiders_deploy_hour_mode = {i[1]: i[0] for i in [x.split("|") for x in spiders_deploy_hour_mode]}
            # split value on |
            for spider in updated_spiders_list2:
                if spiders_deploy_hour_mode.get(spider.name) is not None:
                    hour_mode = str(spiders_deploy_hour_mode.get(spider.name)).lower()
                    spider.hour.set_mode(hour_mode)

                    updated_spiders_list3.append(spider)

            # update minute value
            updated_spiders_list4 = list()
            spiders_deploy_minute_value = req.args.get("deploy_minute_value")
            spiders_deploy_minute_value = {i[1]: i[0] for i in [x.split("|") for x in spiders_deploy_minute_value]}
            # split value on |
            for spider in updated_spiders_list3:
                if spiders_deploy_minute_value.get(spider.name) is not None:
                    minute_value = spiders_deploy_minute_value.get(spider.name)
                    # print(minute_value)
                    spider.minute.set_value(minute_value)

                    updated_spiders_list4.append(spider)

            # update hour value
            updated_spiders_list5 = list()
            spiders_deploy_hour_value = req.args.get("deploy_hour_value")
            spiders_deploy_hour_value = {i[1]: i[0] for i in [x.split("|") for x in spiders_deploy_hour_value]}
            # split value on |
            for spider in updated_spiders_list4:
                if spiders_deploy_hour_value.get(spider.name) is not None:
                    hour_value = spiders_deploy_hour_value.get(spider.name)
                    spider.hour.set_value(hour_value)

                    updated_spiders_list5.append(spider)

            new_config = ProjectConfigController(self.path, self.root.config)
            new_config.write_config(version_name, updated_spiders_list5)

            return self.save_config.__name__

    def deploy_version(self, req):
        # FIXME
        deploy_version = req.args.get("deploy_version")
        if deploy_version:
            pcc = ProjectConfigController(self.path, self.root.config)
            pcc.use_crontab(deploy_version[0], user_name=self.root.config.get("user"))
            return self.deploy_version.__name__

    def add_version(self, req):
        add_egg = req.args.get("add_version")
        if add_egg:
            form = cgi.FieldStorage(
                fp=req.content,
                headers=req.getAllHeaders(),
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': req.getAllHeaders()['content-type'],
                         }
            )
            eggf = StringIO(form["filename"].value)
            project = self.path
            version = form["filename"].filename.rstrip(".egg")
            self.root.eggstorage.put(eggf, project, version)

            return self.add_version.__name__

    def del_version(self, req):
        del_version = req.args.get("del_version")
        if del_version:
            project_name = self.path
            # FIXME
            version_name = del_version[0]
            egg = version_name + ".egg"
            egg_path = path.join(self.eggstorage.basedir, project_name, egg)

            config_base_dir = self.root.config.get("config_dir")
            version_config_path_crontab = path.join(config_base_dir, project_name, version_name)
            version_config_path_xml = path.join(config_base_dir, project_name, version_name + ".xml")
            if path.exists(egg_path):
                remove(egg_path)
                if path.exists(version_config_path_crontab):
                    remove(version_config_path_crontab)
                if path.exists(version_config_path_xml):
                    remove(version_config_path_xml)

                self.scheduler.update_projects()
                return self.del_version.__name__

    def buttons(self, req):
        print(req.args.keys())
        for button_name in req.args.keys():
            if button_name == "deploy_version":
                return self.deploy_version(req)
            elif button_name == "add_version":
                return self.add_version(req)
            elif button_name == "run_project":
                return "run_project"
            elif button_name == "save_config":
                print("sadasdasdasds")
                return self.save_config(req)

        # INFO dont use else statement

    def render_POST(self, request):
        print(request.args)
        action = self.buttons(request)
        print(action)
        if action in ("save_config", "deploy_version", "add_version",):
            request.redirect(self.path)
            return ""
        else:
            return action

        #
        # run_project = request.args.get("run_project")
        # if run_project:
        #     # project or egg name, here is the same
        #     version_name = run_project[0]
        #
        #     spiders = request.args['spiders_for_run']
        #     # self.root.eggstorage.get(self.path, version_name)
        #     # print(str(self.root.eggstorage.get(self.path, version_name)))
        #     print(run_project)
        #     print(spiders)
        #     print(len(spiders))
        #
        #     for spider in spiders:
        #         args = dict()
        #         args['settings'] = dict()
        #         jobid = uuid.uuid1().hex
        #         args['_job'] = jobid
        #         # print(args)
        #         self.root.scheduler.schedule(self.path, spider, **args)
        #
        #     # save_config = request.args['save_config']
        #     print(request.args)
        #     request.redirect(self.path)
        #     return ""


class Jobs(Resource):
    def __init__(self, root, path):
        Resource.__init__(self)
        self.root = root
        self.path = path
        # FIXME
        self.root_info = self.root.get_main_info()

    # def get_running_jobs(self):
    #     for p in self.root.launcher.processes.values():
    #         for a in ['project', 'spider', 'job', 'pid']:
    #             getattr(p, a)
    def render_GET(self, request):
        # FIXME
        projects_list = list(enumerate(self.root_info))

        finished = reversed(self.root.launcher.finished)

        template = self.root.env.get_template('jobs.html')
        return template.render(projects_list=projects_list, finished=finished).encode('utf-8')

