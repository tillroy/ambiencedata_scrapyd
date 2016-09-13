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
import os
import time
from zipfile import is_zipfile, ZipFile
from re import findall, match
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

        self.env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

        self.summary = self.get_main_summary()

        # add webservices API
        services = config.items('services', ())
        for servName, servClsName in services:
          servCls = load_object(servClsName)
          self.putChild(servName, servCls(self))


        self.update_projects()

    def __connect_static_files(self):
        srtatic_dir = os.path.join(os.path.dirname(__file__), "static")
        gui_files = (
            "bootstrap.min.css",
            "bootstrap-theme.min.css",
            "ie10-viewport-bug-workaround.css",
            "starter-template.css",
            "theme.css",
            "styles.css",
            "jquery.min.js",
            "bootstrap.min.js",
            "ie10-viewport-bug-workaround.js",
            "ie-emulation-modes-warning.js",
            "bootstrap-filestyle.min.js",
            "bootstrap-checkbox.min.js",
            "modal_windows.js",
            "logo.png",
        )

        for g_file in gui_files:
            self.putChild(g_file, static.File(os.path.join(srtatic_dir, g_file)))

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
        if path == 'home' or path == '':
            return self
        elif path in self.scheduler.list_projects():
            return Project(self, path)
        elif path == 'jobs':
            return Jobs(self, path)
        else:
            return NoResource()

    def render_GET(self, request):
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        request.args = dict()
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('projects_list.html')

        msg = dir(self.runner)

        return template.render(msg=msg, projects_list=list(enumerate(self.get_main_info()))).encode('utf-8')

    def render_POST(self, request):
        del_project = request.args.get("del_project")
        if del_project:
            print(request.args)
            project_name = request.args.get("del_project")
            if project_name:
                folder_path = os.path.join(self.eggstorage.basedir, request.args["del_project"][0])
                if os.path.exists(folder_path):
                    pass
                    shutil.rmtree(folder_path)
                    self.scheduler.update_projects()
                    request.redirect('/')
                    return ""

        add_project = request.args.get("add_project")
        if add_project:
            project_name = request.args.get("project_name")
            if project_name:
                folder_path = os.path.join(self.eggstorage.basedir, request.args["project_name"][0])
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
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
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
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
        summary = self.get_project_summary()
        project_summary = summary.get("project_summary")
        # print("summary", project_summary)
        for version in project_summary:
            if version.get("egg_name") == version_name:
                return version
            # spiders = version.get("egg_name")
            # print(spiders)
        #     if version.egg_name == version_name:
        #         return version
        return None

    def add_egg(self, req):
        """add agg and update projects"""
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
        print(version)
        self.root.eggstorage.put(eggf, project, version)

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
        page = self.get_project_summary()

        template = self.root.env.get_template('project.html')
        return template.render(
            project_name=page.get("project_name"),
            projects_list=projects_list,
            versions_list=page.get("project_summary"),
            msg=str(self.get_status())
        ).encode('utf-8')

    def render_POST(self, request):
        deploy_egg = request.args.get("deploy_egg")
        if deploy_egg:
            pcc = ProjectConfigController(self.path, self.root.config)
            # FIXME put user name into config file
            pcc.use_crontab(deploy_egg[0], user_name="roman")
            request.redirect(self.path)
            return ""

        add_egg = request.args.get("add_egg")
        if add_egg:
            self.add_egg(request)
            request.redirect('#')
            return ""

        run_project = request.args.get("run_project")
        if run_project:
            # project or egg name, here is the same
            version_name = run_project[0]

            spiders = request.args['spiders_for_run']
            # self.root.eggstorage.get(self.path, version_name)
            # print(str(self.root.eggstorage.get(self.path, version_name)))
            print(run_project)
            print(spiders)
            print(len(spiders))

            for spider in spiders:
                args = dict()
                args['settings'] = dict()
                jobid = uuid.uuid1().hex
                args['_job'] = jobid
                # print(args)
                self.root.scheduler.schedule(self.path, spider, **args)

            # save_config = request.args['save_config']
            print(request.args)
            request.redirect(self.path)
            return ""

        save_config = request.args.get("save_config")
        if save_config:
            version_name = save_config[0]
            version_summary = self.get_version_summary(version_name)

            # INFO it works
            print(version_summary.get("spiders"))

            # if request.args.get("spider_config"):
            #     for spider_name in spidersnames_list:
            #         sp = Spider()
            print(request.args)
            request.redirect(self.path)
            return ""



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

        res = dir(self.root.launcher)


        template = self.root.env.get_template('jobs.html')
        return template.render(projects_list=projects_list, msg=res).encode('utf-8')
