# -*- coding: utf-8 -*-
from System import Math
from System.Drawing import Bitmap
from System.Drawing import Color
from System.Drawing import Graphics
from System.Drawing import Pen
from System.Drawing import Rectangle
from System.Drawing import Size
from System.Drawing import SolidBrush
from System.Drawing.Imaging import PixelFormat
from System.Windows import Point
from System.Windows.Automation import AutomationElement
from System.Windows.Forms import Cursors
from System.Windows.Forms import DialogResult
from System.Windows.Forms import Form
from System.Windows.Forms import FormBorderStyle
from System.Windows.Forms import FormWindowState
from System.Windows.Forms import Keys
from System.Windows.Forms import Screen
from System.Windows.Forms import Timer
from TestStack.White.InputDevices import Mouse

import time


class PickSnipTool(Form):

    mouse_down = None
    mouse_down_button = None
    mouse_down_seconds = 0
    mouse_down_timer = None
    mouse_up = None

    snip_enabled = False
    snip_rectangle = None

    click_timeout = 1  # set this to eg. 4 to enable click + pick

    @staticmethod
    def take_screenshot():
        bounds = Screen.PrimaryScreen.Bounds
        screenshot = Bitmap(
            bounds.Width,
            bounds.Height,
            PixelFormat.Format32bppPArgb,
        )
        graphics = Graphics.FromImage(screenshot)
        graphics.CopyFromScreen(0, 0, 0, 0, screenshot.Size)
        return screenshot

    @staticmethod
    def pick(snip=False):
        snipper = PickSnipTool(PickSnipTool.take_screenshot(), snip=snip)

        while True:
            result = snipper.ShowDialog()
            if result in [DialogResult.OK, DialogResult.Cancel]:
                break
            if snipper.mouse_down_seconds == 1:
                Mouse.Instance.Click(snipper.mouse_down)
                time.sleep(0.5)
            snipper.BackgroundImage = PickSnipTool.take_screenshot()

        if result == DialogResult.OK:
            if (snipper.mouse_down_seconds
                    and snipper.mouse_down_seconds <= snipper.click_timeout):
                Mouse.Instance.Click(snipper.mouse_down)
                time.sleep(0.5)
            el = AutomationElement.FromPoint(snipper.mouse_up)
            result = {
                prop.ProgrammaticName.split('.', 1)[-1]:
                el.GetCurrentPropertyValue(prop)
                for prop in el.GetSupportedProperties()
            }
            result.update({
                'NameProperty': el.GetCurrentPropertyValue(el.NameProperty),
                'ControlTypeProperty': el.GetCurrentPropertyValue(
                    el.ControlTypeProperty
                ).ProgrammaticName.split('.', 1)[-1],
                'AutomationIdProperty': el.GetCurrentPropertyValue(
                    el.AutomationIdProperty
                ),
            })
            return result
        else:
            return {}

    def __init__(self, screenshot=None, snip=False):
        super(PickSnipTool, self).__init__()
        self.snip_enabled = snip

        self.Cursor = Cursors.Cross
        self.BackgroundImage = screenshot
        self.ShowInTaskbar = False
        self.FormBorderStyle = getattr(FormBorderStyle, 'None')
        self.WindowState = FormWindowState.Maximized
        self.DoubleBuffered = True
        self.TopMost = True
        self.TopLevel = True

        self.MouseDown += self.OnMouseDown
        self.MouseMove += self.OnMouseMove
        self.MouseUp += self.OnMouseUp
        self.KeyUp += self.OnKeyUp
        self.KeyDown += self.OnKeyDown
        self.Paint += self.OnPaint

    def OnTimerTick(self, sender, e):
        self.mouse_down_seconds += 1
        if self.mouse_down_seconds == 1:
            self.DialogResult = DialogResult.Retry
        if self.mouse_down_seconds > self.click_timeout:
            self.DialogResult = DialogResult.Retry

    def OnMouseDown(self, sender, e):
        self.mouse_down = Point(e.Location.X, e.Location.Y)
        self.mouse_down_button = e.Button
        self.mouse_down_seconds = 0
        if not self.snip_enabled:
            self.mouse_down_timer = Timer()
            self.mouse_down_timer.Interval = 1000
            self.mouse_down_timer.Tick += self.OnTimerTick
            self.mouse_down_timer.Start()
        self.snip_rectangle = Rectangle(e.Location, Size(0, 0))

    def OnMouseMove(self, sender, e):
        if self.mouse_down and self.snip_enabled:
            x1 = Math.Min(e.X, self.mouse_down.X)
            y1 = Math.Min(e.Y, self.mouse_down.Y)
            x2 = Math.Max(e.X, self.mouse_down.X)
            y2 = Math.Max(e.Y, self.mouse_down.Y)
            self.snip_rectangle = Rectangle(x1, y1, x2 - x1, y2 - y1)
            self.Invalidate()

    def OnMouseUp(self, sender, e):
        self.mouse_up = Point(e.Location.X, e.Location.Y)
        if self.mouse_down_timer is not None:
            self.mouse_down_timer.Stop()
        self.DialogResult = DialogResult.OK

    def OnPaint(self, sender, e):
        if self.snip_enabled and self.snip_rectangle is not None:
            br = SolidBrush(Color.FromArgb(120, Color.White))
            rc = self.snip_rectangle
            pen = Pen(Color.Red, 3)

            x1 = rc.X
            x2 = rc.X + rc.Width
            y1 = rc.Y
            y2 = rc.Y + rc.Height

            e.Graphics.FillRectangle(br, Rectangle(0, 0, x1, self.Height))
            e.Graphics.FillRectangle(
                br, Rectangle(x2, 0, self.Width - x2, self.Height)
            )
            e.Graphics.FillRectangle(br, Rectangle(x1, 0, x2 - x1, y1))
            e.Graphics.FillRectangle(
                br, Rectangle(x1, y2, x2 - x1, self.Height - y2)
            )
            e.Graphics.DrawRectangle(pen, rc)

    def OnKeyUp(self, sender, e):
        if e.KeyCode == Keys.Escape:
            self.DialogResult = DialogResult.Cancel


if __name__ == '__main__':
    from pprint import pprint
    pprint.pprint(PickSnipTool.pick())
