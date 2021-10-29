p2p_default_port = 30303
rpc_http_default_port = 8545

def valid_path(path):
    if path is None:
        return None
    else:
        if path[-1] == '/':
            return path[:-1]
        else:
            return path

def command_at(path, dir):
    return path + dir
