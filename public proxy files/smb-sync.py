#!/usr/bin/python3

import os, pickle, pathlib

os.chdir('html')

local_dir = 'images'
smb_share = '//xxx.xxx.xxx.xxx/sambashare'
records_filename = '../fileshare_records'

def do_smbclient_cmd(cmd):
    smbclient_cmd = f"smbclient '{smb_share}' -N -c 'prompt OFF; {cmd}'"
    cmd_proc = os.popen(smbclient_cmd)
    output = cmd_proc.read()
    retcode = cmd_proc.close()
    return (output,retcode)

# path argument is the remote path
def get_remote_file(path):
    here_path = path.replace('\\','/')
    cmd = f'get "{path}" "{local_dir}/{here_path}"'
    do_smbclient_cmd(cmd)

def parse_file_line(line):
    if line[0:2] != '  ':
        raise ValueError(f'bad listing line: {line}')
    line = line[2:]
    filemodtime = line[-24:]
    line = line[:-24]
    if not filemodtime[0:3] in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
        raise ValueError(f'bad listing line: {line}')
    line = line.rstrip()
    line = line[-1::-1] #reverse the string
    bits = line.split(None,2)
    filename = (bits[2][-1::-1]).rstrip()
    fileflags = bits[1]
    filesize = bits[0][-1::-1]
    filetype = 'D' if 'D' in fileflags else 'F'
    return (filename,filetype,filesize,filemodtime)

def full_update():
    # get a listing of the file share
    cmd = f'recurse ON; dir'
    dir_listing,retcode = do_smbclient_cmd(cmd)
    if retcode != None:
        return
    lines = dir_listing.split('\n')
    remote_files = {}
    current_prefix = ''
    for l in lines:
        if l.strip() == "":
            continue
        if l[0] == '\\':
            current_prefix = l.strip()
            continue
        try:
            filename,filetype,filesize,filemodtime = parse_file_line(l)
        except ValueError:
            continue
        if filename in ['.','..']:
            continue
        remote_files[current_prefix+'\\'+filename] = (filename,filetype,filesize,filemodtime)

    # get a listing of the local directory
    local_files = {}
    for root,dirs,files in os.walk(local_dir):
        for d in dirs:
            local_files[os.path.normpath(root+'/'+d)] = (d,'D')
        for f in files:
            local_files[os.path.normpath(root+'/'+f)] = (f,'F')

    # pull in saved records, NB keys are *remote* paths
    if os.path.isfile(records_filename):
        fh = open(records_filename,'rb')
        old_file_records = pickle.load(fh)
        fh.close()
    else:
        old_file_records = {}

    # walk the local directory and update it by deleting or refreshing files
    dirs_to_remove = []
    for local_path in local_files:
        filename,filetype = local_files[local_path]
        local_sub_path = local_path.split('/',1)[1]
        remote_path = '\\'+local_sub_path.replace('/','\\')

        # if the file is not present on the remote server (or the very unlikely
        # event that it has changed type), remove it
        if (not remote_path in remote_files) or (filetype != remote_files[remote_path][1]):
            if filetype == 'F':
                os.unlink(local_path)
            if filetype == 'D':
                dirs_to_remove.append(local_path)
            continue

        # if this is a directory then we are done
        if filetype == 'D':
            continue

        # if the file is present on the remote server but either the file
        # has been modified since our last record of it, or we don't have
        # a record of it, refresh the file
        file_rec = remote_files[remote_path]
        refresh_file = False
        if not remote_path in old_file_records:
            refresh_file = True
        else:
            old_file_rec = old_file_records[remote_path]
            old_sig = old_file_rec[2]+old_file_rec[3]
            new_sig = file_rec[2]+file_rec[3]
            if old_sig != new_sig:
                refresh_file = True
        if refresh_file:
            get_remote_file(remote_path)

    # remove old directories
    while dirs_to_remove != []:
        d = dirs_to_remove[0]
        try:
            os.rmdir(d)
            dirs_to_remove.remove(d)
        except:
            dirs_to_remove.remove(d)
            dirs_to_remove.append(d)

    # copy over new files
    for remote_path in remote_files:
        local_path = local_dir+'/'+remote_path.replace('\\','/')
        if os.path.exists(local_path):
            continue
        filetype = remote_files[remote_path][1]
        if filetype == 'D':
            pathlib.Path(local_path).mkdir(parents=True)
            continue
        if filetype == 'F':
            parent_dir = os.path.dirname(local_path)
            pathlib.Path(parent_dir).mkdir(exist_ok=True,parents=True)
            get_remote_file(remote_path)

    fh = open(records_filename,'wb')
    pickle.dump(remote_files,fh,protocol=pickle.HIGHEST_PROTOCOL)
    fh.flush()
    fh.close()


full_update()
            

