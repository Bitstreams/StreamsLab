from __future__ import annotations

import curses

from typing import Any, Callable, Generic, Type, TypeVar, overload
from .ui import UI
from .window import Window

T = TypeVar('T')

class Input(Generic[T]):
    def __init__(self, prompt: str, type: Type[T], is_valid: Callable[[T], bool], validation_message: str):
        self.prompt: str = str(prompt)
        self.type: Type[T] = type
        self.is_valid: Callable[[T], bool] = is_valid
        self.validation_message: str = str(validation_message)

    @property
    def value(self) -> T:
        return self._value
    @value.setter
    def value(self, new_value: Any) -> None:

        try:
            converted_value: T = self.type(new_value) # type: ignore
        except:        
            raise TypeError(f"Invalid value type for {self.prompt.lower()}")
        
        if self.is_valid(converted_value):
            self._value: T = converted_value
        else:
            raise ValueError(f"Invalid value for {self.prompt.lower()}")

class InputWindow(Window[dict[str, Input[T]]]):

    @overload
    def __init__(self, ui: UI, title: str, prompt: list[str], inputs: dict[str, Input]):
        ...

    @overload
    def __init__(self, ui: UI, title: str, prompt: list[str], inputs: dict[str, Input], confirm_inputs_text: str, cancel_inputs_text: str):
        ...

    def __init__(self, ui: UI, title: str, prompt: list[str], inputs: dict[str, Input], confirm_inputs_text: str | None = None, cancel_inputs_text: str | None = None):
        self.inputs: dict[str, Input] = inputs
        max_prompt_width: int = max(self.write_len(line) + 2 for line in prompt)
        max_input_description_width = max([self.write_len(self.inputs[k].validation_message) for k in self.inputs])

        width: int = max(max_prompt_width + 10, max_input_description_width + 10, 30)
        height: int = len(prompt) + len(self.inputs) + 8

        self.confirm_inputs_text: str | None = confirm_inputs_text
        self.cancel_inputs_text: str | None = cancel_inputs_text

        super().__init__(ui = ui, title = title, prompt = prompt, height = height, width = width)
    
    def display(self) -> dict[str, Input[T]] | None:
        super().display()


        pair_number = curses.pair_number(0)
        fg_color, bg_color = curses.pair_content(pair_number)
        curses.init_pair(1, curses.COLOR_RED, bg_color)
        
        for i, key in enumerate(self.inputs):
            error: str = ""
            while True:
                input: Input = self.inputs[key]
                prompt_line = len(self.prompt) + 4 + i
                self.clear(y = prompt_line)
                prompt_text = f"{input.prompt}: "
                self.write(prompt_text, prompt_line, 4)
                self.clear(self.height - 3)
                if error:
                    self.write(error, self.height - 3, 2, curses.color_pair(1))                
                self.clear(self.height - 2)
                self.write(input.validation_message, self.height - 2, 2, curses.A_DIM if not error else curses.color_pair(1))
                
                user_input = self.read(prompt_line, self.write_len(prompt_text) + 4, 16)
                if not user_input:
                    self.close()
                    return None
                try:
                    input.value = user_input
                    break
                except (ValueError, TypeError) as e:
                    error = e.args[0]

        if self.confirm_inputs_text and self.cancel_inputs_text:

            self.clear(self.height - 3)
            self.clear(self.height - 2)
            confirmed: bool = False
            while True:
                start_x = (self.width - self.write_len(self.confirm_inputs_text) - self.write_len(self.cancel_inputs_text) - 9) // 2
                self.write(self.confirm_inputs_text, self.height - 3, start_x, curses.A_REVERSE if confirmed else curses.A_NORMAL)
                self.write(self.cancel_inputs_text, self.height - 3, start_x + self.write_len(self.confirm_inputs_text) + 9, (curses.A_REVERSE if not confirmed else curses.A_NORMAL) | curses.A_DIM)
                self.refresh()

                key = self.read()
                if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                    if key  ==  curses.KEY_LEFT or key  ==  curses.KEY_RIGHT:
                        confirmed = not confirmed
                elif key in (curses.KEY_ENTER, 10, 13, 27):
                    self.close()
                    return self.inputs if confirmed else None
        
        else:
            return self.inputs