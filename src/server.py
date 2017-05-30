'''
CSCI 379 Programming Assignment 2
By Antonina Serdyukova
With help of this tutorial https://ruslanspivak.com/lsbaws-part3/
'''
import errno
import os
import sys
import signal
import socket
import datetime
import time

if len(sys.argv) > 1:
    p = int(sys.argv[1])
else:
    p = 80

SERVER_ADDRESS = (HOST, PORT) = '', p
REQUEST_QUEUE_SIZE = 1024

def grim_reaper(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(
                -1,          # Wait for any child process
                 os.WNOHANG  # Do not block and return EWOULDBLOCK error
            )
        except OSError:
            return

        if pid == 0:  # no more zombies
            return

def get_file(path, br_type, sys_type):
    try:
        path = path[1:]
        f = open(path,'r')
        l = f.read(1024)
        data = ''
        while (l):
            data += l
            l = f.read(1024)
        f.close()
        data = data.replace('index.html"', path + '" from ' + br_type + ' running on ' + sys_type)
        return data
    except FileNotFoundError:
        f = open('404.html','r')
        l = f.read(1024)
        data = ''
        while (l):
            data += l
            l = f.read(1024)
        f.close()
        return data

def map_os(line):
    os_list = [
    'Windows 3.11',
    'Windows 95',
    'Windows 98',
    'Windows 2000',
    'Windows XP',
    'Windows Server 2003',
    'Windows Vista',
    'Windows 7',
    'Windows 8',
    'Windows 10',
    'Windows NT 4.0',
    'Windows ME',
    'Open BSD',
    'Sun OS',
    'Linux',
    'Mac OS',
    'QNX',
    'BeOS',
    'OS/2',
    'Search Bot'
    ]
    ua_list = [
    ['Win16'],
    ['Windows 95','Win95','Windows_95'],
    ['Windows 98','Win98'],
    ['Windows NT 5.0','Windows 2000'],
    ['Windows NT 5.1','Windows XP'],
    ['Windows NT 5.2'],
    ['Windows NT 6.0'],
    ['Windows NT 6.1'],
    ['Windows NT 6.2'],
    ['Windows NT 10.0'],
    ['Windows NT 4.0','WinNT4.0','WinNT','Windows NT'],
    ['Windows ME'],
    ['OpenBSD'],
    ['SunOS'],
    ['Linux','X11'],
    ['Mac_PowerPC','Macintosh'],
    ['QNX'],
    ['BeOS'],
    ['OS/2'],
    ['nuhk','Googlebot','Yammybot','Openbot','Slurp','MSNBot','Ask Jeeves/Teoma','ia_archiver']
    ]
    i = 0
    for ua_vals in ua_list:
        for ua_val in ua_vals:
            if ua_val in line:
                return os_list[i]
        i += 1
    return 'OS not detected'

def map_browser(line):
    br_name = [
    'Firefox',
    'Seamonkey',
    'Chrome',
    'Chromium',
    'Safari',
    'Opera',
    'Internet Explorer'
    ]
    ua_str = [
    ['Firefox'],
    ['Seamonkey'],
    ['Chrome'],
    ['Chromium'],
    ['Safari'],
    ['OPR', 'Opera'],
    ['MSIE']
    ]
    i = 0
    for ua_s in ua_str:
        for ua in ua_s:
            if ua in line:
                return br_name[i]
        i += 1
    return 'Browser not detected'

def detect_system(lines):
    info = []
    for line in lines:
        if 'User-Agent' in line:
            return map_browser(line), map_os(line)
    return 'System information is not available'

def hist(addr, path):
    try:
        f = open('ip-log.txt','a+')
        c = open('ip-log.txt','r')
        contents = c.read()
        if addr not in contents:
            f.write(addr + '\n')
        p = open(str(addr),'a+')
        cp = open(str(addr), 'r')
        cont = cp.read()
        p.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + '\t' + path + '\n')
        cp.close()
        p.close()
        c.close()
        f.close()
    except FileNotFoundError:
        print('Error opening the file in hist()')

def get_history(addr):
    try:
        f = open(str(addr), 'r')
        contents = f.readlines()
        h = open('history.html','r')
        l = h.read(1024)
        data = ''
        while (l):
            data += l
            l = h.read(1024)
        h.close()
        f.close()
        data = data.replace('No history', '<br>'.join(contents))
        return data
    except FileNotFoundError:
        print('Error opening the file in get_history()')

def handle_request(client_connection, client_address):
    try:
        request = client_connection.recv(1024)
        reqstr = request.decode()
        first_line = reqstr.splitlines()[0]
        all_lines = reqstr.splitlines()
        browser_type, system_type = detect_system(all_lines)
        req_type = first_line.split()[0]
        path = first_line.split()[1]
        hist(client_address, path)
        if req_type == 'GET':
            http_response = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'
            client_connection.sendall(http_response.encode())
            if path == '/':
                data = get_file('/index.html', browser_type, system_type)
            elif path == '/history.html':
                data = get_history(client_address)
            else:
                data = get_file(path, browser_type, system_type)
            client_connection.sendall(data.encode())
        else:
            http_response = 'HTTP/1.1 404 NotFound\nContent-Type: text/html\n\n'
            client_connection.sendall(http_response.encode())
            data = get_file('404.html', browser_type, system_type)
            client_connection.sendall(data.encode())
    except IndexError:
        pass

def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    signal.signal(signal.SIGCHLD, grim_reaper)

    while True:
        try:
            client_connection, client_address = listen_socket.accept()
        except IOError as e:
            code, msg = e.args
            # restart 'accept' if it was interrupted
            if code == errno.EINTR:
                continue
            else:
                raise

        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child listen socket copy
            handle_request(client_connection, client_address[0])
            client_connection.close()
            os._exit(0)
        else:  # parent
            client_connection.close()  # close parent copy and loop over

if __name__ == '__main__':
    serve_forever()
