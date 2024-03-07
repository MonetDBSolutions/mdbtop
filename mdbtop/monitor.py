import os
import psutil
import json
from tempfile import mkstemp
from datetime import datetime
from time import sleep
from multiprocessing import Process
from typing import List, Dict, Optional


def _get_sys_info() -> Dict:
    res = dict(cpu={}, memory={})
    res['cpu']['percent'] = psutil.cpu_percent(interval=0.1)
    vm = psutil.virtual_memory()._asdict()
    for key in ['available', 'percent', 'used', 'free']:
        res['memory'][key] = vm[key]
    return res


def _get_folder_stats(folder_path):
    some_bytes = 0
    files = []
    with os.scandir(folder_path) as dir_contents:
        for entry in dir_contents:
            if entry.is_file():
                fsize = entry.stat().st_size
                some_bytes += fsize
                files.append(dict(fname=entry.name, fsize=fsize))
            elif entry.is_dir():
                 _bytes, _files = _get_folder_stats(entry.path)
                 some_bytes += _bytes
                 files += _files
    return some_bytes, files


def _get_disk_usage(dbpath):
    wal_bytes, wal_files = _get_folder_stats(os.path.join(dbpath, 'sql_logs'))
    bat_bytes, bat_files = _get_folder_stats(os.path.join(dbpath, 'bat'))
    # bat files could be many, so keep just count and total size
    return dict(
            wal = {'bytes': wal_bytes, 'files': wal_files, 'fcount': len(wal_files)},
            bat = {'bytes': bat_bytes, 'fcount': len(bat_files)})


def _pack_info(proc: psutil.Process):
    # 1st time returns 0 always
    proc.cpu_percent()
    with proc.oneshot():
        mem = proc.memory_info()
        # TODO should those be stored in full or just num suffice?
        mmaps = proc.memory_maps()
        net_connections = proc.connections(kind='all')
        open_files = proc.open_files()
        pname = proc.name()
        res = {
            'pid': proc.pid,
            'pname': pname,
            'rss': mem.rss,
            'vms': mem.vms,
            'num_mmaps': len(mmaps),
            'memory_percent': proc.memory_percent(memtype='rss'),
            'cpu_percent': proc.cpu_percent(),  # 2nd time
            'num_fds': proc.num_fds(),
            'num_threads': proc.num_threads(),
            'num_net_connections': len(net_connections),
            'num_open_files': len(open_files),
        }
        if pname == 'mserver5':
            try:
                for opt in proc.cmdline():
                    if '--dbpath' in opt:
                        dbpath = opt.split('=').pop()
                        res['database'] = dbpath.split('/').pop()
                        disk_usage = _get_disk_usage(dbpath) 
                        res['wal'] = disk_usage['wal']
                        res['bat'] = disk_usage['bat']
                        break
            except:
                pass

        return res


def _get_proc_info(processes: List[str])-> List[Optional[Dict]]:
    res = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.is_running() and (proc.info['name'] in processes):
            try:
                res.append(_pack_info(proc))
            except:
                pass
    return res


def _do_monitor(interval, log, processes: List[str]=[]):
    start = datetime.now()
    while True:
        ts = datetime.now()
        event = dict(ts=ts.isoformat(),
                     system=_get_sys_info(), 
                     processes=(_get_proc_info(processes) if processes else []))
        with open(log, 'a') as f:
            print(json.dumps(event), file=f)
        ellapsed = ts - start
        took =  datetime.now() - ts
        if took.seconds < interval:
            sleep(interval - took.seconds)


class Monitor(object):
    def __init__(self, interval=3, log_file=None, processes=['mserver5', 'monetdbd']):
        self.running = False
        self.worker = None
        self.interval = interval
        self.processes = processes
        if log_file:
            if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                raise ValueError(f'{log_file} is not empty')
            with open(log_file, 'w') as f:
                pass
            self.log = log_file
        else:
            date = datetime.now().date()
            fd, self.log = mkstemp(prefix=f'mdbtop-{date}-', suffix='.log', text=True)
            # don't leak fd
            os.close(fd)

    def start(self):
        if not self.running:
            args = (self.interval, self.log)
            kwargs = dict(processes=self.processes)
            self.worker = Process(target=_do_monitor, args=args, kwargs=kwargs)
            self.worker.start()
            self.running = True

    def stop(self):
        if self.running and self.worker:
            self.worker.terminate()
            self.worker.join()
            self.running = False
            self.worker = None

