from __future__ import annotations

import curses
from curses import window as CursesWindow
from curses.panel import update_panels
from functools import reduce
from typing import Generic, Iterator, TypeVar, overload
from .ui import UI
import re

T = TypeVar('T')

class Window(Generic[T]):
    @overload
    def __init__(self, ui: UI, title: str, prompt: list[str]) -> None:
        ...

    @overload
    def __init__(self, ui: UI, title: str, prompt: list[str], height: int, width: int) -> None:
        ...

    @overload
    def __init__(self, ui: UI, title: str, prompt: list[str], height: int, width: int, y: int, x: int) -> None:
        ...

    def __init__(self, ui: UI, title: str, prompt: list[str], height: int | None = None, width: int | None = None, y: int | None = None, x: int | None = None) -> None:
        if height is None or width is None:
            self.__curses_window: CursesWindow = ui.new_window()
            height, width = self.__curses_window.getmaxyx()
            self.is_box: bool = False
        else:
            if x is None or y is None:
                self.__curses_window: CursesWindow = ui.new_window(height = height, width = width)
            else:
                self.__curses_window: CursesWindow = ui.new_window(height = height, width = width, y = y, x = x)
            self.is_box: bool = True
        
        self.__ui: UI = ui
        self.title: str = title
        self.prompt: list[str] = prompt
        self.height: int = height
        self.width: int = width

    def display(self) -> T | None:
        self.clear()
        self.refresh()
        if self.is_box:
            self.__curses_window.box()
        x: int = (self.width - len(self.title)) // 2 if self.is_box else 0
        y: int = 1 if self.is_box else 0
        self.write(self.title, y, x, curses.A_BOLD)
        for i, line in enumerate(self.prompt):
            self.write(line, y+i+2, 2 if self.is_box else 0)
                    
    @overload
    def clear(self):
        ...
    
    @overload
    def clear(self, y: int, start_x: int, end_x: int):
        ...
    
    @overload
    def clear(self, y: int | None = None):
        ...
    
    def clear(self, y: int | None = None, start_x: int | None = None, end_x: int | None = None):
        if y is None:
            self.__curses_window.clear()
            if self.is_box:
                self.__curses_window.box()
        else:
            window_start_x: int = 1 if self.is_box else 0
            window_end_x: int = self.width - (2 if self.is_box else 1)
            start_x = window_start_x if start_x is None else start_x
            end_x = window_end_x if end_x is None else end_x
            clear_length: int = end_x - start_x
            self.__curses_window.addstr(y, start_x, " " * clear_length)
    
    def refresh(self):
        self.__curses_window.refresh()
        update_panels()
        curses.doupdate()

    def close(self):
        (self.__ui.panels[self.__curses_window]).hide()
        self.refresh()

    @classmethod
    def __get_style_replacements(cls, text: str) -> tuple[str, list[tuple[int, str, int]]]:
        matches: Iterator[re.Match[str]] = re.finditer(r'\{\{([ibu]{1,3}):(.*?)\}\}', text)
        
        replacements: list[tuple[int, str, int]] = []
        offset: int = 0

        for match in matches:
            text = text.replace(match.group(0), match.group(2))

            attr: int = 0

            for a in match.group(1):
                match a:
                    case "i":
                        attr |=  curses.A_ITALIC
                    case "b":
                        attr |=  curses.A_BOLD
                    case "u":
                        attr |=  curses.A_UNDERLINE

            replacements.append((match.start(0) - offset, match.group(2), attr))
            offset +=  len(match.group(0)) - len(match.group(2))
        
        return (text, replacements)
    
    def write(self, text: str, y: int, x: int, *attributes: int):
        replacements: list[tuple[int, str, int]]
        text, replacements = self.__get_style_replacements(text)
        attributes_union: int = reduce(lambda a, b: a | b, attributes) if attributes else curses.A_NORMAL
        self.__curses_window.addstr(y, x, text, *attributes)

        for i, r, a in replacements:
            self.__curses_window.addstr(y, x+i, r, attributes_union | a)

    @classmethod
    def write_len(cls, text: str):
        return len(cls.__get_style_replacements(text)[0])

    @overload
    def read(self) -> int:
        ...
    
    @overload
    def read(self, y: int, x: int, max_input_length: int) -> str | None:
        ...

    def read(self, y: int | None = None, x: int | None = None, max_input_length: int = 1) -> int | str | None:

        self.__curses_window.keypad(True)
        self.__curses_window.nodelay(False)

        result: int | str | None = None

        if y is None or x is None or max_input_length  ==  1:
            result = self.__curses_window.getch()
        else:
            result = ""
            while True:
                key: int = self.__curses_window.getch()
                if key  ==  27:
                    result = None
                    break
                elif key in (curses.KEY_ENTER, 10, 13) and result:
                    break
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if len(result) > 0:
                        result = result[:-1]
                    self.__curses_window.addstr(y, x, " " * max_input_length)
                    self.__curses_window.addstr(y, x, result)
                else:
                    if len(result) < max_input_length and 32 <= key <= 126:
                        result +=  chr(key)
                        self.__curses_window.addch(y, x + len(result) - 1, chr(key))
                self.refresh()
        
        self.__curses_window.keypad(False)
        self.__curses_window.nodelay(True)
        return result