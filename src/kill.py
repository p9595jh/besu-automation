from account import Account
from ssh_manager import SSHManager
import os
import json
import utils
import yaml
import sys

def main():

    if len(sys.argv) == 1:
        conf = input('used config file: ')
        try:
            if conf == '':
                conf = os.listdir('../configs')[0]
            if not os.path.exists('../configs/' + conf):
                raise Exception
        except Exception:
            print('`%s` not exists' % conf)
            exit(-1)
    else:
        conf = sys.argv[1]

    PID_index = 8
    accounts: list[Account] = []
    with open('../configs/' + conf, 'r', encoding='utf8') as f:
        content = (json.load(f) if conf[-4:].lower() == 'json' else yaml.load(f, Loader=yaml.FullLoader))
        for i, attrs in enumerate(content['accounts']):
            account = Account(p2p_port=utils.p2p_default_port + i, rpc_http_port=utils.rpc_http_default_port + i)
            account.config(attrs)
            account.directory = utils.valid_path(account.directory)
            accounts.append(account)

    for account in accounts:
        manager = SSHManager()
        manager.create_ssh_client(account.ip, account.username, account.password)
        res = manager.send_command("netstat -anvp tcp | awk 'NR<3 || /LISTEN/' | grep " + str(account.p2p_port))
        items = []
        if len(res) == 0:
            print('no item to kill in `%s:%d`' % (account.ip, account.p2p_port))
            continue
        for s in res[0].strip().split(' '):
            s = s.strip()
            if s != '':
                items.append(s)
        manager.send_command('kill -9 ' + items[PID_index])
        manager.close_ssh_client()
        print('`%s:%d` killed' % (account.ip, account.p2p_port))

if __name__ == '__main__':
    main()
