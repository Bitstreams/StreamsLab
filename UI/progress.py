from .ui import UI
from .window import Window
from time import sleep

class ProgressWindow(Window[bool]):
    
    def __init__(self, ui: UI, title: str, *, total: int = 100, key_to_continue: bool = False):
        self.total: int = int(total)
        self.progress: int = 0
        width: int = 60
        height: int = 11 if key_to_continue else 10
        self.bar_width = width - 4
        self.key_to_continue: bool = key_to_continue
        super().__init__(ui, title, [], height, width)

    def display(self):
        super().display()
        self.refresh()

    def update(self, progress: int, info: str):
        self.progress: int = progress
        bar_y = self.height // 2
        filled = int((self.progress / self.total) * self.bar_width)
        filled_part = "▓" * filled
        empty_part = "░" * (self.bar_width - filled)
        bar = filled_part + empty_part
        self.clear(bar_y)
        self.write(bar, bar_y, 2)
        percentage = f"{(self.progress / self.total) * 100:6.2f}%"
        self.clear(bar_y + 2)
        self.write(percentage, bar_y + 2, (self.width - self.write_len(percentage)) // 2)
        self.clear(3)
        self.write(info, 3, (self.width - self.write_len(info)) // 2)
        self.refresh()
        
    def close(self):
        if self.key_to_continue:
            self.write("Press any key to continue...", self.height - 2, 2)
            self.refresh()
            self.read()
        else:
            sleep(1)
        super().close()
