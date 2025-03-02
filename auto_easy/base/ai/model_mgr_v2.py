import json
import socket
import time
import xmlrpc
import xmlrpc.server
from abc import abstractmethod

from auto_easy.utils import async_thread, cvt_chinese, logger, is_actual_subclass


class AIModelBase:
    def __init__(self, name, rpc_support=True, preload=True):
        self.name = name
        self.inited = False
        self.rpc_support = rpc_support
        self.model_mgr: ModelMgrV2 = None
        self.start_init = False
        if preload:
            async_thread(self._async_init)

    def _async_init(self):
        # 在这里实现异步初始化的通用逻辑
        self.start_init = True
        self.init_model()
        self.inited = True
        logger.debug("init model: {}".format(self.name))

    def wait_model_init(self):
        if not self.start_init:
            async_thread(self._async_init)
        while not self.inited:
            time.sleep(0.1)

    def predict(self, *args, **kwargs):
        # 检查模型是否已初始化，如果未初始化则等待初始化完成
        self.wait_model_init()
        return self.predict(*args, **kwargs)

    def rpc_req_encode(self, *args, **kwargs):
        return args, kwargs

    def rpc_req_decode(self, *args, **kwargs):
        return args, kwargs

    def rpc_resp_decode(self, str_resp):
        return json.loads(str_resp)

    def rpc_resp_encode(self, origin_resp):
        return json.dumps(origin_resp)

    def rpc_server_api(self, *args, **kwargs):
        args, kwargs = self.rpc_req_decode(*args, **kwargs)
        resp = self.predict(*args, **kwargs)
        return self.rpc_resp_encode(resp)

    def rpc_client_call(self, f, *args, **kwargs):
        args, kwargs = self.rpc_req_encode(*args, **kwargs)
        resp = f(*args, **kwargs)
        return self.rpc_resp_decode(resp)

    def rpc_api_name(self):
        name = '{}_{}_predict'.format(self.__class__.__name__, self.name)
        name = cvt_chinese(name)
        return name

    def mock_rpc_call(self, *args, **kwargs):
        return self.rpc_client_call(self.rpc_server_api, *args, **kwargs)

    def use_rpc(self):
        return not self.inited and self.rpc_support and self.model_mgr and self.model_mgr.rpc_client

    def rpc_call(self, *args, **kwargs):
        if not (self.model_mgr and self.model_mgr.rpc_client):
            raise RuntimeError('model_mgr not initialized')
        rpc_func = self.model_mgr.get_rpc_func(self.rpc_api_name())
        return self.rpc_client_call(rpc_func, *args, **kwargs)

    def set_model_mgr(self, model_mgr):
        self.model_mgr = model_mgr

    @abstractmethod
    def init_model(self):
        pass

    @abstractmethod
    def predict(self, *args, **kwargs):
        pass


class ModelMgrV2:
    def __init__(self, models: list[AIModelBase], rpc_server_port=8765):
        self._models = models
        self.rpc_client = None
        self.rpc_server_port = rpc_server_port
        # async_thread(self._init_rpc_client)
        self._init_rpc_client()
        for model in self._models:
            model.set_model_mgr(self)

    def predict(self, name, *args, **kwargs):
        model = self.get_model(name)
        if model is None:
            raise RuntimeError('No such model: {}'.format(name))

        # 本地模型已初始化,直接使用本地模型
        if model.inited:
            return model.predict(*args, **kwargs)

        # 远程rpc客户端已初始化, 直接使用远程客户端
        if self.rpc_client and model.rpc_support:
            return self._rpc_call(name, *args, **kwargs)

        # 使用本地模型, 内部会自动等待完成初始化
        return model.predict(*args, **kwargs)

    def get_models_by_cls(self, cls):
        return [model for model in self._models if is_actual_subclass(model, cls)]

    def get_model(self, name):
        for model in self._models:
            if model.name == name:
                return model
        return None

    def start_rpc_server(self):
        port_usable = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            port_usable = s.connect_ex(('127.0.0.1', self.rpc_server_port)) != 0
        if not port_usable:
            raise RuntimeError('Port {} is not available'.format(self.rpc_server_port))

        def ping():
            return 'pong'

        # # 创建服务器并注册函数
        server = xmlrpc.server.SimpleXMLRPCServer(('127.0.0.1', self.rpc_server_port))
        server.register_function(ping, 'ping')
        for model in self._models:
            server.register_function(model.rpc_server_api, model.rpc_api_name())
        # 启动服务
        server.serve_forever()

    def _init_rpc_client(self):
        try:
            server = xmlrpc.client.ServerProxy('http://127.0.0.1:{}/'.format(self.rpc_server_port))
            if server.ping() == 'pong':
                self.rpc_client = server

        except Exception as e:
            raise e

    def _rpc_call(self, name, *args, **kwargs):
        model = self.get_model(name)
        api_name = model.rpc_api_name()
        rpc_func = getattr(self.rpc_client, api_name)
        return model.rpc_client_call(rpc_func, *args, **kwargs)

    def get_rpc_func(self, api_name):
        rpc_func = getattr(self.rpc_client, api_name)
        return rpc_func
