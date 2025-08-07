import os
from .base_stt import BaseSTT

class FileSTT(BaseSTT):
    def transcribe_from_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} bulunamadı")
        result = self.transcribe(file_path)  # dict dönecek
        return result