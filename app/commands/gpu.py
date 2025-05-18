from systems.commands.index import Command
from utility.nvidia import Nvidia


class Gpu(Command("gpu")):
    def exec(self):
        nvidia = Nvidia(self)

        self.sh("nvidia-smi")

        for device_index in range(nvidia.device_count):
            device = nvidia.get_device_info(device_index)
            device_info = device.export()
            device_info.pop("name")

            self.data(device.name, device_info, "gpu_info")
