import re
from datetime import datetime
from optparse import OptionParser
from prometheus_client import start_http_server, Counter, Summary


# line splitting regex for parsing purposes, using digits in date for simplicity
line_re = re.compile(r'(\d{4}/\d\d/\d\d )(\d\d:\d\d:\d\d )(\[\d+\] )(.*)')

# define a dict for fast search, keys are the pid strings
rsync_dict = {}

# We define 3 metrics, duration, size, and request counter
duration_summary = Summary('rsync_tasks_seconds', 'Duration of rsync tasks',
                 ['source', 'dataset'])

size_summary = Summary('rsync_tasks_size', 'Size of rsync tasks',
                 ['source', 'dataset'])    
event_counter = Counter('rsync_requests', 'Number of requests received and ')

class RsyncEvent:
    '''
    A class to represent rsync messages belonging to one pid.

    Attributes
    ----------
    pid : int
        the pid number
    start_date : date
        the date and time when process started
    end_date : date
        the date and time when process ended
    msg : list
        and array with the rsync logs from this pid
    duration:
        duration of an event, it's end_date - start_date

    Methods
    -------
    add_msg(msg=str)
        Adds msg to the messages array of the object
    set_end(date)
        Sets the end of the sync date of the pid (or object)
    set_dataset(name)
        Sets the name of the dataset being processed in teh RsyncEvent
    '''
    def __init__(self, pid, date, msg, source):
        self.pid = pid
        self.start_date = date
        self.msg = []
        self.msg.append(msg)
        self.source = source
        self.dataset = ''
        self.total_size = 0
    
    def add_msg(self, msg):
        self.msg.append(msg)

    def set_end(self, date):
        self.end_date = date
        self.duration = (self.end_date - self.start_date).total_seconds()

    def set_dataset(self, str):
        self.dataset = str


def readlines_then_tail(fin):
    "Iterate through lines and then tail for further lines."
    while True:
        line = fin.readline()
        if line:
            yield line
        else:
            tail(fin)


def tail(fin):
    "Listen for new lines added to file."
    while True:
        where = fin.tell()
        line = fin.readline()
        if not line:
            fin.seek(where)
        else:
            yield line
            
def parser(line):
    line_pcs = line_re.match(line)
    if line_pcs == None:
        print('error parsing line')
        return
    date = line_pcs[1]
    hour = line_pcs[2]
    pid = line_pcs[3].strip()
    msg = line_pcs[4]
    date = datetime.strptime(date + hour.strip(), '%Y/%m/%d %H:%M:%S')
    if pid not in rsync_dict:
        if msg.startswith('connect from'):
            source = msg.split('connect from ')[1]
            new_pid = RsyncEvent(pid, date, msg, source)
            rsync_dict[pid] = new_pid
        else:
            print('Dropping message, not interpretable.', msg)
            return
    obj = rsync_dict[pid]
    obj.add_msg(msg)
    if msg.startswith('rsync on '):
        obj.set_dataset(msg.split('rsync on ')[1].split()[0])
    elif msg.startswith('sent ') or msg.startswith('unknown module '):
        obj.set_end(date)
        if msg.startswith('sent '):
            obj.total_size = int(msg.split('total size ')[1].strip())
        else:
            dataset = msg.split('unknown module ')[1]\
                .split(' tried from')[0]\
                .strip('\'')
            obj.total_size = 0
            obj.set_dataset(dataset)
            obj.set_end(date)
        print(pid, 'duration : ', obj.duration,
        ' , source: ', obj.source, ' , dataset: ', obj.dataset, obj.total_size)
        updateSummary(obj)
        rsync_dict.pop(obj.pid)
        event_counter.inc(1)
    else:
        print('Dropping message, not parsing.')
        return


def updateSummary(obj):
    duration_summary.labels(source=obj.source, dataset=obj.dataset).observe(obj.duration)
    size_summary.labels(source=obj.source, dataset=obj.dataset).observe(obj.total_size)
    return True


def main():
    p = OptionParser("usage: rsyncd_prometheus.py file")
    (options, args) = p.parse_args()
    if len(args) < 1:
        p.error("must specify a file to watch")
    # start Prometheus server, localhost:8080
    start_http_server(8080)
    with open(args[0], 'r') as fin:
        for line in readlines_then_tail(fin):
            parser(line.strip())

if __name__ == '__main__':
    main()
