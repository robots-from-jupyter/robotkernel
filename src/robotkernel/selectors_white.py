# -*- coding: utf-8 -*-
from System.Drawing import Bitmap
from System.Drawing import Color
from System.Drawing import Graphics
from System.Drawing import GraphicsUnit
from System.Drawing import Pen
from System.Drawing import Rectangle
from System.Drawing import Size
from System.Drawing import SolidBrush
from System.Drawing.Imaging import ImageFormat
from System.Drawing.Imaging import PixelFormat
from System.IO import MemoryStream
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
import os
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
    def take_screenshot(as_bytes=False):
        bounds = Screen.PrimaryScreen.Bounds
        screenshot = Bitmap(bounds.Width, bounds.Height, PixelFormat.Format32bppPArgb)
        graphics = Graphics.FromImage(screenshot)
        graphics.CopyFromScreen(0, 0, 0, 0, screenshot.Size)
        if as_bytes:
            fp = MemoryStream()
            screenshot.Save(fp, ImageFormat.Png)
            return bytes(bytearray(fp.ToArray()))
        else:
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

        if result == DialogResult.OK and snip:
            if snipper.snip_rectangle.Width and snipper.snip_rectangle.Height:
                img = Bitmap(
                    snipper.snip_rectangle.Width, snipper.snip_rectangle.Height
                )
                gr = Graphics.FromImage(img)
                gr.DrawImage(
                    snipper.BackgroundImage,
                    Rectangle(0, 0, img.Width, img.Height),
                    snipper.snip_rectangle,
                    GraphicsUnit.Pixel,
                )
                fp = MemoryStream()
                img.Save(fp, ImageFormat.Png)
                return {"bytes": bytes(bytearray(fp.ToArray()))}
            return {}

        elif result == DialogResult.OK:
            if (
                snipper.mouse_down_seconds
                and snipper.mouse_down_seconds <= snipper.click_timeout
            ):
                Mouse.Instance.Click(snipper.mouse_down)
                time.sleep(0.5)
            el = AutomationElement.FromPoint(snipper.mouse_up)
            result = {
                prop.ProgrammaticName.split(".", 1)[-1]: el.GetCurrentPropertyValue(
                    prop
                )
                for prop in el.GetSupportedProperties()
            }
            result.update(
                {
                    "NameProperty": el.GetCurrentPropertyValue(el.NameProperty),
                    "ControlTypeProperty": el.GetCurrentPropertyValue(
                        el.ControlTypeProperty
                    ).ProgrammaticName.split(".", 1)[-1],
                    "AutomationIdProperty": el.GetCurrentPropertyValue(
                        el.AutomationIdProperty
                    ),
                }
            )
            return result
        else:
            return {}

    def __init__(self, screenshot=None, snip=False):
        super(PickSnipTool, self).__init__()
        self.snip_enabled = snip

        self.Cursor = Cursors.Cross
        self.BackgroundImage = screenshot
        self.ShowInTaskbar = False
        self.FormBorderStyle = getattr(FormBorderStyle, "None")
        self.WindowState = FormWindowState.Maximized
        self.DoubleBuffered = True
        self.TopMost = True
        self.TopLevel = True

        self.MouseDown += self.on_mouse_down
        self.MouseMove += self.on_mouse_move
        self.MouseUp += self.on_mouse_up
        self.KeyUp += self.on_key_up
        self.KeyDown += self.OnKeyDown
        self.Paint += self.on_paint

    def on_timer_tick(self, sender, e):
        self.mouse_down_seconds += 1
        if self.mouse_down_seconds == 1:
            self.DialogResult = DialogResult.Retry
        if self.mouse_down_seconds > self.click_timeout:
            self.DialogResult = DialogResult.Retry

    def on_mouse_down(self, sender, e):
        self.mouse_down = Point(e.Location.X, e.Location.Y)
        self.mouse_down_button = e.Button
        self.mouse_down_seconds = 0
        if not self.snip_enabled:
            self.mouse_down_timer = Timer()
            self.mouse_down_timer.Interval = 1000
            self.mouse_down_timer.Tick += self.on_timer_tick
            self.mouse_down_timer.Start()
        self.snip_rectangle = Rectangle(e.Location, Size(0, 0))

    def on_mouse_move(self, sender, e):
        if self.mouse_down and self.snip_enabled:
            x1 = int(min(e.X, self.mouse_down.X))
            y1 = int(min(e.Y, self.mouse_down.Y))
            x2 = int(max(e.X, self.mouse_down.X))
            y2 = int(max(e.Y, self.mouse_down.Y))
            self.snip_rectangle = Rectangle(x1, y1, x2 - x1, y2 - y1)
            self.Invalidate()

    def on_mouse_up(self, sender, e):
        self.mouse_up = Point(e.Location.X, e.Location.Y)
        if self.mouse_down_timer is not None:
            self.mouse_down_timer.Stop()
        self.DialogResult = DialogResult.OK

    def on_paint(self, sender, e):
        if self.snip_enabled and self.snip_rectangle is not None:
            br = SolidBrush(Color.FromArgb(120, Color.White))
            rc = self.snip_rectangle
            pen = Pen(Color.Red, 3.0)

            x1 = rc.X
            x2 = rc.X + rc.Width
            y1 = rc.Y
            y2 = rc.Y + rc.Height

            e.Graphics.FillRectangle(br, Rectangle(0, 0, x1, self.Height))
            e.Graphics.FillRectangle(br, Rectangle(x2, 0, self.Width - x2, self.Height))
            e.Graphics.FillRectangle(br, Rectangle(x1, 0, x2 - x1, y1))
            e.Graphics.FillRectangle(br, Rectangle(x1, y2, x2 - x1, self.Height - y2))
            e.Graphics.DrawRectangle(pen, rc)

    def on_key_up(self, sender, e):
        if e.KeyCode == Keys.Escape:
            self.DialogResult = DialogResult.Cancel


class WhiteLibraryCompanion:
    """Complementary keyword library to use OpenCV based image recognition with RobotKernel and WhiteLibrary.
    """

    def match_template(self, template: str, similarity: float = 0.8):
        import numpy as np  # noqa
        import cv2 as cv  # noqa

        screenshot = PickSnipTool.take_screenshot(as_bytes=True)
        image = cv.imdecode(np.frombuffer(screenshot, np.uint8), cv.IMREAD_COLOR)
        template = cv.imread(template)
        result = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

        similarity = float(similarity)
        assert max_val >= similarity, f"Template not found ({max_val} < {similarity})"

        return (
            int(max_loc[0] + template.shape[1] / 2),
            int(max_loc[1] + template.shape[0] / 2),
        )

    def click_template(self, template, similarity=0.95):
        """Click center of the location best matching the given ``template`` if match with at least the given ``similarity`` threshold is found.

        Arguments:

        ``template``
            path to a image file used as the match template

        ``similarity``
            minimum accepted match similarity (default: 0.95).
        """
        assert os.path.isfile(template), f"File not found: {template}"
        x, y = self.match_template(template, similarity)
        Mouse.Instance.Click(Point(int(x), int(y)))


if __name__ == "__main__":
    from pprint import pprint

    pprint.pprint(PickSnipTool.pick())
