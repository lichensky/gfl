"""Cli module"""
import click

from jira_git_flow import config
from jira_git_flow import types

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.filters import IsDone
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (ConditionalContainer, HSplit,
                                              ScrollOffsets, Window)
from prompt_toolkit.layout.controls import FormattedTextControl, UIControl, UIContent
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.styles import Style


from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.filters import to_filter
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.formatted_text.utils import split_lines, fragment_list_to_text
from prompt_toolkit.utils import get_cwidth

UNCHECKED = '\u25cb '
CHECKED = '\u25cf '
POINTER = ' \u276f '


class DynamicFormattedTextControl(UIControl):
    """
    Control that displays formatted text dynamically. This can be either plain
    text, an :class:`~prompt_toolkit.formatted_text.HTML` object an
    :class:`~prompt_toolkit.formatted_text.ANSI` object or a list of
    ``(style_str, text)`` tuples, depending on how you prefer to do the
    formatting. See ``prompt_toolkit.layout.formatted_text`` for more
    information.

    The get_text is callable which is dynamically returning text to render.
    """
    def __init__(self, get_text, style='', focusable=False, key_bindings=None,
                 show_cursor=False, modal=False, get_cursor_position=None):
        from prompt_toolkit.key_binding.key_bindings import KeyBindingsBase
        assert key_bindings is None or isinstance(key_bindings, KeyBindingsBase)
        assert isinstance(show_cursor, bool)
        assert isinstance(modal, bool)
        assert get_cursor_position is None or callable(get_cursor_position)

        self.get_text = get_text
        self.style = style
        self.focusable = to_filter(focusable)

        self.get_cursor_position = get_cursor_position

        # Key bindings.
        self.key_bindings = key_bindings
        self.show_cursor = show_cursor
        self.modal = modal

        #: Cache for the content.
        self._content_cache = SimpleCache(maxsize=18)
        self._fragment_cache = SimpleCache(maxsize=1)
        # Only cache one fragment list. We don't need the previous item.

        # Render info for the mouse support.
        self._fragments = None

    def reset(self):
        self._fragments = None

    def is_focusable(self):
        return self.focusable()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.get_text())

    def _get_formatted_text_cached(self):
        """
        Get fragments, but only retrieve fragments once during one render run.
        (This function is called several times during one rendering, because
        we also need those for calculating the dimensions.)
        """
        return self._fragment_cache.get(
            get_app().render_counter,
            lambda: to_formatted_text(self.get_text(), self.style))

    def preferred_width(self, max_available_width):
        """
        Return the preferred width for this control.
        That is the width of the longest line.
        """
        text = fragment_list_to_text(self._get_formatted_text_cached())
        line_lengths = [get_cwidth(l) for l in text.split('\n')]
        return max(line_lengths)

    def preferred_height(self, width, max_available_height, wrap_lines, get_line_prefix):
        content = self.create_content(width, None)
        return content.line_count

    def create_content(self, width, height):
        # Get fragments
        fragments_with_mouse_handlers = self._get_formatted_text_cached()
        fragment_lines_with_mouse_handlers = list(split_lines(fragments_with_mouse_handlers))

        # Strip mouse handlers from fragments.
        fragment_lines = [
            [tuple(item[:2]) for item in line]
            for line in fragment_lines_with_mouse_handlers
        ]

        # Keep track of the fragments with mouse handler, for later use in
        # `mouse_handler`.
        self._fragments = fragments_with_mouse_handlers

        cursor_position = self.get_cursor_position()

        # Create content, or take it from the cache.
        key = (tuple(fragments_with_mouse_handlers), width, cursor_position)

        def get_content():
            return UIContent(get_line=lambda i: fragment_lines[i],
                             line_count=len(fragment_lines),
                             cursor_position=cursor_position,
                             show_cursor=self.show_cursor)

        return self._content_cache.get(key, get_content)

    def is_modal(self):
        return self.modal

    def get_key_bindings(self):
        return self.key_bindings


class IssuesController(DynamicFormattedTextControl):
    def __init__(self, message, choices, pointer_index=0):
        self.message = message
        self.pointer_index = pointer_index
        self.answered = False
        self.selected = []
        self._init_choices(choices)
        super(IssuesController, self).__init__(
            self.get_formatted_choices,
            show_cursor=False,
            get_cursor_position=lambda: Point(2, self.pointer_index))

    @property
    def line_count(self):
        return len(self.choices)

    def has_active_choices(self):
        for choice in self.choices:
            if not choice[2]:
                return True
        return False

    def mouse_handler(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            index = mouse_event.position.y
            self.toggle(index)

    def toggle(self, index):
        pointed_choice = self.choices[index][1]
        if pointed_choice in self.selected:
            self.selected.remove(pointed_choice)
        else:
            self.selected.append(pointed_choice)

    def get_formatted_choices(self):
        choices = []
        for i, choice in enumerate(self.choices):
            name = choice[0]
            issue = choice[1]
            selected = (issue in self.selected)
            pointed_at = (i == self.pointer_index)

            if issue.type == types.SUBTASK:
                choices.append(('class:default', '   '))

            if pointed_at:
                choices.append(('class:pointer', POINTER))
            else:
                choices.append(('class:default', '   '))

            if choice[2]:  # disabled
                choices.append(('class:default', '- '))
            else:
                if selected:
                    choices.append(('class:sel_issue', CHECKED))
                else:
                    choices.append(('class:default', UNCHECKED))

            choices.append(render_issue_key(issue))
            choices.append(('class:default', ' %s' % name))
            choices.append(render_badge(issue))
            choices.append(('class:default', '\n'))

        return choices

    def _init_choices(self, choices):
        self.choices = []
        pointer_not_set = True if self.pointer_index == 0 else False

        for i, c in enumerate(choices):
            name = c['name']
            issue = c.get('issue', name)
            disabled = c.get('disabled', None)

            # set pointer on the first available choice
            if pointer_not_set and not disabled:
                self.pointer_index = i
                pointer_not_set = False

            self.choices.append((name, issue, disabled))


def select_issue(choices, pointer_index, msg):
    controller = IssuesController(message='choose issues', choices=choices,
                                  pointer_index=pointer_index)
    if msg is None:
        msg = "Choose issues:"

    def get_prompt():
        prompt = []

        prompt.append(('class:qmark', '?'))
        prompt.append(('class:question', ' %s ' % msg))

        return prompt

    layout = Layout(HSplit([
        Window(height=D.exact(1),
               content=FormattedTextControl(get_prompt(), show_cursor=False)),
        ConditionalContainer(
            Window(
                content=controller,
                width=D.exact(43),
                height=D(min=3),
                scroll_offsets=ScrollOffsets(top=1, bottom=1)
            ),
            filter=~IsDone()
        )
    ]))

    bindings = KeyBindings()

    @bindings.add(Keys.ControlQ, eager=True)
    @bindings.add(Keys.ControlC, eager=True)
    def exit(event):
        event.app.exit(result=[])

    @bindings.add(' ', eager=True)
    def toggle(event):
        controller.toggle(controller.pointer_index)
        event.app.invalidate()

    @bindings.add('j', eager=True)
    @bindings.add(Keys.Down, eager=True)
    def move_cursor_down(event):
        def _next():
            controller.pointer_index = ((controller.pointer_index + 1) % controller.line_count)
            event.app.invalidate()
        _next()
        while controller.choices[controller.pointer_index][2]:
            _next()

    @bindings.add(Keys.Up, eager=True)
    @bindings.add('k', eager=True)
    def move_cursor_up(event):
        def _prev():
            controller.pointer_index = ((controller.pointer_index - 1) % controller.line_count)
            event.app.invalidate()
        _prev()
        while controller.choices[controller.pointer_index][2]:
            _prev()

    @bindings.add(Keys.Enter, eager=True)
    def set_answer(event):
        controller.answered = True
        event.app.exit(result=controller.selected)

    style = Style.from_dict({
        'separator': '#6C6C6C',
        'qmark': '#FF9D00 bold',
        'sel_issue': 'fg:#5Fff9D bg: bold',
        'pointer': '#FF9D00 bold',
        'answer': '#5F819D bold',
        'default': '',
    })

    app = Application(
            layout=layout,
            key_bindings=bindings,
            mouse_support=True,
            style=style,
    )

    if controller.has_active_choices():
        result = app.run()
        return result
    else:
        print_formatted_text(
            FormattedText(controller.get_formatted_choices()),
            style=style)
        return []


def convert_stories_to_choices(stories, filter_function):
    choices = []

    def append(issue):
        choice = {
            'name': issue.summary,
            'issue': issue
        }
        if not filter_function(issue):
            choice['disabled'] = True
        choices.append(choice)

    for story in stories:
        append(story)
        for subtask in story.subtasks:
            append(subtask)

    return choices


def has_active_choices(choices):
    for choice in choices:
        if 'disabled' not in choice:
            return True
    return False


def get_pointer_index(issues, current_issue):
    issue_keys = get_issue_keys(issues)

    if current_issue:
        try:
            return issue_keys.index(current_issue)
        except ValueError:
            pass
    return 0


def get_issue_keys(stories):
    keys = []
    for story in stories:
        keys.append(story.key)
        keys.extend([task.key for task in story.subtasks])
    return keys


def render_issue_key(issue):
    return ('bold', issue.key)


def render_badge(issue):
    badge = config.BADGES[issue.status]['badge']
    color = config.BADGES[issue.status]['color']
    return ('fg: {color} bg:'.format(color=color), ' %s' % badge)


def print_simple_collection(schema, collection, id, exclude=[]):
    for item in collection:
        item_dict = schema.dump(item)

        id_title = id.capitalize()
        print_formatted_text(HTML("<b>%s: </b>%s" % (id_title, item_dict[id])))

        for k, v in item_dict.items():
            if k != id and k not in exclude:
                print_formatted_text(HTML("  <b>%s:</b> %s" % (k.capitalize(), v)))

        if item != collection[-1]:
            print()
