import sys
from collections import OrderedDict
from typing import Callable, Optional

from orpheus.services import brain, CLIEvent


class MenuScreen:
    def __init__(self, title: str):
        self.title = title
        self.options = OrderedDict()

    def option(self, key: str, description: str, handler: Callable[[], Optional['MenuScreen']]):
        self.options[key] = (description, handler)


class InteractiveMenu:
    def __init__(self):
        self.root: Optional[MenuScreen] = None
        self.stack: list[MenuScreen] = []

    def set_root(self, screen: MenuScreen):
        self.root = screen
        brain.record_event(CLIEvent(command='register_menu', metadata={'key': 'root', 'description': screen.title}))

    def push(self, screen: MenuScreen):
        self.stack.append(screen)
        brain.record_event(CLIEvent(command='push_menu', metadata={'title': screen.title}))

    def pop(self):
        if len(self.stack) > 1:
            popped = self.stack.pop()
            brain.record_event(CLIEvent(command='pop_menu', metadata={'title': popped.title}))

    def create_screen(self, title: str) -> MenuScreen:
        return MenuScreen(title)

    def register(self, key: str, description: str, handler: Callable[[], Optional[MenuScreen]]):
        if not self.root:
            raise RuntimeError('Root menu not set')
        self.root.option(key, description, handler)

    def run(self):
        if not self.root:
            print('No menu registered.')
            return
        if not self.stack:
            self.push(self.root)

        while self.stack:
            screen = self.stack[-1]
            print(f"=== {screen.title} ===")
            for key, (description, _) in screen.options.items():
                print(f'[{key}] {description}')
            if len(self.stack) > 1:
                print('[b] Back')
            print('[q] Quit menu')

            try:
                choice = input('Select option: ').strip().lower()
            except EOFError:
                print('\nExiting menu.')
                break
            if choice == 'q':
                break
            if choice == 'b' and len(self.stack) > 1:
                self.pop()
                continue
            handler_entry = screen.options.get(choice)
            if not handler_entry:
                print('Invalid option.')
                continue
            _, handler = handler_entry
            try:
                result = handler()
                if isinstance(result, MenuScreen):
                    self.push(result)
            except SystemExit:
                raise
            except Exception as exc:
                print(f'Option failed: {exc}')


menu = InteractiveMenu()
