from __future__ import annotations

import curses
from curses import window as CursesWindow
from curses.panel import panel as CursesPanel, new_panel
import logging
from typing import Any, Type, overload
from pyfiglet import Figlet, FigletString

class UI:
    
    def __init__(self, banner: str):
        self.panels: dict[CursesWindow, CursesPanel] = {}
        if 3 <= len(banner) <= 20:
            self.banner: str = banner
        else:
            raise ValueError("Banner argument must be between 3 and 20 characters long")
        
        self.__enter__()
        
    def __enter__(self) -> UI:
        screen: CursesWindow = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.set_escdelay(1)
        screen.keypad(True)

        screen.clear()

        height, width = screen.getmaxyx()

        if width < 160 or height < 25:
            raise RuntimeError("Terminal screen must be at least 25 rows and 160 columns")
        
        attributes: int = curses.A_NORMAL
        lines: list[str]

        if height > 30:
            figlet = Figlet(font = 'banner3', width = 160)
            ascii_art: FigletString = figlet.renderText(self.banner)
            
            lines = ascii_art.splitlines()
        else:
            lines = [self.banner, ""]
            attributes |=  curses.A_BOLD | curses.A_UNDERLINE

        for i, line in enumerate(lines):
            x: int = max(0, (width // 2) - (len(line) // 2))
            if i + 1 < height:
                screen.addstr(i + 1, x, line[:width - x - 1], attributes)
        
        self.start_y: int = len(lines) + 3
        self.start_x: int = 2
        self.end_y: int = height - 2
        self.end_x: int = width - 2

        return self

    def __del__(self):
        self.__exit__(None, None, None)

    def __exit__(self,
                 exc_type: Type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: Any) -> bool:
        
        curses.endwin()

        if exc_type:
            logging.error(exc_value, traceback)
            input()
            return True

        return False
    
    @overload
    def new_window(self) -> CursesWindow:
        ...

    @overload
    def new_window(self, height: int, width: int) -> CursesWindow:
        ...
    
    @overload
    def new_window(self, height: int, width: int, y: int, x: int) -> CursesWindow:
        ...
    
    def new_window(self, height: int | None = None, width: int | None = None, y: int | None = None, x: int | None = None) -> CursesWindow:

        if height is None or width is None:
            height = self.end_y - self.start_y
            width = self.end_x - self.start_x
            y = self.start_y
            x = self.start_x
        elif y is None or x is None:
            y = self.start_y + (self.end_y - self.start_y - height) // 6
            x = self.start_x + (self.end_x - self.start_x - width) // 2

        window: CursesWindow = curses.newwin(height, width, y, x)
        panel: CursesPanel = new_panel(window)
        self.panels[window] = panel

        return window