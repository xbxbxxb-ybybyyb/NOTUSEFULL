# coding=utf-8

from ht_dubbo_client.rpclib import DubboClient
import time
import uuid
from ht_dubbo_client.htjsonrpc import Server as JsonRpcClient, JsonClientError, TransportError
from ht_dubbo_client.rpcerror import ConnectionFail, dubbo_client_errors, InternalError, DubboClientError
from ht_dubbo_client.kafkaQueue import KafkaThread
import socket
import logging
from ht_dubbo_client.compatibility import HTTPError


logger = logging.getLogger(__name__)


class DirectDubboClient(DubboClient):
    """
    ht client
    """

    def __init__(self, interface, registry, direct_dubbo_location, **kwargs):
        super(DirectDubboClient, self).__init__(interface, registry, **kwargs)
        self._zk_cli = registry
        self._kafka = self._zk_cli.kafka_producer
        self.interface = interface
        self.provider_path = None
        self.trace_id = None
        self.kafka_message_list = KafkaThread.buffer_queue
        self.kafka_status = KafkaThread.send_status
        self.direct_dubbo_location = direct_dubbo_location

    def __getattr__(self, method):
        self.trace_id = str(uuid.uuid1())
        start_time = (int(round((time.time()) * 1000)))
        func = DubboClient.__getattr__(self, method)

        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                self.send_2_kafka(method, start_time, True)
            except Exception:
                self.send_2_kafka(method, start_time, False)
                raise
            else:
                pass
            return result

        return wrapper

    def send_2_kafka(self, method, start_time, call_status):
        """
        call kafka client
        :param method: string, method name
        :param start_time: timestamp, call start time
        :param call_status: bool, call fails or succeeds
        """
        try:
            end_time = (int(round((time.time()) * 1000)))
            message_to_send = self._format_message(method, start_time, end_time, call_status)
            self.send_buffer(message_to_send)
        except Exception as error:
            logger.warning("SENT TO KAFKA FAILED!e: {0}".format(str(error)))

    def send_buffer(self, msg):
        """
        put info into buffer
        :param msg: kafka message
        :return: none
        """
        if KafkaThread.send_status:
            try:
                self.kafka_message_list.put_nowait(msg)
            except Exception as err:
                logger.warning("FAIL TO ADD TO KAFKA BUFFER! e: {0}".format(str(err)))
                KafkaThread.fail_times += 1
            if KafkaThread.fail_times > KafkaThread.FAIL_TIMES_MAX:
                logger.warning("PLEASE CHECK KAFKA! TOO MANY RPC INFO LOST")

    def _format_message(self, method_name, start_time, end_time, status):
        """
        kafka topic value
        :param method_name: method name of provider
        :param start_time: call start time
        :param end_time: call finish time
        :param status: call fails or succeeds?
        :return: {}
        """
        consumer_host = socket.gethostbyname(socket.gethostname())
        app_name = self._zk_cli.consumer_app
        ports = '' if self.provider_path is None else self.provider_path.split(':')[1]
        provider_host = '' if self.provider_path is None else self.provider_path.split(':')[0]
        return {"traceId": self.trace_id, "consumerHost": consumer_host, "initial": True, "appName": app_name,
                "consumerPort": 0, "serviceGroup": '', "methodName": method_name, "serviceName": self.interface,
                "providerPort": ports, "protocol": "jsonrpc", "chainId": 0, "providerHost": provider_host,
                "startTime": start_time, "endTime": end_time, "success": status, "consumerSide": True,
                "serviceVersion": self.version
                }

    def call(self, method, *args, **kwargs):
        """
        override DubboClient method to get provider path and insert trace info into header
        :param method: method name
        :param args:
        :param kwargs:
        :return:
        """
        provider = self.registry.get_random_provider(self.interface, version=self.version, group=self.group)
        self.provider_path = self.direct_dubbo_location#provider.location
        logger.debug('print provider---> %s, %s, %s, %s, %s' % (self.direct_dubbo_location, provider.path, method, args, kwargs))
        client = JsonRpcClient("http://{0}{1}".format(self.direct_dubbo_location, provider.path),
                               headers={"TraceId": self.trace_id, "ChainId": "0"}
                               )
        try:
            return client.call(method, *args, **kwargs)
        except HTTPError as e:
            raise ConnectionFail(None, e.filename)
        except (JsonClientError, TransportError) as error:
            if error.code in dubbo_client_errors:
                raise dubbo_client_errors[error.code](message=error.message, data=error.data)
            else:
                raise DubboClientError(code=error.code, message=error.message, data=error.data)
        except Exception as ue:
            if hasattr(ue, 'reason'):
                raise InternalError(str(ue), ue.reason)
            else:
                raise InternalError(str(ue), None)
