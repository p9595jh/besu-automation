class Account:
    def __init__(self, p2p_port: int, rpc_http_port: int):
        self.p2p_port: int = p2p_port
        self.rpc_http_port: int = rpc_http_port

    def config(self, attrs):
        for k, v in attrs.items():
            setattr(self, k, v)
