import json
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout

from weather import WeatherService


class DashboardRoot(FloatLayout):
    time_text = StringProperty("--:--:--")
    date_text = StringProperty("----------")
    weather_text = StringProperty("Sää: (ei haettu vielä)")
    calendar_text = StringProperty("Kalenteri: (placeholder)")
    shopping_text = StringProperty("Ostoslista:\n- maito\n- kahvi\n- banaani")
    debug_mode = BooleanProperty(False)

    screensaver_active = BooleanProperty(False)

    def __init__(self, config: dict, **kwargs):
        super().__init__(**kwargs)
        self.config_data = config
        self.debug_mode = bool(config.get("debug", False))
        self.weather = WeatherService(config)

        # Kellot
        Clock.schedule_interval(self._tick_clock, 1.0)
        Clock.schedule_once(lambda *_: self._update_all(), 0.2)

        # Sää päivitys
        weather_minutes = int(config.get("weather_update_minutes", 30))
        Clock.schedule_interval(lambda *_: self._update_weather(), weather_minutes * 60)

        # Screensaver idle
        self._idle_seconds = float(config.get("screensaver_seconds", 30))
        self._idle_ev = None

        # Tärkeä: bindaa kosketukset koko ikkunaan
        Window.bind(on_touch_down=self._on_any_input)

        # Käynnistä idle laskuri
        Clock.schedule_once(lambda *_: self._reset_idle_timer(), 0)

    def _tick_clock(self, _dt):
        now = datetime.now()
        self.time_text = now.strftime("%H:%M:%S")
        self.date_text = now.strftime("%a %d.%m.%Y")

        # Päivitä screensaverin iso kello jos se on päällä
        if self.screensaver_active:
            try:
                self.ids.screensaver.ids.bigclock.text = now.strftime("%H:%M")
            except Exception:
                pass

    # -------- Screensaver-metodit --------
    def _reset_idle_timer(self):
        if self._idle_ev is not None:
            self._idle_ev.cancel()
        self._idle_ev = Clock.schedule_once(self._activate_screensaver, self._idle_seconds)

    def _activate_screensaver(self, _dt):
        self.screensaver_active = True
        ss = self.ids.screensaver
        ss.disabled = False
        ss.opacity = 1

        # Päivitä teksti heti
        now = datetime.now()
        try:
            ss.ids.bigclock.text = now.strftime("%H:%M")
        except Exception:
            pass

    def _deactivate_screensaver(self):
        self.screensaver_active = False
        ss = self.ids.screensaver
        ss.opacity = 0
        ss.disabled = True

    def _on_any_input(self, _window, touch):
        # Jos screensaver päällä: sulje se ja syö tämä kosketus (ei vahinkopainallusta nappiin)
        if self.screensaver_active:
            self._deactivate_screensaver()
            self._reset_idle_timer()
            return True

        # Muuten vain nollaa idle
        self._reset_idle_timer()
        return False

    # -------- Data-päivitykset --------
    def _update_all(self):
        self._update_weather()
        # self._update_calendar()
        # self._update_shopping()

    def _update_weather(self):
        try:
            self.weather_text = self.weather.get_weather_summary()
        except Exception as e:
            self.weather_text = f"Sää: virhe ({e.__class__.__name__})"

    def on_send_shopping(self):
        # Turvallinen placeholder ettei kaadu testissä
        self.shopping_text = self.shopping_text + "\n\n(placeholder: ei vielä käytössä)"

    def toggle_fullscreen(self):
        Window.fullscreen = not bool(Window.fullscreen)
        Window.borderless = bool(Window.fullscreen)


class KotiDashboardApp(App):
    def build(self):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        if config.get("fullscreen", False):
            Window.fullscreen = True
            Window.borderless = True
        else:
            Window.fullscreen = False
            Window.borderless = False

        Builder.load_file("ui/dashboard_V1.kv")
        return DashboardRoot(config)


if __name__ == "__main__":
    KotiDashboardApp().run()