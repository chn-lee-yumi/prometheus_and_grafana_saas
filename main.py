import json
import os
import time
from datetime import timedelta

import flask_login
from flask import Flask, request, redirect

# 初始化Flask
app = Flask(__name__)
app.send_file_max_age_default = timedelta(seconds=30)
app.secret_key = "s1f3ha9q3sdahfkgu3p094oyi4r89pt0ua"
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
data_time = 0

avail_ip_set = {'172.22.124.8', '172.22.124.9', '172.22.124.10', '172.22.124.11', '172.22.124.12', '172.22.124.13', '172.22.124.14', '172.22.124.15'}

######################以下是登录部分代码######################

users = {'dn42': {'password': 'dn42'}}  # 前端页面的用户名密码


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(req):
    username = req.form.get('username')
    if username not in users:
        return
    user = User()
    user.id = username
    user.is_authenticated = req.form['password'] == users[username]['password']
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return app.send_static_file("login.html")
    username = request.form['username']
    try:
        if request.form['password'] == users[username]['password']:
            user = User()
            user.id = username
            flask_login.login_user(user)
            return redirect('/')
    except:
        pass
    return redirect('/login')


@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return app.send_static_file("login.html")


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/login')


######################以上是登录部分代码######################


def collect_data():
    global cluster_data
    global instance_data
    global data_time
    cluster_data = get_cluster_data()
    instance_data = get_instance_data()
    data_time = time.time()


def get_node_info(ip: str, node: str = None) -> dict:
    """
    返回节点信息，包括配置和负载。
    :param ip: 节点ip地址（hostname也行，ssh需要能够解析）
    :param node: 节点名称（自定义）
    :return: 节点信息字典
    """
    if not node:
        node = ip
    sys_info = os.popen("top -b -n 1 | head -n5 && lscpu | grep 'CPU(s):' | awk '{print $2}'").read().strip().split('\n')
    try:
        cpu = 100 - float(sys_info[2].split()[7])
    except:
        cpu = 0
    # core = sys_info[5].split()[1]
    core = sys_info[5]
    cpu = "%.1f%% / %s" % (cpu, core)
    load_tmp = sys_info[0].split()[-3:]
    load = load_tmp[0][:-1] + ' / ' + load_tmp[1][:-1] + ' / ' + load_tmp[2]
    load_5min = load_tmp[1][:-1]
    mem_total, mem_used = sys_info[3].split()[3:8:4]
    # mem = "%dM / %dM / %.1f%%" % (round(int(mem_used) / 1024), round(int(mem_total) / 1024), round(int(mem_used) / int(mem_total) * 100, 1))
    mem = "%dM / %dM / %.1f%%" % (round(float(mem_used)), round(float(mem_total)), round(float(mem_used) / float(mem_total) * 100, 1))
    swap_total, swap_used = sys_info[4].split()[2:7:4]
    if swap_total != '0':
        swap = "%dM / %dM / %.1f%%" % (
            # round(int(swap_used) / 1024), round(int(swap_total) / 1024), round(int(swap_used) / int(swap_total) * 100, 1))
            round(float(swap_used)), round(float(swap_total)), round(float(swap_used) / float(swap_total) * 100, 1))
    else:
        swap = "0M / 0M / 0%"

    disk_used, disk_total, disk_percent = os.popen("df -h | grep /home | awk '{print $3,$4,$5}'").read().strip().split()
    disk = "%s / %s / %s" % (disk_used, disk_total, disk_percent)

    return {
        'node': node,
        'cpu': cpu,
        'load': load,
        'mem': mem,
        'swap': swap,
        'mem_used': float(mem_used),
        'mem_total': float(mem_total),
        'swap_used': float(swap_used),
        'swap_total': float(swap_total),
        'load_5min': float(load_5min),
        'core': int(core),
        'disk': disk,
        'disk_used': disk_used,
        'disk_total': disk_total,
        'disk_percent': disk_percent
    }


def get_node_instances(ip: str = None) -> list:
    """
    获取节点上运行的实例（仅针对alone模式）
    :param ip: 节点ip地址（hostname也行），如果为None，则为本机
    :return:
    """
    data = []
    instance_status = os.popen('./pro_gra_saas.sh list').read().strip().split('\n')
    for line in instance_status:
        if not line:
            continue
        line = line.split()
        status = line[1]
        name, ipv4 = line[0].split('_')
        data.append({
            'name': name,
            'state': status,
            'ipv4': ipv4,
            'location': 'la_us',
        })

    return data


def get_cluster_data() -> list:
    """
    获取集群宿主信息
    :return:
    """
    data = []
    data.append(get_node_info('hz_cn'))
    return data


def get_instance_data() -> list:
    """
    获取集群实例信息
    :return:
    """
    data = []
    data.extend(get_node_instances(''))
    return data


def scheduler():
    global avail_ip_set
    used_ip_list = os.popen("ip addr show dev docker0 | grep inet | awk '{print $2}' | awk -F '/' '{print $1}'").read().strip().split()
    free_ip = avail_ip_set - set(used_ip_list)
    if len(free_ip) > 0:
        return list(free_ip)[0]
    else:
        return None


######################以下是API部分代码######################

@app.route("/")
@flask_login.login_required
def index():
    return app.send_static_file("index.html")


@app.route("/conf")
@flask_login.login_required
def conf_html():
    return app.send_static_file("conf.html")


@app.route("/api/status")
@flask_login.login_required
def api_status():
    global cluster_data
    global instance_data
    global data_time
    if time.time() - data_time > 3:
        collect_data()
    return json.dumps({
        'clusterData': cluster_data,
        'instanceData': instance_data
    })


@app.route("/api/optInstance", methods=['POST'])
@flask_login.login_required
def api_opt_instance():
    data = json.loads(request.get_data(as_text=True))
    if "name" in data and "opt" in data and "ipv4" in data:
        if data['name'].find(' ') != -1 or data['name'].find(';') != -1 or data['name'].find('_') != -1:
            return 'Error: Please only use letters and number.'
        if data['opt'] in ['start', 'stop', 'restart', 'delete']:
            ret = os.popen("./pro_gra_saas.sh " + data['opt'] + " " + data['name'] + " " + data['ipv4']).read()
            return ret
        if data['opt'] == "configure":
            return redirect('conf?name=' + data['name'] + "&ipv4=" + data['ipv4'])
    else:
        return 'Error: Name and IPv4 must match.'


@app.route("/api/createInstance", methods=['POST'])
@flask_login.login_required
def api_create_instance():
    data = json.loads(request.get_data(as_text=True))
    if "name" in data:
        name = data['name']
        if data['saas'] != "pro_gra":
            return "SaaS not found!"
        target_ip = scheduler()
        if not target_ip:
            return 'No enough ip! Please contact us to add it.'
        ret = os.popen(' '.join(['./pro_gra_saas.sh', 'create', name, target_ip])).read()
        return ret


@app.route("/api/getConf", methods=['GET'])
@flask_login.login_required
def api_get_conf():
    name = request.args.get("name")
    ipv4 = request.args.get("ipv4")
    with open("/home/cloud/saas/" + name + "_" + ipv4 + "/prometheus.yml", 'r') as f:
        pro_conf = f.read()
    return json.dumps({"data": pro_conf})


@app.route("/api/putConf", methods=['POST'])
@flask_login.login_required
def api_put_conf():
    data = json.loads(request.get_data(as_text=True))
    name = data["name"]
    ipv4 = data["ipv4"]
    conf = data["conf"]
    with open("/home/cloud/saas/" + name + "_" + ipv4 + "/prometheus.yml", 'w') as f:
        f.write(conf)
    ret = os.popen("./pro_gra_saas.sh restart " + name + " " + ipv4).read()
    return ret


if __name__ == '__main__':
    app.run('172.22.124.4', port=80)
