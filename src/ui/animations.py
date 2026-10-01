from PyQt6.QtCore import (
    Qt, QObject, QPropertyAnimation, QVariantAnimation, QEasingCurve,
    QPointF, pyqtProperty, QTimer
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QPen


class SmoothAnimationHelper(QObject):
    """
    Provides smooth easing transitions for ProgressBars, ProgressRings, and numeric values.
    """

    @staticmethod
    def animate_progress_bar(bar, target_value, duration=500):
        """Animates a QProgressBar smoothly to a new value using OutCubic curve."""
        current_val = bar.value()
        if current_val == target_value:
            return

        # Store animation on the widget to prevent garbage collection
        anim = QPropertyAnimation(bar, b"value", bar)
        anim.setDuration(duration)
        anim.setStartValue(current_val)
        anim.setEndValue(int(target_value))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        bar._current_anim = anim

    @staticmethod
    def animate_progress_ring(ring, target_value, duration=700):
        """Animates a ProgressRing with a subtle spring bounce (OutBack)."""
        current_val = ring.value()
        if current_val == target_value:
            return

        anim = QPropertyAnimation(ring, b"value", ring)
        anim.setDuration(duration)
        anim.setStartValue(current_val)
        anim.setEndValue(int(target_value))
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        ring._current_anim = anim


class MiniWaveWidget(QWidget):
    """
    Real-time dynamic sparkline / wave graph with smooth gradient fill.
    Inspired by Windows 11 Task Manager performance charts.
    """

    def __init__(self, color_hex="#0078D4", max_points=24, parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.max_points = max_points
        self.points = [10] * max_points
        self.setFixedHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def add_point(self, value):
        """Pushes a new value (0-100) and smoothly repaints."""
        val = max(0, min(100, float(value)))
        self.points.append(val)
        if len(self.points) > self.max_points:
            self.points.pop(0)
        self.update()

    def set_color(self, color_hex):
        self.color = QColor(color_hex)
        self.update()

    def paintEvent(self, event):
        if not self.points or self.width() <= 0 or self.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self.points)
        step = w / max(1, (n - 1))

        # Build path
        path = QPainterPath()
        first_y = h - (self.points[0] / 100.0) * (h - 6) - 3
        path.moveTo(0, first_y)

        for i in range(1, n):
            x = i * step
            y = h - (self.points[i] / 100.0) * (h - 6) - 3
            # Smooth cubic bezier curve between points
            prev_x = (i - 1) * step
            prev_y = h - (self.points[i - 1] / 100.0) * (h - 6) - 3
            cx1 = prev_x + step / 2
            cy1 = prev_y
            cx2 = prev_x + step / 2
            cy2 = y
            path.cubicTo(cx1, cy1, cx2, cy2, x, y)

        # Gradient fill path
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        grad_color = QColor(self.color)
        grad_color.setAlpha(80)
        grad.setColorAt(0.0, grad_color)
        grad_color_bottom = QColor(self.color)
        grad_color_bottom.setAlpha(5)
        grad.setColorAt(1.0, grad_color_bottom)

        painter.fillPath(fill_path, grad)

        # Stroke line
        pen = QPen(self.color, 1.8)
        painter.strokePath(path, pen)

        # Draw glowing dot on the latest point
        last_x = w
        last_y = h - (self.points[-1] / 100.0) * (h - 6) - 3
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(last_x - 3, last_y), 3, 3)

        painter.end()


class PulseEffect(QObject):
    """
    Sinusoidal breathing / pulse glow animation for warning badges and cards.
    """

    def __init__(self, target_widget, min_opacity=0.35, max_opacity=1.0, duration=1400):
        super().__init__(target_widget)
        self.target = target_widget
        self.effect = QGraphicsOpacityEffect(target_widget)
        self.target.setGraphicsEffect(self.effect)

        self.anim = QPropertyAnimation(self.effect, b"opacity", self)
        self.anim.setDuration(duration)
        self.anim.setStartValue(max_opacity)
        self.anim.setKeyValueAt(0.5, min_opacity)
        self.anim.setEndValue(max_opacity)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.setLoopCount(-1)  # Infinite breathing loop

    def start(self):
        if self.anim.state() != QPropertyAnimation.State.Running:
            self.anim.start()

    def stop(self):
        if self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
            self.effect.setOpacity(1.0)


class NumberRollAnimation(QObject):
    """
    Smoothly interpolates numeric values (e.g. rolling counter from 150MB -> 0MB
    or RAM freed from 0MB -> 800MB).
    """

    def __init__(self, target_label, start_val, end_val, duration=700, is_size=True, prefix="", suffix="", parent=None):
        super().__init__(parent or target_label)
        self.target_label = target_label
        self.is_size = is_size
        self.prefix = prefix
        self.suffix = suffix
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(duration)
        self.anim.setStartValue(float(start_val))
        self.anim.setEndValue(float(end_val))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val):
        from core.cleaner import format_size
        if self.is_size:
            text = format_size(int(val))
        else:
            text = f"{int(val)}"
        self.target_label.setText(f"{self.prefix}{text}{self.suffix}")

    def start(self):
        self.anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


def animate_button_bounce(btn):
    """
    Subtle physical click bounce animation for major action buttons.
    Shrinks by 2px and springs back out cleanly in 160ms.
    """
    try:
        orig_geo = btn.geometry()
        anim = QPropertyAnimation(btn, b"geometry", btn)
        anim.setDuration(160)
        anim.setStartValue(orig_geo)
        shrink_geo = orig_geo.adjusted(2, 2, -2, -2)
        anim.setKeyValueAt(0.5, shrink_geo)
        anim.setEndValue(orig_geo)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        pass


class TableFadeOutHelper(QObject):
    """
    Fades out a table smoothly before rows are removed or updated,
    creating a seamless disappearance effect.
    """

    @staticmethod
    def fade_out_table(table, duration=220, on_finished=None):
        effect = QGraphicsOpacityEffect(table)
        table.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", table)
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.15)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        def finish():
            table.setGraphicsEffect(None)
            if on_finished:
                on_finished()

        anim.finished.connect(finish)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


class StaggeredCardEntrance(QObject):
    """
    Staggered entrance animation for cards/widgets on tab load (Phương án 8).
    Animates opacity smoothly for each widget in sequential cascade.
    """

    @staticmethod
    def animate_cards(widgets, base_delay=40, step_delay=50, duration=350):
        for idx, w in enumerate(widgets):
            if not w:
                continue
            delay = base_delay + idx * step_delay
            effect = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(effect)
            effect.setOpacity(0.0)

            anim = QPropertyAnimation(effect, b"opacity", w)
            anim.setDuration(duration)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def make_starter(a, widget):
                def start_it():
                    def on_done():
                        widget.setGraphicsEffect(None)
                    a.finished.connect(on_done)
                    a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
                return start_it

            QTimer.singleShot(delay, make_starter(anim, w))

