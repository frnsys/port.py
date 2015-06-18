"""
this is super hacky...but it works (on ubuntu 14.04, at least)

This generates the necessary config and application files
for supervisor and nginx to run the uwsgi flask processes.

I don't feel good about this approach but it works for now
"""

import os
import subprocess
from jinja2 import Template

supervisor_tmpl = Template('''
[program:{{ port_name }}]
command=/usr/bin/uwsgi --plugin python3 -s /tmp/{{ port_name }}.sock -w {{ port_name }}:app --chmod-socket=666
directory={{ app_dir }}
autostart=true
autorestart=true
stdout_logfile=/var/log/{{ port_name }}.log
redirect_stderr=true
stopsignal=QUIT
user={{ user }}
''')

application_tmpl = Template('''
from port.cli import app_for_site
app = app_for_site('{{ site_name }}', {{ port }})
''')

nginx_tmpl = Template('''
server {
    listen       80;
    server_name  {{ host }};

    location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/{{ port_name }}.sock;
            uwsgi_param UWSGI_CHDIR {{ app_dir }};
            uwsgi_param UWSGI_MODULE {{ port_name }};
            uwsgi_param UWSGI_CALLABLE app;
    }

    error_page   404              /404.html;

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
            root   /usr/share/nginx/html;
    }
}
''')


def host_site(site_name, host, user, port=5005):
    port_name = 'port_{}'.format(site_name)
    app_dir = '/tmp'

    supervisor_conf = supervisor_tmpl.render(port_name=port_name, app_dir=app_dir, user=user)
    application = application_tmpl.render(site_name=site_name, port=port)
    nginx_conf = nginx_tmpl.render(host=host, port_name=port_name, app_dir=app_dir)

    nginx_file = '/etc/nginx/conf.d/{}.conf'.format(host)
    with open(nginx_file, 'w') as f:
        f.write(nginx_conf)
        print('Wrote to', nginx_file)

    supervisor_file = '/etc/supervisor/conf.d/{}.conf'.format(port_name)
    with open(supervisor_file, 'w') as f:
        f.write(supervisor_conf)
        print('Wrote to', supervisor_file)

    app_file = '{}/{}.py'.format(app_dir, port_name)
    with open(app_file, 'w') as f:
        f.write(application)
        print('Wrote to', app_file)

    subprocess.call(['sudo', 'service', 'supervisor', 'restart'])
    subprocess.call(['sudo', 'service', 'nginx', 'restart'])


def unhost_site(site_name, host):
    port_name = 'port_{}'.format(site_name)
    app_dir = '/tmp'

    nginx_file = '/etc/nginx/conf.d/{}.conf'.format(host)
    supervisor_file = '/etc/supervisor/conf.d/{}.conf'.format(port_name)
    app_file = '{}/{}.py'.format(app_dir, port_name)

    for f in [nginx_file, supervisor_file, app_file]:
        os.remove(f)
        print('Removed {}'.format(f))

    subprocess.call(['sudo', 'service', 'supervisor', 'restart'])
    subprocess.call(['sudo', 'service', 'nginx', 'restart'])
