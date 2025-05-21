import curses
from .ui import UI
from .window import Window

class Menu(Window[str]):
    
    def __init__(self, ui: UI, title: str, prompt: list[str], options: list[str], last_option_is_exit: bool = False) -> None:

        if 2 <= len(options) <= 10:
            self.options: list[str] = options
        else:
            raise ValueError("Expected at least two options and at most ten.")

        self.has_exit: bool = last_option_is_exit
        super().__init__(ui = ui, title = title, prompt = prompt)
    
    def display(self, selected_option: str | None = None) -> str:
        super().display()
        selected_index = self.options.index(selected_option) if selected_option else 0

        while True:
            for i, option in enumerate(self.options):
                attr = curses.A_REVERSE if i  ==  selected_index else curses.A_NORMAL
                attr = attr | curses.A_DIM if self.has_exit and i  ==  len(self.options) -1 else attr
                self.write(option,i + (4 if self.has_exit and i  ==  len(self.options) - 1 else 3) + len(self.prompt), 2, attr)
            self.refresh()
            key = self.read()
            if key  ==  27 and self.has_exit:
                selected_index = len(self.options) - 1
                key = curses.KEY_ENTER
            if key  ==  curses.KEY_UP:
                selected_index = (selected_index - 1) % len(self.options)
            elif key  ==  curses.KEY_DOWN:
                selected_index = (selected_index + 1) % len(self.options)
            elif key in (curses.KEY_ENTER, ord('\n')):
                return self.options[selected_index]