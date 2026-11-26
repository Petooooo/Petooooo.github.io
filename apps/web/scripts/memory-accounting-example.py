#!/usr/bin/env python3
"""Measure a single 4 MiB shared mapping in two processes; no pressure test."""
import os,mmap,re,json
from pathlib import Path
SIZE=4*1024*1024
NAME='portfolio-memory-accounting-example'
def measure(pid):
    s=Path(f'/proc/{pid}/smaps').read_text()
    chunks=re.split(r'(?m)(?=^[0-9a-f]+-[0-9a-f]+ )',s)
    matches=[c for c in chunks if c and '/memfd:'+NAME in c.splitlines()[0]] if s else []
    assert len(matches)==1,(pid,len(matches))
    fields=dict((k,int(v)) for k,v in re.findall(r'(?m)^([A-Za-z_]+):\s+(\d+)\s+kB$',matches[0]))
    return {k:fields[k] for k in ('Size','Rss','Pss','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty')}
def run():
    fd=os.memfd_create(NAME,os.MFD_CLOEXEC);os.ftruncate(fd,SIZE)
    m=mmap.mmap(fd,SIZE,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ|mmap.PROT_WRITE)
    page=os.sysconf('SC_PAGE_SIZE')
    for i in range(0,SIZE,page):m[i]=1
    ready_r,ready_w=os.pipe();stop_r,stop_w=os.pipe()
    pid=os.fork()
    if pid==0:
        try:
            os.close(ready_r);os.close(stop_w)
            assert sum(m[i] for i in range(0,SIZE,page))==SIZE//page
            os.write(ready_w,b'1');os.close(ready_w)
            os.read(stop_r,1)
            os._exit(0)
        except BaseException:os._exit(1)
    os.close(ready_w);os.close(stop_r)
    try:
        assert os.read(ready_r,1)==b'1'
        a,b=measure(os.getpid()),measure(pid)
        for v in (a,b):
            assert v['Size']==v['Rss']==4096,v
            assert abs(v['Pss']-2048)<=4,v
            assert v['Private_Clean']+v['Private_Dirty']==0,v
        result={'parent':a,'child':b,'page_bytes':page,'rss_sum_kib':a['Rss']+b['Rss'],'pss_sum_kib':a['Pss']+b['Pss']}
        print(json.dumps(result))
    finally:
        os.close(ready_r);os.close(stop_w)
        _,status=os.waitpid(pid,0);m.close();os.close(fd)
        assert status==0,status
    return result
if __name__=='__main__':run()
