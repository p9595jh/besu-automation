from ssh_manager import SSHManager
from account import Account
from kill import main as kill_main
from platform import system
import os
import shutil
import json
import yaml
import utils
import time
import sys
import asyncio

workspace = '../work/'
templates = '../templates/'

open_in_terminal = False

def get_command(options, **fields):
    ''' DIR ENODE P2P_PORT RPC_HTTP_PORT '''
    s = '{DIR}/bin/besu ' + ' '.join(options)
    for key, value in fields.items():
        s = s.replace('{%s}' % key, str(value))
    return s

def get_virtual_command(command: str, opsys: str):
    if opsys.startswith('windows'):
        return 'start cmd.exe /c %s' % command
    elif opsys.startswith('linux'):
        return "gnome-terminal -- bash -c '%s'" % command
    elif opsys.startswith('mac'):
        c = command.replace('"', '\\"')
        return """osascript -e 'tell app "Terminal"
                        do script "%s"
                    end tell'""" % command.replace('"', '\\"')
    else:
        # unknown os
        return None

def node_boot(manager: SSHManager, key_folder, directory, opsys, options):
    manager.send_command('rm -rf ' + directory)
    manager.send_command('mkdir ' + directory)
    manager.send_directory(templates + 'bin', directory)
    manager.send_directory(templates + 'lib', directory)
    manager.send_file('networkFiles/genesis.json', directory)

    data_path = '%s/data' % directory
    manager.send_command('mkdir ' + data_path)
    manager.send_file('networkFiles/keys/%s/key' % key_folder, data_path)
    manager.send_file('networkFiles/keys/%s/key.pub' % key_folder, data_path)

    if open_in_terminal:
        cmd = get_command(options, DIR=directory)
        cmd = get_virtual_command(cmd, opsys)
        manager.send_command2(cmd)
    else:
        manager.send_command2(get_command(options, DIR=directory))

async def node_else(key_folder, account: Account, enode, options):
    manager = SSHManager()
    manager.create_ssh_client(account.ip, account.username, account.password)
    manager.send_command('rm -rf ' + account.directory)
    manager.send_command('mkdir ' + account.directory)
    manager.send_directory(templates + 'bin', account.directory)
    manager.send_directory(templates + 'lib', account.directory)
    manager.send_file('networkFiles/genesis.json', account.directory)

    data_path = '%s/data' % account.directory
    manager.send_command('mkdir ' + data_path)
    manager.send_file('networkFiles/keys/%s/key' % key_folder, data_path)
    manager.send_file('networkFiles/keys/%s/key.pub' % key_folder, data_path)

    if open_in_terminal:
        cmd = get_command(options, DIR=account.directory, ENODE=enode, P2P_PORT=account.p2p_port, RPC_HTTP_PORT=account.rpc_http_port)
        cmd = get_virtual_command(cmd, account.os)
        manager.send_command2(cmd)
    else:
        manager.send_command2(get_command(options, DIR=account.directory, ENODE=enode, P2P_PORT=account.p2p_port, RPC_HTTP_PORT=account.rpc_http_port))

    print('configured on `%s:%d`' % (account.ip, account.p2p_port))

def close(manager: SSHManager):
    time.sleep(1)
    manager.close_ssh_client()

async def main():
    needed_commands = [
        'besu'
    ]
    for cmd in needed_commands:
        if shutil.which(cmd) is None:
            print('command `%s` does not exist' % cmd)
            exit(-1)

    accounts: list[Account] = []

    if len(sys.argv) == 1:
        config_path = input('filename to run (default is the first): ')
        try:
            if config_path == '':
                config_path = os.listdir('../configs')[0]
            if not os.path.exists('../configs/' + config_path):
                raise Exception
        except Exception:
            print('`%s` not exists' % config_path)
            exit(-1)
    else:
        config_path = sys.argv[1]

    print('run `%s`' % config_path)

    with open('../configs/' + config_path, 'r', encoding='utf8') as f:
        config = (json.load(f) if config_path[-4:].lower() == 'json' else yaml.load(f, Loader=yaml.FullLoader))
        for i, attrs in enumerate(config['accounts']):
            account = Account(p2p_port=utils.p2p_default_port + i, rpc_http_port=utils.rpc_http_default_port + i)
            account.config(attrs)
            account.directory = utils.valid_path(account.directory)
            accounts.append(account)

    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    
    os.mkdir(workspace)
    shutil.copy(templates + 'ibftConfig.json', workspace + 'ibftConfig.json')

    os.chdir(workspace)
    os.mkdir('networkFiles')
    os.system('besu operator generate-blockchain-config --config-file=ibftConfig.json --to=networkFiles --private-key-file-name=key')

    keys = os.listdir('networkFiles/keys')
    with open('networkFiles/keys/%s/key.pub' % keys[0], 'r') as f:
        line = f.readline()
        enode = 'enode://%s@%s:%d' % (line[2:], accounts[0].ip, accounts[0].p2p_port)

    boot_manager = SSHManager()
    boot_manager.create_ssh_client(accounts[0].ip, accounts[0].username, accounts[0].password)
    node_boot(boot_manager, keys[0], accounts[0].directory, account.os, config['options_boot'])
    print('configured boot node on `%s:%d`' % (accounts[0].ip, accounts[0].p2p_port))

    await asyncio.sleep(3)

    futures = [asyncio.ensure_future(node_else(keys[i], accounts[i], enode, config['options_else'])) for i in range(1, len(keys))]

    await asyncio.gather(*futures)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # try:
    #     loop.run_forever()
    # except KeyboardInterrupt:
    #     pass
    loop.close()
