import curses

from .ui import UI
from .window import Window

class YesNoWindow(Window[bool]):
    
    def __init__(self, ui: UI, title: str, prompt: list[str], yes_text: str = "Yes", no_text: str = "No"):
        self.yes_text: str = str(yes_text)
        self.no_text: str = str(no_text)
        max_prompt_width: int = max(self.write_len(line) for line in prompt)
        height: int = len(prompt) + 7
        width: int = max(max_prompt_width + 10, sum([self.write_len(yes_text), self.write_len(no_text), 19]), 30)
        super().__init__(ui = ui, title = title, prompt = prompt, height = height, width = width)

    def display(self) -> bool:
        super().display()

        yes_selected: bool = False
        while True:
            start_x = (self.width - self.write_len(self.yes_text) - self.write_len(self.no_text) - 9) // 2
            self.write(self.yes_text, self.height - 3, start_x, curses.A_REVERSE if yes_selected else curses.A_NORMAL)
            self.write(self.no_text, self.height - 3, start_x + self.write_len(self.yes_text) + 9, (curses.A_REVERSE if not yes_selected else curses.A_NORMAL) | curses.A_DIM)
            self.refresh()

            key = self.read()
            if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                if key  ==  curses.KEY_LEFT or key  ==  curses.KEY_RIGHT:
                    yes_selected = not yes_selected
            elif key in (curses.KEY_ENTER, 10, 13, 27):
                self.close()
                return yes_selected

class OkWindow(Window[None]):
    
    def __init__(self, ui: UI, title: str, prompt: list[str], ok_text: str = "Ok"):
        self.ok_text: str = str(ok_text)
        max_prompt_width: int = max(self.write_len(line) for line in prompt)
        height: int = len(prompt) + 7
        width: int = max(max_prompt_width + 10, sum([self.write_len(ok_text), 19]), 30)
        super().__init__(ui = ui, title = title, prompt = prompt, height = height, width = width)

    def display(self) -> None:
        super().display()

        start_x = (self.width - self.write_len(self.ok_text)) // 2
        self.write(self.ok_text, self.height - 3, start_x, curses.A_REVERSE)
        self.refresh()
        self.read()
        self.close()
