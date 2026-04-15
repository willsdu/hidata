import  logging



logger = logging.getLogger(__name__)



class MemoryCompactionHook:
    def __init__(self,memory_manager: "MemoryManager"):
        self.memory_manager = memory_manager