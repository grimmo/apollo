#-*- encoding: utf-8
# Apollo: Centralized WakeOnLAN


import os
import sqlite3
import re
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, make_response,flash,jsonify
     
import logging
from logging.handlers import RotatingFileHandler
import socket

app = Flask(__name__)
app.config.from_object(__name__)
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'apollo.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    DOMAIN='biblio.unimib.it'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('apollo_schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def resolve_ip(hostname):
    print(app.config['DOMAIN'])
    return socket.gethostbyname(hostname + '.' + app.config['DOMAIN'])

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('select name, mac, ip, enabled, iswol from computers order by ip,name asc')
    computers = cur.fetchall()
    return render_template('index.html', computers=computers)

@app.route('/nuovopc/', methods=['GET','POST'])
def nuovopc():
    error = None
    if request.method == "POST":
        if not bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})']*6) + '$', request.form["mac"].lower())):
            error = "MAC address non valido"
        else:
            try:
                db = get_db()
                try:
                    is_wol_node = request.form["is_wol_node"]
                except KeyError:
                    is_wol_node = 0
                    pass
                db.execute('insert into computers (name,mac,ip,enabled,iswol) values (?, ?, ?, ?, ?)',
                    [str.upper(request.form["name"]), request.form["mac"], resolve_ip(request.form["name"]), 1, is_wol_node])
                db.commit()
            except Exception:
                error = "Errore nell'inserimento del nuovo pc. Computer esistente?"
                logging.exception('Errore nell\'inserimento del nuovo pc.')
                pass
            else:
                flash('Nuovo computer aggiunto')
                return redirect(url_for('index'))
    return render_template('nuovopc.html',error=error)



    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or \
                request.form['password'] != 'secret':
            error = 'Invalid credentials'
        else:
            flash('You were successfully logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

# Aggiunge un computer nel database
# il flag is_wol_node determina se il computer
# e' quello che svegliera' tutti gli altri nella stessa subnet
@app.route('/computers/add/<string:name>/<string:mac>/', methods=['POST'])
def add_computer(name,mac):
    if request.method == "POST":
        try:
            # verifica che il MAC address sia valido
            if not bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})']*6) + '$', mac.lower())):
                return make_response("%s %s" %(name,mac),422)
        except:
            return make_response("INvalid parameters",400)
        else:
            db = get_db()
            try:
                db.execute('insert into computers (name,mac,ip,enabled,iswol) values (?, ?, ?, ?, ?)',
                    [str.upper(name), mac.lower(), request.environ['REMOTE_ADDR'], 1, 0])
                db.commit()
            except:
                return make_response("",409)
            else:
                return make_response("Inserito %s %s" % (name,mac), 201)

@app.route('/computers/<name>/enable/',methods=['PUT','POST'])
def enable(name):
    if request.method == "POST" or request.method == "PUT":
        db = get_db()
        cur = db.execute('update computers set enabled = 1 where name = ?',[str.upper(name)])
        db.commit()
        if cur.rowcount > 0:
            app.logger.info('Enabled Wake On Lan for %s' % name)
            return make_response("", 201)
        else:
            app.logger.warning('Failed attempt to enable wake on lan for non existing host:%s' % name)
            return make_response("ERROR: Not found",404)

@app.route('/computers/<name>/disable/',methods=['PUT','POST'])
def disable(name):
    if request.method == "POST" or request.method == "PUT":
        db = get_db()
        cur = db.execute('update computers set enabled = 0 where name = ?',[str.upper(name)])
        db.commit()
        if cur.rowcount > 0:
            app.logger.info('Disabled Wake On Lan for %s' % name)
            return make_response("", 201)
        else:
            app.logger.warning('Failed attempt to disable wake on lan for non existing host:%s' % name)
            return make_response("ERROR: Not found",404)

@app.route('/computers/<name>/remove/',methods=['DEL','POST'])
def remove(name):
    if request.method == "POST" or request.method == "DEL":
        db = get_db()
        try:
            cur = db.execute('delete from computers where name = ?',[name])
            deleted = cur.rowcount
            app.logger.info('Removed %i rows for computer %s' % (cur.rowcount,name))
            db.commit()
        except:
            return make_response("", 400)
            raise
        else:
            if deleted > 0:
                return make_response("",201)
            else:
                return make_response("",404)

@app.route('/computers/<name>/wolnode/activate/',methods=['PUT','POST'])
def wol_node_activate(name):
    if request.method == "POST" or request.method == "PUT":
        db = get_db()
        db.execute('update computers set iswol = 1 where name = ?',[name])
        db.commit()
        return make_response("", 201)

@app.route('/computers/<name>/wolnode/deactivate/',methods=['PUT','POST'])
def wol_node_deactivate(name):
    if request.method == "POST" or request.method == "PUT":
        db = get_db()
        db.execute('update computers set iswol = 0 where name = ?',[name])
        db.commit()
        return make_response("", 201)

# Ritorna un elenco hostname,macaddress
# di tutti i computer da svegliare che fanno parte
# della stessa subnet dell'ip da cui proviene la richiesta
@app.route('/indecent/wakeuplist/', methods=['GET'])
def computers_to_be_rudely_awakened():
    if request.environ['REMOTE_ADDR']:
        db = get_db()
        cur = db.execute('select name,mac from computers where enabled = 1 and iswol = 0 and ip like ?',['%s%%' % '.'.join(request.environ['REMOTE_ADDR'].split('.')[0:3])])
        mac_list = map(list,cur.fetchall())
        lista = ""
        for computer in mac_list:
            lista+="C:\Temp\WakeOnLan\mac-wol.exe %s /a 149.132.118.255\n" % computer[1]
        return lista

@app.route('/wakeuplist/', methods=['GET'])
def computers_to_be_awakened():
    if request.environ['REMOTE_ADDR']:
        db = get_db()
        cur = db.execute('select name,mac from computers where enabled = 1 and iswol = 0 and ip like ?',['%s%%' % '.'.join(request.environ['REMOTE_ADDR'].split('.')[0:3])])
        mac_list = map(list,cur.fetchall())
        return make_response(jsonify(list(mac_list)),200)

@app.route('/wakeuplist/<ip>/', methods=['GET'])
def computers_to_be_awakened_by_ip(ip):
        db = get_db()
        cur = db.execute('select name,mac from computers where enabled = 1 and iswol = 0 and ip like ?',['%s%%' %
        ('.'.join(ip.split('.')[0:3]) +'.')])
        mac_list = map(list,cur.fetchall())
        return make_response(jsonify(list(mac_list)),200)

if __name__ == '__main__':
    handler = RotatingFileHandler('apollo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run()
