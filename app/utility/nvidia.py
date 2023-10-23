from .data import Collection

import pynvml


class NvidiaError(Exception):
    pass


class Nvidia(object):

    def __init__(self, command):
        self.command = command

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


    def select_device(self, max_vram): # MB
        def get_device():
            if max_vram:
                for device_index in range(self.device_count):
                    device_info = self.get_device_info(device_index)
                    if max_vram < device_info.free_memory:
                        return "cuda:{}".format(device_index)

                raise NvidiaError("No CUDA device available (out of memory)")
            return None

        return self.command.run_exclusive('nvidia_device_selector', get_device)
