from __future__ import annotations

import itertools
import math
import random
from typing import TYPE_CHECKING, Any

from ayugespidertools.exceptions import NotConfigured

try:
    import cv2
    import numpy as np
except ImportError:
    raise NotConfigured(
        "The opencv-python (cv2) and numpy packages are required. "
        "Install them with: pip install ayugespidertools[all]"
    )

__all__ = ["BezierTrajectory", "CvnpilKit"]

if TYPE_CHECKING:
    from cv2.typing import MatLike


class CvnpilKit:
    @staticmethod
    def get_array_dimension(array: frozenset | list | set | tuple) -> int:
        return len(np.array(array).shape)

    @staticmethod
    def read_image_data(
        img: bytes | str, flags: int = cv2.IMREAD_COLOR
    ) -> np.ndarray | None:
        """Load image data from a file path or encoded image bytes using OpenCV.

        Args:
            img: Image file path or encoded image bytes.
            flags: OpenCV read flags for file paths. Byte input is decoded with
                IMREAD_ANYCOLOR regardless of this argument.

        Returns:
            The decoded image array, or None if OpenCV cannot decode the image.
        """
        assert type(img) in [str, bytes], (
            "img must be a file path (str) or encoded image bytes"
        )
        if isinstance(img, bytes):
            img_buf = np.frombuffer(img, np.uint8)
            img_cv = cv2.imdecode(img_buf, cv2.IMREAD_ANYCOLOR)
        else:
            # Load the image using the requested flags; color mode defaults to BGR.
            img_cv = cv2.imread(img, flags)
        return img_cv

    @staticmethod
    def clear_white(img):
        """Crop blank areas around the slider."""
        rows, cols, channel = img.shape
        min_x = 255
        min_y = 255
        max_x = 0
        max_y = 0
        for x, y in itertools.product(range(1, rows), range(1, cols)):
            t = set(img[x, y])
            if len(t) >= 2:
                if x <= min_x:
                    min_x = x
                elif x >= max_x:
                    max_x = x

                if y <= min_y:
                    min_y = y
                elif y >= max_y:
                    max_y = y
        return img[min_x:max_x, min_y:max_y]

    @staticmethod
    def image_edge_detection(img):
        """Detect image edges with the Canny algorithm."""
        return cv2.Canny(img, 100, 200)

    @staticmethod
    def _template_match(bg: MatLike, slider: MatLike, out: str | None = None) -> int:
        """Find the slider gap in the background using normalized template matching.

        Args:
            bg: Background image array.
            slider: Slider template image array.
            out: Optional output path for the background with the match outlined.

        Returns:
            The horizontal coordinate of the best match.
        """
        res = cv2.matchTemplate(bg, slider, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # Top-left corner of the best match.
        tl = max_loc

        if out:
            # Draw a rectangle around the matched region.
            th, tw = slider.shape[:2]
            # Bottom-right corner of the matched region.
            br = (tl[0] + tw, tl[1] + th)
            cv2.rectangle(bg, tl, br, (0, 0, 255), 2)
            cv2.imwrite(out, bg)
        return tl[0]

    @classmethod
    def discern_gap(
        cls, bg: str | bytes, slider: str | bytes, out: str | None = None
    ) -> int:
        """Locate a slider gap after cropping the slider and extracting image edges.

        Args:
            bg: Background image file path or encoded image bytes.
            slider: Slider image file path or encoded image bytes.
            out: Optional output path for the annotated match image.

        Returns:
            The horizontal coordinate of the matched gap.
        """
        slider_cv = CvnpilKit.read_image_data(slider)
        bg_cv = CvnpilKit.read_image_data(bg, cv2.IMREAD_GRAYSCALE)
        slider_clr = cls.clear_white(slider_cv)
        slider_clr = cv2.cvtColor(slider_clr, cv2.COLOR_RGB2GRAY)
        slider_img = cls.image_edge_detection(slider_clr)
        bg_img = cls.image_edge_detection(bg_cv)
        slider_img = cv2.cvtColor(slider_img, cv2.COLOR_GRAY2RGB)
        bg_img = cv2.cvtColor(bg_img, cv2.COLOR_GRAY2RGB)
        return cls._template_match(bg_img, slider_img, out)

    @classmethod
    def identify_gap(
        cls, bg: bytes | str, slider: bytes | str, out: str | None = None
    ) -> int:
        """Locate a slider gap by matching the background and slider edge maps.

        Args:
            bg: Background image file path or encoded image bytes.
            slider: Slider image file path or encoded image bytes.
            out: Optional output path for the annotated match image.
                No image is saved when this argument is omitted.

        Returns:
            The horizontal coordinate of the matched gap.
        """
        # Decode the background and slider images.
        bg_cv = cls.read_image_data(bg)
        slider_cv = cls.read_image_data(slider, cv2.IMREAD_GRAYSCALE)
        # Extract edge maps.
        bg_edge = cv2.Canny(bg_cv, 100, 200)
        slider_edge = cv2.Canny(slider_cv, 100, 200)
        # Convert the edge maps to three-channel images.
        bg_img = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        slider_img = cv2.cvtColor(slider_edge, cv2.COLOR_GRAY2RGB)
        return cls._template_match(bg_img, slider_img, out)

    @staticmethod
    def match_gap(bg: str | bytes, slider: str | bytes) -> int | None:
        """Locate a slider template by iteratively adjusting the match threshold.

        Args:
            bg: Background image file path or encoded image bytes.
            slider: Slider image file path or encoded image bytes.

        Returns:
            The first horizontal coordinate meeting the final threshold,
            or None if the threshold becomes negative.
        """
        bg_cv = CvnpilKit.read_image_data(bg, cv2.IMREAD_GRAYSCALE)
        slider_cv = CvnpilKit.read_image_data(slider, cv2.IMREAD_GRAYSCALE)

        run = 1
        # The number of values returned here may vary across OpenCV versions.
        # w, h, z = slider_cv.shape[::-1]
        # Find the slider template in the background image.
        res = cv2.matchTemplate(bg_cv, slider_cv, cv2.TM_CCOEFF_NORMED)
        # Use binary search to determine the precise matching threshold.
        lft: float = 0.0
        rgt: float = 1.0
        loc: tuple[np.ndarray[Any, np.dtype[np.signedinteger[Any]]], ...] = ()
        while run < 20:
            run += 1
            threshold = (rgt + lft) / 2
            if threshold < 0:
                # This indicates an error: the target location was not found.
                return None

            # Get the x and y coordinates where the matching score exceeds the threshold.
            loc = np.where(res >= threshold)
            if len(loc[1]) > 1:
                rgt += (rgt - lft) / 2
            elif len(loc[1]) == 1:
                # The x-coordinate of the target region's starting point is loc[1][0].
                break
            elif len(loc[1]) < 1:
                rgt -= (rgt - lft) / 2
        return loc[1][0]

    @staticmethod
    def get_normal_track(space):
        """Generate a track array based on the slider distance.

        Args:
            space: The distance to the slider gap.

        Returns:
            The generated track array.
        """
        x = [0, 0]
        y = [0, 0, 0]
        z = [0]
        # x
        count = np.linspace(-math.pi / 2, math.pi / 2, random.randrange(20, 30))
        func = list(map(math.sin, count))
        nx = [i + 1 for i in func]
        add = random.randrange(10, 15)
        sadd = space + add
        x.extend([i * (sadd / 2) for i in nx])
        # x.extend(np.linspace(sadd, space, 4 if add > 12 else 3))
        x.extend(np.linspace(sadd, space, 3 if add > 12 else 2))
        x = [math.floor(i) for i in x]
        # y
        for _ in range(len(x) - 2):
            if y[-1] < 30:
                y.append(y[-1] + random.choice([0, 0, 1, 1, 2, 2, 1, 2, 0, 0, 3, 3]))
            else:
                y.append(
                    y[-1] + random.choice([0, 0, -1, -1, -2, -2, -1, -2, 0, 0, -3, -3])
                )
        # z
        for _ in range(len(x) - 1):
            # z.append((z[-1] // 100 * 100) + 100 + random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2]))
            z.append(
                (z[-1] // 100 * 100)
                + 100
                + random.choice([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3])
            )

        tracks_list = list(map(list, zip(x, y, z, strict=False)))
        return [x for x in tracks_list if x[0] > 0]


class BezierTrajectory:
    """Generate trajectories along Bezier curves.

    Examples:
        >>> bt = BezierTrajectory()
        >>> gen_data = bt.gen_track(start=[50, 268], end=[367, 485], num=45, order=4, mode=2)
        >>> track = gen_data["trackArray"]
    """

    def _generate_control_points(self, track: list):
        """Calculate the control points of a Bézier curve."""
        track_len = len(track)

        def calculate_bezier_point(x):
            t = (x - track[0][0]) / (track[-1][0] - track[0][0])
            y = np.array([0, 0], dtype=np.float64)
            for s in range(len(track)):
                y += track[s] * (
                    (
                        math.factorial(track_len - 1)
                        / (math.factorial(s) * math.factorial(track_len - 1 - s))
                    )
                    * math.pow(t, s)
                    * math.pow((1 - t), track_len - 1 - s)
                )
            return y[1]

        return calculate_bezier_point

    def _type(self, mode, x, length):
        numbers = []
        pin = (x[1] - x[0]) / length
        if mode == 0:
            numbers.extend(i * pin for i in range(length))
            if pin >= 0:
                numbers.reverse()
        elif mode == 1:
            numbers = [1 * ((i * pin) ** 2) for i in range(length)]
            numbers.reverse()
        elif mode == 2:
            numbers = [1 * ((i * pin - x[1]) ** 2) for i in range(length)]

        elif mode == 3:
            track = [
                np.array([0, 0]),
                np.array([(x[1] - x[0]) * 0.8, (x[1] - x[0]) * 0.6]),
                np.array([x[1] - x[0], 0]),
            ]
            fun = self._generate_control_points(track)
            numbers = [0]
            numbers.extend(fun(i * pin) + numbers[-1] for i in range(1, length))
            if pin >= 0:
                numbers = numbers[::-1]
        numbers = np.abs(np.array(numbers) - max(numbers))
        normal_numbers = (
            (numbers - numbers[numbers.argmin()])
            / (numbers[numbers.argmax()] - numbers[numbers.argmin()])
        ) * (x[1] - x[0]) + x[0]
        normal_numbers[0] = x[0]
        normal_numbers[-1] = x[1]
        return normal_numbers

    def simulation(self, start, end, order=1, deviation=0, bias=0.5):
        """Build a Bezier curve from endpoints and generated intermediate control points.

        Args:
            start: Starting point coordinates.
            end: Ending point coordinates.
            order: Degree of the Bezier curve.
            deviation: Vertical displacement of intermediate control points
                from the line connecting the endpoints.
            bias: Position from which intermediate control-point intervals begin,
                expressed as a fraction of the horizontal span.

        Returns:
            A dictionary with equation (a callable mapping x to y) and P
            (the endpoints and intermediate control points).
        """
        start = np.array(start)
        end = np.array(end)
        shake_num = []
        if order != 1:
            e = (1 - bias) / (order - 1)
            shake_num = [[bias + e * i, bias + e * (i + 1)] for i in range(order - 1)]

        track_lst = [start]

        t = random.choice([-1, 1])
        w = 0
        for i in shake_num:
            px1 = start[0] + (end[0] - start[0]) * (
                random.random() * (i[1] - i[0]) + (i[0])
            )
            p = np.array(
                [px1, self._generate_control_points([start, end])(px1) + t * deviation]
            )
            track_lst.append(p)
            w += 1
            if w >= 2:
                w = 0
                t = -1 * t

        track_lst.append(end)
        return {
            "equation": self._generate_control_points(track_lst),
            "P": np.array(track_lst),
        }

    def gen_track(
        self,
        start: np.ndarray | list,
        end: np.ndarray | list,
        num: int,
        order: int = 1,
        deviation: int = 0,
        bias=0.5,
        mode=0,
        shake_num=0,
        yhh=10,
    ) -> dict:
        """Sample a Bezier trajectory with optional oscillation around the endpoint.

        Args:
            start: Starting point coordinates.
            end: Ending point coordinates.
            num: Requested number of trajectory points.
            order: Degree of the Bezier curve.
            deviation: Vertical displacement of intermediate control points.
            bias: Starting fraction for intermediate control-point intervals.
            mode: Horizontal sampling mode:
                0 for linear spacing;
                1 for reversed quadratic weights;
                2 for endpoint-based quadratic weights;
                3 for Bezier-based weights.
            shake_num: Number of oscillation segments around the endpoint.
            yhh: Initial horizontal amplitude of the endpoint oscillation.

        Returns:
            A dictionary with trackArray (the sampled trajectory points) and P
            (the endpoints and intermediate control points).
        """
        s: list = []
        fun = self.simulation(start, end, order, deviation, bias)
        w = fun["P"]
        fun = fun["equation"]
        if shake_num != 0:
            track_number = round(num * 0.2 / (shake_num + 1))
            num -= track_number * (shake_num + 1)

            x_track_array = self._type(mode, [start[0], end[0]], num)
            s.extend([i, fun(i)] for i in x_track_array)
            dq = yhh / shake_num
            kg = 0
            ends = np.copy(end)
            for i in range(shake_num):
                if kg == 0:
                    d = np.array(
                        [
                            end[0] + (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] + (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 1
                else:
                    d = np.array(
                        [
                            end[0] - (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] - (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 0
                y = self.gen_track(
                    ends,
                    d,
                    track_number,
                    order=2,
                    deviation=0,
                    bias=0.5,
                    mode=0,
                    shake_num=0,
                    yhh=10,
                )
                s += list(y["trackArray"])
                ends = d
            y = self.gen_track(
                ends,
                end,
                track_number,
                order=2,
                deviation=0,
                bias=0.5,
                mode=0,
                shake_num=0,
                yhh=10,
            )
            s += list(y["trackArray"])

        else:
            x_track_array = self._type(mode, [start[0], end[0]], num)
            s.extend([i, fun(i)] for i in x_track_array)
        return {"trackArray": np.array(s), "P": w}
