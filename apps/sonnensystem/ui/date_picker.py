"""Date picker popup for simulation date."""

from datetime import datetime, timezone

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput

from ui.theme import Colors, SPACING_MD, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class DatePickerPopup(ModalView):
    """Popup for setting the simulation date."""

    def __init__(self, initial_date: datetime, on_date_set=None, **kwargs):
        super().__init__(
            size_hint=(0.6, 0.2),
            background_color=(0, 0, 0, 0.6),
            **kwargs
        )
        self.on_date_set = on_date_set
        self.current = initial_date

        content = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=SPACING_MD,
            spacing=SPACING_MD,
        )
        with content.canvas.before:
            Color(*Colors.BG_PANEL)
            content._bg = RoundedRectangle(pos=(0, 0), size=(0, 0), radius=[12] * 4)
        content.bind(pos=lambda b, v: setattr(b._bg, "pos", v))
        content.bind(size=lambda b, v: setattr(b._bg, "size", v))

        content.add_widget(
            Label(
                text="Datum wählen",
                font_name=_font(),
                font_size="24sp",
                bold=True,
                color=Colors.TEXT_PRIMARY,
                size_hint_y=None,
                height=40,
            )
        )

        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=MIN_TOUCH_TARGET, spacing=SPACING_MD)
        row.add_widget(Label(text="Tag:", font_name=_font(), font_size="18sp", color=Colors.TEXT_PRIMARY, size_hint_x=None, width=60))
        self.day_in = TextInput(
            text=str(initial_date.day),
            font_name=_font(),
            font_size="20sp",
            foreground_color=Colors.TEXT_PRIMARY,
            background_color=Colors.BG_BUTTON,
            size_hint_x=None,
            width=70,
            multiline=False,
            input_filter="int",
        )
        row.add_widget(self.day_in)
        row.add_widget(Label(text="Monat:", font_name=_font(), font_size="18sp", color=Colors.TEXT_PRIMARY, size_hint_x=None, width=70))
        self.month_in = TextInput(
            text=str(initial_date.month),
            font_name=_font(),
            font_size="20sp",
            foreground_color=Colors.TEXT_PRIMARY,
            background_color=Colors.BG_BUTTON,
            size_hint_x=None,
            width=70,
            multiline=False,
            input_filter="int",
        )
        row.add_widget(self.month_in)
        row.add_widget(Label(text="Jahr:", font_name=_font(), font_size="18sp", color=Colors.TEXT_PRIMARY, size_hint_x=None, width=60))
        self.year_in = TextInput(
            text=str(initial_date.year),
            font_name=_font(),
            font_size="20sp",
            foreground_color=Colors.TEXT_PRIMARY,
            background_color=Colors.BG_BUTTON,
            size_hint_x=None,
            width=100,
            multiline=False,
            input_filter="int",
        )
        row.add_widget(self.year_in)
        content.add_widget(row)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=MIN_TOUCH_TARGET, spacing=SPACING_MD)
        heute_btn = RoundedButton(
            text="Heute",
            font_name=_font(),
            font_size="18sp",
            size_hint_x=0.5,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        heute_btn.bind(on_release=self._set_today)
        btn_row.add_widget(heute_btn)
        setzen_btn = RoundedButton(
            text="Übernehmen",
            font_name=_font(),
            font_size="18sp",
            size_hint_x=0.5,
            background_color=Colors.ACCENT,
            color=Colors.TEXT_PRIMARY,
        )
        setzen_btn.bind(on_release=self._apply)
        btn_row.add_widget(setzen_btn)
        content.add_widget(btn_row)

        self.add_widget(content)

    def _set_today(self, *args):
        now = datetime.now(timezone.utc)
        self.day_in.text = str(now.day)
        self.month_in.text = str(now.month)
        self.year_in.text = str(now.year)

    def _apply(self, *args):
        try:
            d = int(self.day_in.text or 1)
            m = int(self.month_in.text or 1)
            y = int(self.year_in.text or 2025)
            d = max(1, min(31, d))
            m = max(1, min(12, m))
            y = max(1900, min(2100, y))
            new_dt = datetime(y, m, d, 12, 0, 0, tzinfo=timezone.utc)
            if self.on_date_set:
                self.on_date_set(new_dt)
            self.dismiss()
        except (ValueError, TypeError):
            pass
