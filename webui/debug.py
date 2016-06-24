#coding=utf8
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-23 00:19:06


import sys
import time
import socket
import inspect
import datetime
import traceback
from flask import render_template, request, json
import flask_login

from libs import utils, sample_handler, dataurl
from libs.response import rebuild_response
from processor.project_module import ProjectManager, ProjectFinder
from app import app

import os

from flask import url_for
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


'''
我的第一个版本
'''

default_task = {
    'taskid': 'data:,on_start',
    'project': '',
    'url': 'data:,on_start',
    'process': {
        'callback': 'on_start',
    },
}
default_script = inspect.getsource(sample_handler).decode('utf8')

column_info = {

}
proj_info = {
    u'begin_url': '',
    u'detail_page_url': '',
    u'next_page_url': '',
    u'save_path': '',
    u'column_info': column_info
}

file_name = ''

def get_my_script(begin_url, detail_page_url, next_page_url, save_path, column_dict):
    # print default_script
    return default_script.replace('__BEGIN_URL__', begin_url).\
        replace('__DETAIL_PAGE_URL__', detail_page_url).\
        replace('__NEXT_PAGE_URL__', next_page_url).\
        replace('__SAVE_PATH__', save_path).\
        replace('__COLUMN_DICT__', column_dict).\
        replace('"""', '')

@app.route('/debug/<project>', methods=['GET', 'POST'])
def debug(project):
    global column_info, proj_info
    column_info = {
    }
    proj_info = {
        u'begin_url': '',
        u'detail_page_url': '',
        u'next_page_url': '',
        u'save_path': '',
        u'column_info': column_info
    }
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    global file_name
    file_name = project + '.txt'
    read_proj_info()
    # print proj_info

    info = projectdb.get(project, fields=['name', 'script'])

    # print '>>>>>>>>>>>>>>>>>>>>'
    # print url_for('static', filename='debug.js')
    # print '>>>>>>>>>>>>>>>>>>>>'
    #
    # print '------------------------------'
    # print info['script']
    # print '------------------------------'

    # if info:
    #     begin_url =
    #     detail_page_url =
    #     next_page_url =
    # else:
    #     script = (default_script
    #               .replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    #               .replace('__PROJECT_NAME__', project)
    #               .replace('__START_URL__', request.values.get('start-urls') or '__START_URL__'))

    begin_url = proj_info['begin_url']
    detail_page_url = proj_info['detail_page_url']
    next_page_url = proj_info['next_page_url']
    save_path = proj_info['save_path']

    taskid = request.args.get('taskid')
    if taskid:
        taskdb = app.config['taskdb']
        task = taskdb.get_task(
            project, taskid, ['taskid', 'project', 'url', 'fetch', 'process'])
    else:
        task = default_task

    default_task['project'] = project

    # print 'task=' + str(task)

    columns = []
    for k, v in column_info.iteritems():
        if str(v['inspired_word']).strip() != '':
            v[u'column_name'] = k
            columns.append(v)

    return render_template("debug2.html", begin_url=begin_url.decode('utf8'), detail_page_url=detail_page_url.decode('utf8'),
                           next_page_url=next_page_url.decode('utf8'), project_name=project.decode('utf8'), columns=columns,
                           save_path=save_path)


@app.before_first_request
def enable_projects_import():
    sys.meta_path.append(ProjectFinder(app.config['projectdb']))


@app.route('/debug/<project>/save', methods=['POST', ])
def save(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    begin_url = request.form['beginUrl']
    detail_page_url = request.form['detailPageUrl']
    next_page_url = request.form['nextPageUrl']
    save_path = request.form['savePath']

    print '================'
    print \
        begin_url, \
        detail_page_url, \
        next_page_url,\
        save_path
    print '================'

    proj_info['begin_url'] = begin_url
    proj_info['detail_page_url'] = detail_page_url
    proj_info['next_page_url'] = next_page_url
    proj_info['column_info'] = column_info
    proj_info['save_path'] = save_path

    # print column_info
    write_proj_info()

    script = get_my_script(begin_url, detail_page_url, next_page_url, save_path, change_dict_to_str(column_info))
    print script

    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if project_info and 'lock' in projectdb.split_group(project_info.get('group')) \
            and not flask_login.current_user.is_active():
        return app.login_response

    if project_info:
        info = {
            'script': script,
        }
        if project_info.get('status') in ('DEBUG', 'RUNNING', ):
            info['status'] = 'CHECKING'
        projectdb.update(project, info)
    else:
        info = {
            'name': project,
            'script': script,
            'status': 'TODO',
            'rate': app.config.get('max_rate', 1),
            'burst': app.config.get('max_burst', 3),
        }
        projectdb.insert(project, info)

    rpc = app.config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            app.logger.warning('connect to scheduler rpc error: %r', e)
            return 'rpc error', 200

    return 'ok', 200


@app.route('/debug/<project>/add', methods=['POST', ])
def add(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400

    inspired_word = str(request.form['inspiredWord']).strip()
    column_name = str(request.form['columnName']).strip()
    extract_content = str(request.form['extractContent']).strip()
    if inspired_word == '' or extract_content == '':
        inspired_word = ''
        extract_content = ''
    column_info[column_name] = {u'inspired_word': inspired_word, u'extract_content': extract_content}
    # print '>>>>>>>>>>>>>>>>>>>>>'
    # print column_info
    write_proj_info()
    return 'ok', 200

@app.route('/debug/<project>/get')
def get_script(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    info = projectdb.get(project, fields=['name', 'script'])
    return json.dumps(utils.unicode_obj(info)), \
        200, {'Content-Type': 'application/json'}


@app.route('/helper.js')
def resizer_js():
    host = request.headers['Host']
    return render_template("helper.js", host=host), 200, {'Content-Type': 'application/javascript'}


@app.route('/helper.html')
def resizer_html():
    height = request.args.get('height')
    script = request.args.get('script', '')
    return render_template("helper.html", height=height, script=script)

def write_proj_info():
    global proj_info
    if os.path.exists(file_name):
        os.remove(file_name)
    my_output = open(file_name, 'w')
    try:
        my_output.write('{')
        for k, v in proj_info.iteritems():
            if isinstance(v, dict):
                v = change_dict_to_str(v)
                s = '"' + k + '"' + ': ' + v + ', '
            else:
                s = '"' + k + '"' + ': ' + '"' + v + '", '
            s = s.encode('utf8')
            my_output.write(s)
        my_output.write('}')
    finally:
        my_output.close()

def change_dict_to_str(my_dict):
    ss = '{'
    for k, v in my_dict.iteritems():
        if isinstance(v, dict):
            v = change_dict_to_str(v)
            s = '"' + k + '"' + ': ' + v + ', '
        else:
            s = '"' + k + '"' + ': ' + '"' + v + '", '
        ss += s
        # print k, v
    ss += '}'
    return ss

def read_proj_info():
    global proj_info, column_info
    if not os.path.exists(file_name):
        return
    my_input = open(file_name, 'r')
    try:
        # print '----------------'
        s = my_input.read()
        print s
        proj_info = dict(eval(s))
        # print '----------------'
        # print proj_info
        # print '----------------'
        column_info = proj_info['column_info']
        print column_info
    except:
        column_info = {
        }
        proj_info = {
            u'begin_url': u'',
            u'detail_page_url': u'',
            u'next_page_url': u'',
            u'save_path': u'',
            u'column_info': column_info
        }
    finally:
        my_input.close()

#######################################################################


@app.route('/debug/<project>/debug', methods=['GET', 'POST'])
def debug2(project):
    print('debug2执行！')
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    info = projectdb.get(project, fields=['name', 'script'])
    if info:
        script = info['script']
    else:
        script = (default_script
                  .replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                  .replace('__PROJECT_NAME__', project)
                  .replace('__START_URL__', request.values.get('start-urls') or '__START_URL__'))

    taskid = request.args.get('taskid')
    if taskid:
        taskdb = app.config['taskdb']
        task = taskdb.get_task(
            project, taskid, ['taskid', 'project', 'url', 'fetch', 'process'])
    else:
        task = default_task

    # print 'task: ' + str(task)
    # print 'script: ' + script
    # print 'project_name: ' + project

    default_task['project'] = project
    return render_template("debug.html", task=task, script=script, project_name=project)


@app.route('/debug/<project>/debug/save', methods=['POST', ])
def save2(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    script = request.form['script']
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if project_info and 'lock' in projectdb.split_group(project_info.get('group')) \
            and not flask_login.current_user.is_active():
        return app.login_response

    if project_info:
        info = {
            'script': script,
        }
        if project_info.get('status') in ('DEBUG', 'RUNNING', ):
            info['status'] = 'CHECKING'
        projectdb.update(project, info)
    else:
        info = {
            'name': project,
            'script': script,
            'status': 'TODO',
            'rate': app.config.get('max_rate', 1),
            'burst': app.config.get('max_burst', 3),
        }
        projectdb.insert(project, info)

    rpc = app.config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            app.logger.warning('connect to scheduler rpc error: %r', e)
            return 'rpc error', 200

    return 'ok', 200


@app.route('/debug/<project>/debug/run', methods=['POST', ])
def run(project):
    start_time = time.time()
    try:
        task = utils.decode_unicode_obj(json.loads(request.form['task']))
    except Exception:
        result = {
            'fetch_result': "",
            'logs': u'task json error',
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
        return json.dumps(utils.unicode_obj(result)), \
            200, {'Content-Type': 'application/json'}

    project_info = {
        'name': project,
        'status': 'DEBUG',
        'script': request.form['script'],
    }

    if request.form.get('webdav_mode') == 'true':
        projectdb = app.config['projectdb']
        info = projectdb.get(project, fields=['name', 'script'])
        if not info:
            result = {
                'fetch_result': "",
                'logs': u' in wevdav mode, cannot load script',
                'follows': [],
                'messages': [],
                'result': None,
                'time': time.time() - start_time,
            }
            return json.dumps(utils.unicode_obj(result)), \
                200, {'Content-Type': 'application/json'}
        project_info['script'] = info['script']

    fetch_result = {}
    try:
        fetch_result = app.config['fetch'](task)
        response = rebuild_response(fetch_result)
        module = ProjectManager.build_module(project_info, {
            'debugger': True
        })
        ret = module['instance'].run_task(module['module'], task, response)
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
            'fetch_result': fetch_result,
            'logs': logs,
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
    else:
        result = {
            'fetch_result': fetch_result,
            'logs': ret.logstr(),
            'follows': ret.follows,
            'messages': ret.messages,
            'result': ret.result,
            'time': time.time() - start_time,
        }
        result['fetch_result']['content'] = response.text
        if (response.headers.get('content-type', '').startswith('image')):
            result['fetch_result']['dataurl'] = dataurl.encode(
                response.content, response.headers['content-type'])

    try:
        # binary data can't encode to JSON, encode result as unicode obj
        # before send it to frontend
        return json.dumps(utils.unicode_obj(result)), 200, {'Content-Type': 'application/json'}
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
            'fetch_result': "",
            'logs': logs,
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
        return json.dumps(utils.unicode_obj(result)), 200, {'Content-Type': 'application/json'}