"""Константи та бізнес-ліміти застосунку."""

API_PREFIX = "/api/v1"
ASYNC_DRIVER = "postgresql+asyncpg"
PLATFORM_TELEGRAM = "telegram"
PLATFORM_TIMEOUT_SECONDS = 10.0
MAX_MESSAGE_LENGTH = 4000
DISPLAY_NAME_MAX_LENGTH = 100

BOOK_TITLE_MAX_LENGTH = 200
BOOK_AUTHOR_MAX_LENGTH = 120
BOOK_NOTE_MAX_LENGTH = 1000
BOOK_MIN_PAGES = 1
BOOK_MAX_PAGES = 10000
LIST_PAGE_SIZE = 10

STATUS_PLANNED = "planned"
STATUS_READING = "reading"
STATUS_FINISHED = "finished"
DEFAULT_STATUS = STATUS_PLANNED
STATUS_LABELS = {
    STATUS_PLANNED: "заплановано",
    STATUS_READING: "читаю",
    STATUS_FINISHED: "прочитано",
}
STATUS_ALIASES = {
    "planned": STATUS_PLANNED,
    "заплановано": STATUS_PLANNED,
    "планую": STATUS_PLANNED,
    "reading": STATUS_READING,
    "читаю": STATUS_READING,
    "finished": STATUS_FINISHED,
    "прочитано": STATUS_FINISHED,
    "завершено": STATUS_FINISHED,
}

FIELD_TITLE = "title"
FIELD_AUTHOR = "author"
FIELD_PAGES = "pages"
FIELD_STATUS = "status"
FIELD_NOTE = "note"
FIELD_ALIASES = {
    "title": FIELD_TITLE,
    "назва": FIELD_TITLE,
    "author": FIELD_AUTHOR,
    "автор": FIELD_AUTHOR,
    "pages": FIELD_PAGES,
    "сторінки": FIELD_PAGES,
    "status": FIELD_STATUS,
    "статус": FIELD_STATUS,
    "note": FIELD_NOTE,
    "нотатка": FIELD_NOTE,
}
CLEAR_NOTE_MARKER = "-"

CMD_START = "start"
CMD_HELP = "help"
CMD_ADD = "add"
CMD_LIST = "list"
CMD_BOOK = "book"
CMD_UPDATE = "update"
CMD_DELETE = "delete"
CMD_CANCEL = "cancel"
CMD_STATS = "stats"
COMMANDS_ALLOWED_IN_DIALOG = frozenset({CMD_START, CMD_HELP, CMD_CANCEL})

DIALOG_FLOW_ADD_BOOK = "add_book"
STEP_TITLE = "title"
STEP_AUTHOR = "author"
STEP_PAGES = "pages"
STEP_CONFIRM = "confirm"
NEXT_STEP = {
    STEP_TITLE: STEP_AUTHOR,
    STEP_AUTHOR: STEP_PAGES,
    STEP_PAGES: STEP_CONFIRM,
}
YES_ANSWERS = frozenset({"так", "т", "yes", "y", "+"})
NO_ANSWERS = frozenset({"ні", "н", "no", "n", "-"})
