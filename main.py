"""
Wenner Soil Resistivity Calculator
-----------------------------------
Input: electrode spacing (a) and two measurement pairs (V, I) per spacing,
following the four-electrode Wenner method used in earth resistivity testing.

Formula per measurement:
    R   = V / I                      (V in mV, I in mA -> R in ohms)
    rho = 2 * pi * a * R             (apparent resistivity, ohm-meters)

rho_avg for a spacing = average(rho_measurement_1, rho_measurement_2)

The apparent resistivity at spacing 'a' is treated as representative of the
average resistivity down to depth ~ a, so the resulting rho-vs-a curve is
shown as the resistivity-depth chart.

Runtime: Python 3 / Kivy. No matplotlib / kivy_garden dependency is used for
the chart -- it's drawn directly on a Kivy Canvas to keep the APK small and
avoid extra native build dependencies.
"""

import math
import csv
import os
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.spinner import Spinner


ROW_FIELDS = ["a", "v1", "i1", "v2", "i2"]


def safe_float(text, default=0.0):
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


class ResistivityRow(BoxLayout):
    """One measurement row: a, V1, I1, V2, I2 -> R1, R2, rho1, rho2, rho_avg"""

    def __init__(self, on_remove, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                          height=dp(44), spacing=dp(2), **kwargs)
        self.inputs = {}
        for field, hint in [("a", "a (m)"), ("v1", "V1 (mV)"), ("i1", "I1 (mA)"),
                             ("v2", "V2 (mV)"), ("i2", "I2 (mA)")]:
            ti = TextInput(
                hint_text=hint, multiline=False, input_filter="float",
                size_hint_x=None, width=dp(88),
            )
            self.inputs[field] = ti
            self.add_widget(ti)

        self.result_label = Label(text="rho_avg: -", size_hint_x=None, width=dp(180))
        self.add_widget(self.result_label)

        remove_btn = Button(text="X", size_hint_x=None, width=dp(40))
        remove_btn.bind(on_release=lambda *_: on_remove(self))
        self.add_widget(remove_btn)

        self.last_result = None  # (a, rho_avg)

    def get_values(self):
        return {f: safe_float(self.inputs[f].text) for f in ROW_FIELDS}

    def compute(self):
        v = self.get_values()
        a = v["a"]
        rho1 = rho2 = None
        if v["i1"] != 0:
            r1 = v["v1"] / v["i1"]
            rho1 = 2 * math.pi * a * r1
        if v["i2"] != 0:
            r2 = v["v2"] / v["i2"]
            rho2 = 2 * math.pi * a * r2

        vals = [x for x in (rho1, rho2) if x is not None]
        if not vals or a <= 0:
            self.result_label.text = "rho_avg: -"
            self.last_result = None
            return None

        rho_avg = sum(vals) / len(vals)
        self.result_label.text = f"rho_avg: {rho_avg:.3f} Ohm.m"
        self.last_result = (a, rho_avg, rho1, rho2)
        return self.last_result


class ResistivityChart(Widget):
    """Simple canvas-drawn plot of apparent resistivity vs electrode spacing (depth)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []  # list of (a, rho_avg)
        self.bind(size=self.redraw, pos=self.redraw)

    def set_points(self, points):
        self.points = sorted(points, key=lambda p: p[0])
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        pad_l, pad_b, pad_t, pad_r = dp(60), dp(40), dp(20), dp(20)
        w = self.width - pad_l - pad_r
        h = self.height - pad_b - pad_t
        if w <= 0 or h <= 0:
            return

        with self.canvas:
            Color(0.6, 0.6, 0.6, 1)
            Line(points=[self.x + pad_l, self.y + pad_b,
                         self.x + pad_l, self.y + pad_b + h], width=1)
            Line(points=[self.x + pad_l, self.y + pad_b,
                         self.x + pad_l + w, self.y + pad_b], width=1)

        if not self.points:
            return

        max_a = max(p[0] for p in self.points) or 1
        max_rho = max(p[1] for p in self.points) or 1
        min_rho = 0

        def to_px(a, rho):
            px = self.x + pad_l + (a / max_a) * w
            py = self.y + pad_b + ((rho - min_rho) / (max_rho - min_rho or 1)) * h
            return px, py

        line_pts = []
        with self.canvas:
            Color(0.85, 0.85, 0.85, 1)
            for i in range(1, 5):
                yy = self.y + pad_b + h * i / 4
                Line(points=[self.x + pad_l, yy, self.x + pad_l + w, yy], width=0.5)

            Color(0.2, 0.5, 0.9, 1)
            for a, rho in self.points:
                px, py = to_px(a, rho)
                line_pts.extend([px, py])
            if len(line_pts) >= 4:
                Line(points=line_pts, width=dp(2))

            Color(0.9, 0.3, 0.2, 1)
            for a, rho in self.points:
                px, py = to_px(a, rho)
                Ellipse(pos=(px - dp(3), py - dp(3)), size=(dp(6), dp(6)))

        # Axis labels (redrawn each time as child labels)
        for child in list(self.children):
            if getattr(child, "_axis_label", False):
                self.remove_widget(child)

        x_label = Label(text="Electrode spacing a (m) = approx. depth",
                         size_hint=(None, None), size=(w, dp(20)),
                         pos=(self.x + pad_l, self.y),
                         color=(0.3, 0.3, 0.3, 1), font_size=dp(12))
        x_label._axis_label = True
        self.add_widget(x_label)

        y_label = Label(text="rho (Ohm.m)", size_hint=(None, None),
                         size=(dp(56), dp(20)),
                         pos=(self.x, self.y + pad_b + h - dp(10)),
                         color=(0.3, 0.3, 0.3, 1), font_size=dp(12))
        y_label._axis_label = True
        self.add_widget(y_label)

        max_label = Label(text=f"max {max_rho:.1f}", size_hint=(None, None),
                           size=(pad_l, dp(16)),
                           pos=(self.x, self.y + pad_b + h - dp(8)),
                           color=(0.3, 0.3, 0.3, 1), font_size=dp(10))
        max_label._axis_label = True
        self.add_widget(max_label)


class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.rows = []

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(90),
                            padding=(dp(8), dp(4)))
        title = Label(text="Wenner Soil Resistivity Calculator", bold=True,
                      size_hint_y=None, height=dp(28), font_size=dp(18))
        header.add_widget(title)

        meta = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.site_input = TextInput(hint_text="Substation / Site", multiline=False)
        self.date_input = TextInput(
            hint_text="Date", multiline=False,
            text=datetime.now().strftime("%Y-%m-%d"))
        meta.add_widget(self.site_input)
        meta.add_widget(self.date_input)
        header.add_widget(meta)
        self.add_widget(header)

        col_header = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(2),
                                padding=(dp(4), 0))
        for text in ["a (m)", "V1 (mV)", "I1 (mA)", "V2 (mV)", "I2 (mA)"]:
            col_header.add_widget(Label(text=text, size_hint_x=None, width=dp(88),
                                         font_size=dp(11)))
        col_header.add_widget(Label(text="Result", size_hint_x=None, width=dp(180),
                                     font_size=dp(11)))
        col_header.add_widget(Label(text="", size_hint_x=None, width=dp(40)))
        self.add_widget(col_header)

        self.rows_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(2),
                                       padding=(dp(4), 0))
        self.rows_layout.bind(minimum_height=self.rows_layout.setter("height"))
        scroll = ScrollView(size_hint=(1, 0.35))
        scroll.add_widget(self.rows_layout)
        self.add_widget(scroll)

        # Default spacings matching common IEEE 81 Wenner test sequence
        for a in [0.5, 1, 2, 4, 8, 12, 16, 20]:
            self.add_row(default_a=a)

        controls = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6),
                              padding=(dp(6), dp(4)))
        add_btn = Button(text="+ Add Row")
        add_btn.bind(on_release=lambda *_: self.add_row())
        calc_btn = Button(text="Calculate")
        calc_btn.bind(on_release=lambda *_: self.calculate())
        export_btn = Button(text="Export CSV")
        export_btn.bind(on_release=lambda *_: self.export_csv())
        controls.add_widget(add_btn)
        controls.add_widget(calc_btn)
        controls.add_widget(export_btn)
        self.add_widget(controls)

        self.chart = ResistivityChart(size_hint=(1, 0.5))
        self.add_widget(self.chart)

        self.status_label = Label(text="", size_hint_y=None, height=dp(22),
                                   font_size=dp(12))
        self.add_widget(self.status_label)

    def add_row(self, default_a=None):
        row = ResistivityRow(on_remove=self.remove_row)
        if default_a is not None:
            row.inputs["a"].text = str(default_a)
        self.rows.append(row)
        self.rows_layout.add_widget(row)

    def remove_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            self.rows_layout.remove_widget(row)

    def calculate(self):
        points = []
        for row in self.rows:
            result = row.compute()
            if result:
                a, rho_avg = result[0], result[1]
                points.append((a, rho_avg))
        self.chart.set_points(points)
        self.status_label.text = f"Calculated {len(points)} of {len(self.rows)} rows."

    def export_csv(self):
        out_dir = App.get_running_app().user_data_dir
        fname = f"wenner_resistivity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(out_dir, fname)
        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Site", self.site_input.text])
                writer.writerow(["Date", self.date_input.text])
                writer.writerow([])
                writer.writerow(["a (m)", "V1 (mV)", "I1 (mA)", "V2 (mV)", "I2 (mA)",
                                  "rho1 (Ohm.m)", "rho2 (Ohm.m)", "rho_avg (Ohm.m)"])
                for row in self.rows:
                    v = row.get_values()
                    res = row.last_result
                    if res:
                        _, rho_avg, rho1, rho2 = res
                        writer.writerow([v["a"], v["v1"], v["i1"], v["v2"], v["i2"],
                                          f"{rho1:.4f}" if rho1 is not None else "",
                                          f"{rho2:.4f}" if rho2 is not None else "",
                                          f"{rho_avg:.4f}"])
                    else:
                        writer.writerow([v["a"], v["v1"], v["i1"], v["v2"], v["i2"],
                                          "", "", ""])
            self.status_label.text = f"Saved: {path}"
        except OSError as e:
            self.status_label.text = f"Export failed: {e}"


class WennerApp(App):
    def build(self):
        Window.clearcolor = (0.97, 0.97, 0.97, 1)
        return RootWidget()


if __name__ == "__main__":
    WennerApp().run()
