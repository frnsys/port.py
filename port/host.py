"""
this is super hacky
"""

import subprocess
from jinja2 import Template

supervisor_tmpl = Template('''
[program:{{ port_name }}]
command=/usr/bin/uwsgi --plugin python3 -s /tmp/{{ port_name }}.sock -w application:app --chmod-socket=666
directory=/tmp/
autostart=true
autorestart=true
stdout_logfile=/var/log/{{ port_name }}.log
redirect_stderr=true
stopsignal=QUIT
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
            uwsgi_param UWSGI_CHDIR /tmp/;
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


def host(site_name, host, port=5005):
    site_name = 'test_site'
    port_name = 'port_{}'.format(site_name)


    supervisor_conf = supervisor_tmpl.render(port_name=port_name)
    application = application_tmpl.render(site_name=site_name, port=port)
    nginx_conf = nginx_tmpl.render(host=host, port_name=port_name)

    print(application)

    with open('/etc/nginx/sites-enabled/{}.conf'.format(host), 'w') as f:
        f.write(nginx_conf)

    with open('/etc/supervisor/conf.d/{}.conf'.format(port_name), 'w') as f:
        f.write(supervisor_conf)

    with open('/tmp/{}.py'.format(port_name), 'w') as f:
        f.write(application)

    subprocess.call(['sudo', 'service', 'supervisor', 'restart'])
    subprocess.call(['sudo', 'service', 'nginx', 'restart'])
