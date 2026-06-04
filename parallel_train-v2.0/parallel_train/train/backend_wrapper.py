from typing import List, Dict
from .train.backend import Backend, BackendConfig, EncodedData
from .train.worker_group import WorkerGroup


class BackendTaskWrapper(object):
    def prepare_data(self, data_param):
        """Logic for prepare data."""
        pass

    def train(self, model_params):
        """Logic for prepare data."""
        pass


class BackendWrapper(Backend):
    def prepare_data(self, data_param):
        """Logic for prepare data."""
        pass

    def train(self, model_params):
        """Logic for prepare data."""
        pass

    def on_start(self, worker_group: WorkerGroup,
                 backend_config: BackendConfig):
        """Logic for starting this backend."""
        pass

    def on_shutdown(self, worker_group: WorkerGroup,
                    backend_config: BackendConfig):
        """Logic for shutting down the backend."""
        pass

    def handle_failure(self, worker_group: WorkerGroup,
                       failed_worker_indexes: List[int],
                       backend_config: BackendConfig):
        """Logic for handling failures.

        By default, restart all workers.
        """
        worker_group.shutdown()
        worker_group.start()
        self.on_start(worker_group, backend_config)

    @staticmethod
    def encode_data(data_dict: Dict) -> EncodedData:
        """Logic to encode a data dict before sending to the driver.

        This function will be called on the workers for any data that is
        sent to the driver via ``train.report()`` or
        ``train.save_checkpoint()``.
        """

        return data_dict

    @staticmethod
    def decode_data(encoded_data: EncodedData) -> Dict:
        """Logic to decode an encoded data dict.

        This function will be called on the driver after receiving the
        encoded data dict from the worker.
        """

        return encoded_data


class BackendConfigWrapper(BackendConfig):
    """Parent class for configurations of training backend."""

    @property
    def backend_cls(self):
        raise NotImplementedError