from .data import Collection

import pynvml


class NvidiaError(Exception):
    pass


class Nvidia(object):

    def __init__(self):
        self._device_count = pynvml.nvmlDeviceGetCount()

    @property
    def device_count(self):
        return self._device_count


    def get_device_info(self, index):
        if isinstance(index, str):
            index = int(index.removeprefix('cuda:'))

        if index >= self.device_count:
            raise NvidiaError("CUDA device {} does not exist".format(index))

        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
        mb_bytes = (1024 ** 2)

        return Collection(
            driver_version = pynvml.nvmlSystemGetDriverVersion(),
            name = pynvml.nvmlDeviceGetName(handle),
            index = index,
            total_memory = int(memory.total / mb_bytes),
            free_memory = int(memory.free / mb_bytes),
            used_memory = int(memory.used / mb_bytes)
        )
