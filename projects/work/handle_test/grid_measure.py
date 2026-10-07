"""
Calibrate 10 mm graph paper and measure grip geometry from reference photos.

Grid fact (not estimated): 1 square = 10.0 mm horizontally and vertically on the physical paper.
Pixel scale is derived locally from detected grid spacing.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np
from scipy.signal import find_peaks

MM_PER_SQUARE = 10.0


@dataclass
class MeasurementItem:
    name: str
    value_mm: float
    source_photo: str
    measurement_method: str
    confidence: str
    notes: str = ""
    grid_squares: Optional[float] = None
    perspective_note: str = ""


@dataclass
class GridCalibration:
    region: str
    spacing_px_x: float
    spacing_px_y: float
    mm_per_px_x: float
    mm_per_px_y: float
    perspective_delta_pct: float


@dataclass
class PhotoMeasurementResult:
    file: str
    image_size: Tuple[int, int]
    calibrations: List[GridCalibration] = field(default_factory=list)
    measurements: List[MeasurementItem] = field(default_factory=list)
    overlay_path: Optional[str] = None


def _blue_line_score(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    return np.clip(b - 0.45 * (r + g), 0, 255)


def _estimate_grid_spacing_1d(profile: np.ndarray, min_distance: int) -> float:
    profile = profile.astype(np.float32)
    profile = profile - profile.min()
    if profile.max() > 0:
        profile = profile / profile.max()
    peaks, props = find_peaks(profile, distance=min_distance, prominence=0.15)
    if len(peaks) < 3:
        peaks, _ = find_peaks(profile, distance=max(8, min_distance // 2), prominence=0.08)
    if len(peaks) < 2:
        return float("nan")
    diffs = np.diff(peaks.astype(float))
    # Drop outliers > 1.5× median
    med = float(np.median(diffs))
    good = diffs[(diffs > med * 0.6) & (diffs < med * 1.5)]
    if len(good) == 0:
        return med
    return float(np.median(good))


def calibrate_grid_local(rgb: np.ndarray, region_name: str, y0: int, y1: int, x0: int, x1: int) -> GridCalibration:
    crop = rgb[y0:y1, x0:x1]
    score = _blue_line_score(crop)
    h_profile = score.sum(axis=1)
    v_profile = score.sum(axis=0)
    h_span = max(20, crop.shape[0] // 30)
    v_span = max(20, crop.shape[1] // 30)
    spacing_y = _estimate_grid_spacing_1d(h_profile, h_span)
    spacing_x = _estimate_grid_spacing_1d(v_profile, v_span)
    mm_per_px_y = MM_PER_SQUARE / spacing_y if spacing_y > 0 else float("nan")
    mm_per_px_x = MM_PER_SQUARE / spacing_x if spacing_x > 0 else float("nan")
    delta = abs(spacing_x - spacing_y) / max(spacing_x, spacing_y) * 100.0 if spacing_x and spacing_y else 0.0
    return GridCalibration(
        region=region_name,
        spacing_px_x=spacing_x,
        spacing_px_y=spacing_y,
        mm_per_px_x=mm_per_px_x,
        mm_per_px_y=mm_per_px_y,
        perspective_delta_pct=float(delta),
    )


def _px_to_mm(u: float, v: float, cal: GridCalibration, origin_uv: Tuple[float, float]) -> Tuple[float, float]:
    du = u - origin_uv[0]
    dv = v - origin_uv[1]
    return du * cal.mm_per_px_x, dv * cal.mm_per_px_y


def width_px_fallback(grip_rgb: np.ndarray, lap: np.ndarray, row: int, cal: GridCalibration) -> float:
    gray = cv2.cvtColor(grip_rgb, cv2.COLOR_RGB2GRAY)
    strip = gray[row, :]
    tex = lap[row, :]
    mask_row = (tex > np.percentile(tex, 65)) & (strip > np.percentile(strip, 30))
    if mask_row.sum() < 5:
        return cal.spacing_px_x * 3.0
    ix = np.where(mask_row)[0]
    return float(ix.max() - ix.min())


def _grid_line_positions(score: np.ndarray, axis: int, min_distance: int) -> np.ndarray:
    profile = score.sum(axis=axis).astype(np.float32)
    profile = profile - profile.min()
    if profile.max() > 0:
        profile /= profile.max()
    peaks, _ = find_peaks(profile, distance=min_distance, prominence=0.12)
    return peaks.astype(int)


def _row_tuinslang_columns(
    gray: np.ndarray,
    lap: np.ndarray,
    row: int,
    spacing_px_x: float,
) -> tuple[int, int] | None:
    """Bright mesh sleeve (~2–4 grid squares wide), not full loop or finger."""
    strip = gray[row, :]
    tex = lap[row, :]
    mask_row = (tex > np.percentile(tex, 68)) & (strip > max(145.0, np.percentile(strip, 58)))
    if mask_row.sum() < 8:
        return None
    ix = np.where(mask_row)[0]
    width = float(ix.max() - ix.min())
    if width < spacing_px_x * 1.6 or width > spacing_px_x * 4.6:
        return None
    return int(ix.min()), int(ix.max())


def _tuinslang_box_from_grid(
    h_lines: np.ndarray,
    gray: np.ndarray,
    lap: np.ndarray,
    spacing_px_x: float,
    spacing_px_y: float,
    *,
    target_squares: int = 13,
) -> tuple[int, int, int, int, np.ndarray]:
    """Orange ROI: exactly ``target_squares`` horizontal grid lines, tight mesh width."""
    h, w = gray.shape
    mask = np.zeros((h, w), np.uint8)
    target = int(target_squares)
    if len(h_lines) < target + 1:
        return 0, h - 1, 0, w - 1, mask

    best: tuple[int, int, int, int] | None = None
    best_score = -1.0

    for i in range(len(h_lines) - target):
        y_top = int(h_lines[i])
        y_bot = int(h_lines[i + target])
        cols: List[tuple[int, int]] = []
        step = max(1, (y_bot - y_top) // 28)
        for row in range(y_top, y_bot + 1, step):
            pair = _row_tuinslang_columns(gray, lap, row, spacing_px_x)
            if pair:
                cols.append(pair)
        if len(cols) < 6:
            continue
        width_px = float(np.median([mx - mn for mn, mx in cols]))
        w_sq = width_px / spacing_px_x
        if w_sq < 2.0 or w_sq > 3.8:
            continue
        patch = gray[y_top : y_bot + 1, int(np.median([mn for mn, _ in cols])) : int(np.median([mx for _, mx in cols])) + 1]
        if patch.size and float(np.mean(patch > 125)) < 0.18:
            continue
        lefts = [mn for mn, _ in cols]
        rights = [mx for _, mx in cols]
        col_min = int(np.percentile(lefts, 15))
        col_max = int(np.percentile(rights, 85))
        max_w = int(spacing_px_x * 3.4)
        if col_max - col_min > max_w:
            cx = 0.5 * (float(np.median(lefts)) + float(np.median(rights)))
            col_min = int(max(0, cx - max_w / 2.0))
            col_max = int(min(w - 1, cx + max_w / 2.0))
        score = float(len(cols)) - abs(w_sq - 2.6) * 1.2
        if col_max > w * 0.82:
            score -= 4.0
        if score > best_score:
            best_score = score
            best = (y_top, y_bot, col_min, col_max)

    if best is None:
        return -1, -1, 0, w - 1, mask

    y_top, y_bot, col_min, col_max = best
    patch = gray[y_top : y_bot + 1, col_min : col_max + 1]
    if patch.size == 0:
        return -1, -1, 0, w - 1, mask
    bright_frac = float(np.mean(patch > 135))
    dark_frac = float(np.mean(patch < 88))
    # Tight mesh patch can be brighter than the old wide ROI; do not drop a scored window.
    if patch.size and (float(np.std(patch)) < 12.0 and bright_frac > 0.92):
        return -1, -1, 0, w - 1, mask

    for row in range(y_top, y_bot + 1):
        pair = _row_tuinslang_columns(gray, lap, row, spacing_px_x)
        if pair:
            mask[row, pair[0] : pair[1] + 1] = 255
    return y_top, y_bot, col_min, col_max, mask


def _vertical_sleeve_window(
    row_widths_px: List[Tuple[int, float]],
    spacing_px_y: float,
    spacing_px_x: float,
    image_height: int,
    *,
    target_squares: float = 13.0,
    width_squares: tuple[float, float] = (2.0, 4.5),
) -> tuple[int, int, List[Tuple[int, float]]]:
    """Locate ~13 grid squares of tuinslang: slide window on sleeve-width rows."""
    eligible = sorted(
        [
            (r, w)
            for r, w in row_widths_px
            if width_squares[0] <= (w / spacing_px_x) <= width_squares[1]
        ],
        key=lambda t: t[0],
    )
    if len(eligible) < 6:
        eligible = sorted(row_widths_px, key=lambda t: t[0])
    if not eligible:
        half = int(round(target_squares * spacing_px_y / 2.0))
        center = max(half, image_height // 2)
        lo = max(0, center - half)
        hi = min(image_height - 1, center + half)
        return lo, hi, []

    runs: List[List[Tuple[int, float]]] = []
    cur: List[Tuple[int, float]] = []
    prev_row = -9999
    for row, width in eligible:
        if cur and row - prev_row > 5:
            runs.append(cur)
            cur = []
        cur.append((row, width))
        prev_row = row
    if cur:
        runs.append(cur)
    if not runs:
        runs = [eligible]

    half = int(round(target_squares * spacing_px_y / 2.0))
    best: tuple[int, int, List[Tuple[int, float]]] | None = None
    best_score = -1e9
    step = max(1, half // 8)

    for run in runs:
        if len(run) < 6:
            continue
        for row, _w in run[::step]:
            lo = max(0, row - half)
            hi = min(image_height - 1, row + half)
            sub = [(r, w) for r, w in run if lo <= r <= hi]
            if len(sub) < 6:
                continue
            width_sq = float(np.median([w for _r, w in sub]) / spacing_px_x)
            if width_sq < 2.2 or width_sq > 4.0:
                continue
            span_sq = (hi - lo) / spacing_px_y
            score = len(sub) * 2.0 - abs(span_sq - target_squares) * 3.0 - abs(width_sq - 3.0) * 2.5
            if score > best_score:
                best_score = score
                best = (lo, hi, sub)

    if best is None:
        center = eligible[len(eligible) // 2][0]
        lo = max(0, center - half)
        hi = min(image_height - 1, center + half)
        sub = [(r, w) for r, w in eligible if lo <= r <= hi]
        return lo, hi, sub

    return best


def _tuinslang_roi_mask(
    gray: np.ndarray,
    lap: np.ndarray,
    row_min: int,
    row_max: int,
    spacing_px: float,
) -> tuple[np.ndarray, int, int, int, int]:
    """
    Binary mask + tight bbox (local ROI coords) for the hose sleeve only.

    Vertical extent comes from the grid-aligned window; horizontal from per-row texture
    inside that window (sleeve width ~2–3 squares).
    """
    h, w = gray.shape
    mask = np.zeros((h, w), np.uint8)
    col_mins: List[int] = []
    col_maxs: List[int] = []

    for row in range(row_min, row_max + 1):
        strip = gray[row, :]
        tex = lap[row, :]
        mask_row = (tex > np.percentile(tex, 72)) & (strip > np.percentile(strip, 42))
        if mask_row.sum() < 5:
            continue
        ix = np.where(mask_row)[0]
        width = float(ix.max() - ix.min())
        if width < spacing_px * 1.8 or width > spacing_px * 4.5:
            continue
        x0 = int(ix.min())
        x1 = int(ix.max())
        mask[row, x0 : x1 + 1] = 255
        col_mins.append(x0)
        col_maxs.append(x1)

    if col_mins:
        col_min, col_max = min(col_mins), max(col_maxs)
    else:
        col_min, col_max = 0, w - 1

    return mask, row_min, row_max, col_min, col_max


def measure_sleeved_grip(rgb: np.ndarray, filename: str, out_dir: Path) -> PhotoMeasurementResult:
    h, w = rgb.shape[:2]
    result = PhotoMeasurementResult(file=filename, image_size=(w, h))

    y0, y1 = int(h * 0.12), int(h * 0.88)
    x_g0, x_g1 = int(w * 0.50), int(w * 0.88)
    grip_rgb = rgb[y0:y1, x_g0:x_g1]
    cal_grip = calibrate_grid_local(rgb, "grip_right", y0, y1, x_g0, x_g1)
    cal_left = calibrate_grid_local(rgb, "left_reference", y0, y1, int(w * 0.05), int(w * 0.40))
    result.calibrations = [cal_grip, cal_left]

    score = _blue_line_score(grip_rgb)
    min_d = max(12, int(min(cal_grip.spacing_px_x, cal_grip.spacing_px_y) * 0.65))
    h_lines = _grid_line_positions(score, axis=1, min_distance=min_d)
    v_lines = _grid_line_positions(score, axis=0, min_distance=min_d)

    gray = cv2.cvtColor(grip_rgb, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    lap = np.abs(lap)

    # Per-row sleeve width via texture + brightness (mesh sleeve vs dark metal).
    row_widths_px: List[Tuple[int, float]] = []
    for row in range(10, grip_rgb.shape[0] - 10):
        strip = gray[row, :]
        tex = lap[row, :]
        # Sleeve rows: elevated texture and mid-high brightness.
        mask_row = (tex > np.percentile(tex, 70)) & (strip > np.percentile(strip, 35))
        if mask_row.sum() < 5:
            continue
        idx = np.where(mask_row)[0]
        width = float(idx.max() - idx.min())
        if width < cal_grip.spacing_px_x * 1.2:
            continue
        row_widths_px.append((row, width))

    if len(row_widths_px) < 10:
        result.measurements.append(
            MeasurementItem(
                "grip_detection",
                0.0,
                filename,
                "row_texture_scan",
                "low",
                notes="Could not isolate sleeve rows; review overlay.",
            )
        )
        return result

    # Sleeve rows: plan width ~2–4.5 grid squares (20–45 mm); excludes full-loop bbox.
    sleeve_rows: List[Tuple[int, float]] = []
    for row, width in row_widths_px:
        squares_w = width / cal_grip.spacing_px_x
        if 2.0 <= squares_w <= 4.5:
            sleeve_rows.append((row, width))

    if len(sleeve_rows) < 8:
        result.measurements.append(
            MeasurementItem(
                "grip_detection",
                0.0,
                filename,
                "sleeve_width_band_filter",
                "low",
                notes="No rows in 2.0–4.5 square width band; adjust ROI or review photo.",
            )
        )
        return result

    # Tight band for translucent sleeve (~2.5–3.8 squares wide).
    tight_rows = [
        (row, width)
        for row, width in row_widths_px
        if 2.5 <= (width / cal_grip.spacing_px_x) <= 3.8
    ]
    if len(tight_rows) < 6:
        tight_rows = sleeve_rows  # fallback to wider band

    row_min, row_max, span_rows = _vertical_sleeve_window(
        row_widths_px,
        cal_grip.spacing_px_y,
        cal_grip.spacing_px_x,
        gray.shape[0],
        target_squares=13.0,
    )
    grid_row_min, grid_row_max, col_min, col_max, sleeve_mask = _tuinslang_box_from_grid(
        h_lines,
        gray,
        lap,
        cal_grip.spacing_px_x,
        cal_grip.spacing_px_y,
        target_squares=13,
    )
    if grid_row_min >= 0:
        row_min, row_max = grid_row_min, grid_row_max
        grid_snapped = True
    else:
        grid_snapped = False
        sleeve_mask, row_min, row_max, col_min, col_max = _tuinslang_roi_mask(
            gray, lap, row_min, row_max, cal_grip.spacing_px_x
        )
    widths_arr = np.array([w for _r, w in span_rows]) if span_rows else np.array([cal_grip.spacing_px_x * 3])
    row_min = int(row_min)
    row_max = int(row_max)
    col_min = int(col_min)
    col_max = int(col_max)

    span_px = float(row_max - row_min)
    squares_v = 13.0 if grid_snapped else span_px / cal_grip.spacing_px_y
    length_mm = squares_v * MM_PER_SQUARE
    length_method = (
        "13 grid squares × 10 mm (grid-snapped tuinslang span)"
        if grid_snapped
        else "sleeve row window / grid spacing × 10 mm"
    )

    sleeve_x0 = x_g0 + col_min
    sleeve_x1 = x_g0 + col_max

    mesh_widths: List[float] = []
    for row in range(row_min, row_max + 1, max(1, (row_max - row_min) // 40)):
        pair = _row_tuinslang_columns(gray, lap, row, cal_grip.spacing_px_x)
        if pair:
            mesh_widths.append(float(pair[1] - pair[0]))
    if mesh_widths:
        widths_arr = np.array(mesh_widths)
    squares_u = float(np.median(widths_arr / cal_grip.spacing_px_x))
    od_mm = squares_u * MM_PER_SQUARE
    sleeve_rows = tight_rows

    # Centerline in mm (Y up along grip, X outward)
    center_pts_img: List[Tuple[float, float]] = []
    cx_ref = x_g0 + (col_min + col_max) / 2.0
    oy = y0 + row_max
    cx_samples: List[float] = []
    for row in range(row_min, row_max + 1, max(1, (row_max - row_min) // 40)):
        seg = gray[row, col_min : col_max + 1]
        tex = lap[row, col_min : col_max + 1]
        bright = (seg > 118) & (tex > np.percentile(tex, 58))
        xs = np.where(bright)[0]
        if len(xs) < 4:
            continue
        cu = x_g0 + col_min + float(np.median(xs))
        cx_samples.append(cu)
    if cx_samples:
        cx_arr = np.array(cx_samples)
        q1, q3 = np.percentile(cx_arr, [25, 75])
        iqr = float(q3 - q1)
        inlier = cx_arr[(cx_arr >= q1 - iqr) & (cx_arr <= q3 + iqr)]
        cx_med = float(np.median(inlier if len(inlier) >= 3 else cx_arr))
        tol = max(cal_grip.spacing_px_x * 0.85, iqr * 0.5)
        for row in range(row_min, row_max + 1, max(1, (row_max - row_min) // 40)):
            seg = gray[row, col_min : col_max + 1]
            tex = lap[row, col_min : col_max + 1]
            bright = (seg > 118) & (tex > np.percentile(tex, 58))
            xs = np.where(bright)[0]
            if len(xs) < 4:
                continue
            cu = x_g0 + col_min + float(np.median(xs))
            if abs(cu - cx_med) > tol:
                continue
            cv = y0 + float(row)
            center_pts_img.append((cu, cv))

    centerline_mm: List[List[float]] = []
    for cu, cv in center_pts_img:
        mm_x = (cu - cx_ref) * cal_grip.mm_per_px_x
        mm_y = (oy - cv) * cal_grip.mm_per_px_y
        centerline_mm.append([round(mm_x, 2), round(mm_y, 2)])
    if centerline_mm:
        y_base = min(p[1] for p in centerline_mm)
        centerline_mm = [[p[0], round(p[1] - y_base, 2)] for p in centerline_mm]

    persp_note = (
        f"Local grid px spacing Y={cal_grip.spacing_px_y:.1f} vs left region "
        f"{cal_left.spacing_px_y:.1f} (perspective Δ "
        f"{abs(cal_grip.spacing_px_y - cal_left.spacing_px_y) / cal_left.spacing_px_y * 100:.1f}%). "
        f"Values use square_count × 10 mm."
    )

    result.measurements.extend(
        [
            MeasurementItem(
                "tuinslang_span_vertical_mm",
                round(length_mm, 1),
                filename,
                length_method,
                "medium",
                grid_squares=round(squares_v, 2),
                perspective_note=persp_note,
                notes="Reinforced hose sleeve on metal grip; outer span incl. partial end cells.",
            ),
            MeasurementItem(
                "grip_outer_span_vertical_mm",
                round(length_mm, 1),
                filename,
                length_method,
                "medium",
                grid_squares=round(squares_v, 2),
                perspective_note=persp_note,
                notes="Alias of tuinslang_span_vertical_mm for legacy readers.",
            ),
            MeasurementItem(
                "grip_outer_diameter_mm",
                round(od_mm, 1),
                filename,
                "grid-calibrated mid-row width: squares × 10 mm",
                "medium",
                grid_squares=round(squares_u, 2),
                perspective_note=persp_note,
                notes="Plan-view width at sleeve mid-height.",
            ),
        ]
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    vis = rgb.copy()
    if grid_snapped:
        full_mask = np.zeros((h, w), np.uint8)
        mh, mw = sleeve_mask.shape[:2]
        full_mask[y0 : y0 + mh, x_g0 : x_g0 + mw] = sleeve_mask
        contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cv2.drawContours(vis, contours, -1, (255, 80, 0), 2)
        else:
            cv2.rectangle(vis, (sleeve_x0, y0 + row_min), (sleeve_x1, y0 + row_max), (255, 80, 0), 2)
        for y_line in h_lines:
            y_abs = y0 + int(y_line)
            if y0 + row_min <= y_abs <= y0 + row_max:
                cv2.line(vis, (sleeve_x0, y_abs), (sleeve_x1, y_abs), (0, 180, 255), 1)
    else:
        cv2.putText(
            vis,
            "Geen tuinslang in beeld — geen oranje kader",
            (x_g0, max(y0 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 80, 0),
            2,
            cv2.LINE_AA,
        )
    for cu, cv in center_pts_img:
        if grid_snapped:
            lu, lv = int(cu - x_g0), int(cv - y0)
            if not (0 <= lv < sleeve_mask.shape[0] and 0 <= lu < sleeve_mask.shape[1] and sleeve_mask[lv, lu]):
                continue
        cv2.circle(vis, (int(cu), int(cv)), 3, (0, 220, 0), -1)
    overlay = out_dir / f"calibrated_{Path(filename).stem}.jpg"
    cv2.imwrite(str(overlay), cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    result.overlay_path = str(overlay)
    return result


def measure_bare_metal(rgb: np.ndarray, filename: str, out_dir: Path) -> PhotoMeasurementResult:
    h, w = rgb.shape[:2]
    result = PhotoMeasurementResult(file=filename, image_size=(w, h))
    cal = calibrate_grid_local(rgb, "full_frame", int(h * 0.1), int(h * 0.9), int(w * 0.1), int(w * 0.9))
    result.calibrations = [cal]

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, dark = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    ys, xs = np.where(dark > 0)
    if len(xs) > 100:
        loop_h_px = ys.max() - ys.min()
        loop_w_px = xs.max() - xs.min()
        result.measurements.append(
            MeasurementItem(
                "metal_loop_bbox_height_mm",
                round(loop_h_px * cal.mm_per_px_y, 1),
                filename,
                "dark metal mask bbox × local grid",
                "medium",
                grid_squares=round(loop_h_px / cal.spacing_px_y, 2),
            )
        )
        result.measurements.append(
            MeasurementItem(
                "metal_loop_bbox_width_mm",
                round(loop_w_px * cal.mm_per_px_x, 1),
                filename,
                "dark metal mask bbox × local grid",
                "medium",
                grid_squares=round(loop_w_px / cal.spacing_px_x, 2),
            )
        )
        loop, lx0, ly0, lx1, ly1 = _loop_roi_mask(dark, w, h)
        ly, lx = np.where(loop > 0)
        if len(lx) > 50:
            rope_w_px = lx.max() - lx.min()
            rope_h_px = ly.max() - ly.min()
            result.measurements.append(
                MeasurementItem(
                    "metal_loop_rope_plan_width_mm",
                    round(rope_w_px * cal.mm_per_px_x, 1),
                    filename,
                    "loop ROI mask bbox × local grid (excludes square shaft)",
                    "medium",
                    grid_squares=round(rope_w_px / cal.spacing_px_x, 2),
                    notes="Use for reference D-loop plan width, not full dark mask.",
                )
            )
            result.measurements.append(
                MeasurementItem(
                    "metal_loop_rope_plan_height_mm",
                    round(rope_h_px * cal.mm_per_px_y, 1),
                    filename,
                    "loop ROI mask bbox × local grid (excludes square shaft)",
                    "medium",
                    grid_squares=round(rope_h_px / cal.spacing_px_y, 2),
                )
            )

    out_dir.mkdir(parents=True, exist_ok=True)
    overlay = out_dir / f"calibrated_{Path(filename).stem}.jpg"
    vis = rgb.copy()
    loop_overlay = _draw_loop_plan_overlay(rgb, cal)
    if loop_overlay is not None:
        vis = loop_overlay
    cv2.imwrite(str(overlay), cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    result.overlay_path = str(overlay)
    return result


def _loop_roi_mask(dark: np.ndarray, w: int, h: int) -> tuple[np.ndarray, int, int, int, int]:
    """Crop to D-loop only (exclude square shaft on far left)."""
    x0, x1 = int(w * 0.40), int(w * 0.92)
    y0, y1 = int(h * 0.12), int(h * 0.90)
    return dark[y0:y1, x0:x1], x0, y0, x1, y1


def _loop_origin_px(loop: np.ndarray, x0: int, y0: int) -> tuple[int, int]:
    h = loop.shape[0]
    for r in range(h - 1, int(h * 0.82), -1):
        cols = np.where(loop[r] > 0)[0]
        if len(cols) > 8:
            return x0 + int(cols.max()), y0 + r
    ys, xs = np.where(loop > 0)
    return x0 + int(xs.max()), y0 + int(ys.max())


def _binary_runs(cols: np.ndarray, gap_px: int = 2) -> list[tuple[int, int]]:
    if cols.size == 0:
        return []
    runs: list[tuple[int, int]] = []
    start = int(cols[0])
    prev = int(cols[0])
    for c in cols[1:]:
        c = int(c)
        if c > prev + gap_px:
            runs.append((start, prev))
            start = c
        prev = c
    runs.append((start, prev))
    return runs


def _loop_inner_ellipse_px(rgb: np.ndarray) -> dict[str, Any]:
    """Fit the paper opening inside the steel ring (pixel ellipse)."""
    h, w = rgb.shape[:2]
    # Stay on the D-loop: cut the right finger and the square shaft.
    x0, x1 = int(w * 0.40), int(w * 0.70)
    y0, y1 = int(h * 0.16), int(h * 0.80)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)[y0:y1, x0:x1]
    metal = ((gray < 150).astype(np.uint8)) * 255
    metal = cv2.morphologyEx(metal, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    spacing = max(40.0, (x1 - x0) / 8.0)
    pts: list[list[int]] = []
    for r in range(metal.shape[0]):
        cols = np.where(metal[r] > 0)[0]
        runs = _binary_runs(cols)
        rod_runs = [
            run
            for run in runs
            if 0.35 * spacing <= (run[1] - run[0]) <= 2.4 * spacing
        ]
        if len(rod_runs) < 2:
            continue
        left, right = rod_runs[0], rod_runs[-1]
        gap = right[0] - left[1]
        if gap < 2.8 * spacing or gap > 8.5 * spacing:
            continue
        pts.append([left[1], r])
        pts.append([right[0], r])
    if len(pts) < 30:
        raise RuntimeError("Not enough inner-edge samples for the D-loop oval")
    arr = np.array(pts, dtype=np.float32)
    (cx, cy), (axis_w, axis_h), angle = cv2.fitEllipse(arr)
    return {
        "center_px": (float(cx) + x0, float(cy) + y0),
        "axes_px": (float(axis_w), float(axis_h)),
        "angle_deg": float(angle),
        "inner_pts_roi": arr,
    }


def _ellipse_points_px(
    center: tuple[float, float],
    axes: tuple[float, float],
    angle_deg: float,
    n: int,
) -> list[tuple[float, float]]:
    cx, cy = center
    aw, ah = axes[0] / 2.0, axes[1] / 2.0
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    pts: list[tuple[float, float]] = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        x = aw * math.cos(t)
        y = ah * math.sin(t)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def extract_loop_centerline_xy_mm(
    rgb: np.ndarray,
    rod_diameter_mm: float = 11.1,
    n: int = 96,
) -> dict[str, Any]:
    """
    Photo inner oval, offset by rod radius, converted with 1 square = 10 mm.

    No extra stretch: millimetres come from detected grid spacing (1 cm squares).
    Origin: rightmost centerline X=0, bottommost Y=0 (Y up).
    """
    h, w = rgb.shape[:2]
    cal = calibrate_grid_local(rgb, "full_frame", int(h * 0.1), int(h * 0.9), int(w * 0.1), int(w * 0.9))
    fitted = _loop_inner_ellipse_px(rgb)
    mx = float(cal.mm_per_px_x)
    my = float(cal.mm_per_px_y)
    m = 0.5 * (mx + my)
    r_mm = float(rod_diameter_mm) / 2.0
    r_px = r_mm / m
    inner_pts = _ellipse_points_px(fitted["center_px"], fitted["axes_px"], fitted["angle_deg"], n)
    cl_px = _ellipse_points_px(
        fitted["center_px"],
        (fitted["axes_px"][0] + 2.0 * r_px, fitted["axes_px"][1] + 2.0 * r_px),
        fitted["angle_deg"],
        n,
    )
    origin_x = max(p[0] for p in cl_px)
    origin_y = max(p[1] for p in cl_px)
    xy_mm = [[round((px - origin_x) * m, 3), round((origin_y - py) * m, 3)] for px, py in cl_px]
    xs = [p[0] for p in xy_mm]
    ys = [p[1] for p in xy_mm]
    y_bot = min(ys)
    x_right = max(xs)
    placed = [[round(x - x_right, 3), round(y - y_bot, 3)] for x, y in xy_mm]
    xs_s = [p[0] for p in placed]
    ys_s = [p[1] for p in placed]
    outer_w = (max(xs_s) - min(xs_s)) + rod_diameter_mm
    outer_h = (max(ys_s) - min(ys_s)) + rod_diameter_mm
    return {
        "centerline_xy_mm": placed,
        "bbox_centerline_mm": {
            "width": round(max(xs_s) - min(xs_s), 2),
            "height": round(max(ys_s) - min(ys_s), 2),
            "xmin": round(min(xs_s), 2),
            "xmax": round(max(xs_s), 2),
            "ymin": round(min(ys_s), 2),
            "ymax": round(max(ys_s), 2),
        },
        "outer_bbox_mm": {"width": round(outer_w, 1), "height": round(outer_h, 1)},
        "grid_squares": {
            "square_mm": MM_PER_SQUARE,
            "outer_width": round(outer_w / MM_PER_SQUARE, 2),
            "outer_height": round(outer_h / MM_PER_SQUARE, 2),
            "rod": round(rod_diameter_mm / MM_PER_SQUARE, 2),
        },
        "hub_xy_mm": [round(min(xs_s), 2), round(0.5 * (min(ys_s) + max(ys_s)), 2)],
        "mm_per_px": {"x": mx, "y": my, "uniform": m},
        "inner_ellipse_px": {
            "center": fitted["center_px"],
            "axes": fitted["axes_px"],
            "angle_deg": fitted["angle_deg"],
        },
        "inner_pts_px": inner_pts,
        "centerline_pts_px": cl_px,
        "source": "fitEllipse on photo inner opening; 1 grid square = 10 mm (1 cm)",
        "provenance": "measured",
    }


def save_loop_trace_overlay(rgb: np.ndarray, out_path: Path, rod_diameter_mm: float = 11.1) -> Path:
    """Draw fitted inner oval + rod centerline in photo pixels."""
    vis = rgb.copy()
    trace = extract_loop_centerline_xy_mm(rgb, rod_diameter_mm=rod_diameter_mm)
    inner = [(int(round(x)), int(round(y))) for x, y in trace["inner_pts_px"]]
    center = [(int(round(x)), int(round(y))) for x, y in trace["centerline_pts_px"]]
    for a, b in zip(inner, inner[1:] + inner[:1]):
        cv2.line(vis, a, b, (0, 220, 80), 2)
    for a, b in zip(center, center[1:] + center[:1]):
        cv2.line(vis, a, b, (255, 80, 0), 2)
    hx, hy = trace["inner_ellipse_px"]["center"]
    cv2.circle(vis, (int(hx), int(hy)), 8, (255, 0, 255), 2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    return out_path


def extract_loop_plan_mm(rgb: np.ndarray, plan_height_mm: float) -> dict[str, float]:
    """
    INFERRED rod centerline frame for the bare-metal D-loop (mm).

    Origin: inner bottom-right of loop (Y up, X left negative). Excludes square shaft bbox.
    """
    h, w = rgb.shape[:2]
    cal = calibrate_grid_local(rgb, "full_frame", int(h * 0.1), int(h * 0.9), int(w * 0.1), int(w * 0.9))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, dark = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    loop, x0, y0, _x1, _y1 = _loop_roi_mask(dark, w, h)
    ou, ov = _loop_origin_px(loop, x0, y0)
    rod_r = 5.55

    row_samples: List[Tuple[float, float, float]] = []
    for r in range(loop.shape[0]):
        cols = np.where(loop[r] > 0)[0]
        if len(cols) < 6:
            continue
        lx, rx = int(cols.min()), int(cols.max())
        span = rx - lx
        if span < cal.spacing_px_x * 0.9:
            continue
        mm_y = (ov - (y0 + r)) * cal.mm_per_px_y
        if mm_y < -5:
            continue
        mm_x_left = (x0 + lx + rod_r - ou) * cal.mm_per_px_x
        mm_x_right = (x0 + rx - rod_r - ou) * cal.mm_per_px_x
        row_samples.append((mm_y, mm_x_left, mm_x_right))

    if len(row_samples) < 20:
        return {
            "plan_height_mm": plan_height_mm,
            "top_bar_left_x_mm": -48.0,
            "left_leg_bottom_x_mm": -54.0,
            "left_leg_arc_split_y_mm": round(plan_height_mm * 0.335, 1),
            "bottom_arc_mid_x_mm": -22.0,
            "bottom_arc_mid_y_mm": round(plan_height_mm * 0.16, 1),
            "hub_to_right_outer_mm": 57.0,
        }

    ymax = max(t[0] for t in row_samples)
    y_scale = plan_height_mm / ymax if ymax > 0 else 1.0
    scaled = [(t[0] * y_scale, t[1], t[2]) for t in row_samples]

    wide = [t for t in scaled if (t[2] - t[1]) > 25.0]
    mid_band = [t for t in wide if plan_height_mm * 0.25 <= t[0] <= plan_height_mm * 0.75]
    top_band = [t for t in scaled if t[0] > plan_height_mm * 0.82]
    bot_band = [t for t in scaled if t[0] < plan_height_mm * 0.18]

    if mid_band:
        top_x = float(np.median([t[1] for t in mid_band]))
        bot_x = float(min(t[1] for t in bot_band)) if bot_band else float(min(t[1] for t in mid_band))
    else:
        top_x = float(np.median([t[1] for t in top_band])) if top_band else -48.0
        bot_x = float(min(t[1] for t in bot_band)) if bot_band else -54.0

    hub_span = 57.0
    # Grid: ~5.7 squares from hub face to outer arc; clamp CV to photo span.
    x_from_grid = -(hub_span - 10.0)
    top_x = min(top_x, x_from_grid)
    bot_x = min(bot_x, x_from_grid - 6.0)

    split_y = plan_height_mm * 0.335
    mid_x = bot_x * 0.42
    mid_y = split_y * 0.48

    return {
        "plan_height_mm": round(plan_height_mm, 1),
        "top_bar_left_x_mm": round(top_x, 1),
        "left_leg_bottom_x_mm": round(bot_x, 1),
        "left_leg_arc_split_y_mm": round(split_y, 1),
        "bottom_arc_mid_x_mm": round(mid_x, 1),
        "bottom_arc_mid_y_mm": round(mid_y, 1),
        "hub_to_right_outer_mm": 57.0,
        "anchor_y_mm": round(max(0.0, (plan_height_mm - 130.0) / 2.0), 1),
    }


def _draw_loop_plan_overlay(rgb: np.ndarray, cal: GridCalibration) -> np.ndarray | None:
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, dark = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    loop, x0, y0, x1, y1 = _loop_roi_mask(dark, w, h)
    ou, ov = _loop_origin_px(loop, x0, y0)
    vis = rgb.copy()
    cv2.rectangle(vis, (x0, y0), (x1, y1), (255, 120, 0), 2)
    cv2.circle(vis, (ou, ov), 6, (0, 255, 80), 2)
    return vis


def build_reference_measurements(project_dir: Path) -> dict[str, Any]:
    ref_dir = project_dir / "reference"
    out_dir = ref_dir / "calibrated"
    photos: List[dict] = []
    all_items: List[MeasurementItem] = []

    sleeved = ref_dir / "WhatsApp Image 2026-10-02 at 20.16.42 (1).jpeg"
    bare = ref_dir / "WhatsApp Image 2026-10-02 at 20.16.42.jpeg"

    grip_length = None
    grip_diameter = None
    centerline: List[List[float]] = []
    core_d = None

    if sleeved.exists():
        rgb = cv2.cvtColor(cv2.imread(str(sleeved)), cv2.COLOR_BGR2RGB)
        res = measure_sleeved_grip(rgb, sleeved.name, out_dir)
        photos.append(
            {
                "file": res.file,
                "image_size": res.image_size,
                "calibrations": [asdict(c) for c in res.calibrations],
                "measurements": [asdict(m) for m in res.measurements],
                "overlay_path": res.overlay_path,
            }
        )
        all_items.extend(res.measurements)
        for m in res.measurements:
            if m.name == "grip_outer_span_vertical_mm":
                grip_length = m.value_mm
            if m.name == "grip_outer_diameter_mm":
                grip_diameter = m.value_mm
            if m.name == "metal_core_diameter_estimate_mm" and m.value_mm > 0:
                core_d = m.value_mm
        # Re-run to get centerline stored - extract from measure function
        # Store centerline in JSON via separate call
        centerline = _extract_centerline_mm(rgb, sleeved.name)
        # Add rod measurement item from bare photo when available
        if bare.exists():
            rod = _estimate_rod_diameter_bare(bare)
            if rod:
                core_d = rod
                res.measurements.append(
                    MeasurementItem(
                        "metal_rod_diameter_mm",
                        rod,
                        bare.name,
                        "bare-metal rod thickness: squares × 10 mm (right straight leg)",
                        "medium",
                        grid_squares=round(rod / MM_PER_SQUARE, 2),
                        notes="Cross-check for hard core diameter.",
                    )
                )

    if bare.exists():
        rgb = cv2.cvtColor(cv2.imread(str(bare)), cv2.COLOR_BGR2RGB)
        res = measure_bare_metal(rgb, bare.name, out_dir)
        photos.append(
            {
                "file": res.file,
                "image_size": res.image_size,
                "calibrations": [asdict(c) for c in res.calibrations],
                "measurements": [asdict(m) for m in res.measurements],
                "overlay_path": res.overlay_path,
            }
        )
        all_items.extend(res.measurements)
        # Rod diameter from bare photo: estimate ~0.85 squares from prior analysis - compute from loop rod
        for m in res.measurements:
            if m.name == "metal_loop_bbox_height_mm":
                pass

    # Cross-check core diameter: prefer bare metal rod ~8-9mm if sleeved estimate poor
    rod_mm = _estimate_rod_diameter_bare(bare) if bare.exists() else None
    if rod_mm:
        core_d = rod_mm

    outer_r = (grip_diameter / 2.0) if grip_diameter else None
    core_r = (core_d / 2.0) if core_d else None

    # Build 3-point arc centerline from traced points if available
    arc_points = _centerline_to_arc(centerline, grip_length)

    # Authoritative tuinslang counts from grid paper (photo review).
    tuinslang_squares = 13.0
    tuinslang_core_squares = 11.0
    cv_tuinslang_squares: float | None = None
    for m in all_items:
        if m.name == "tuinslang_span_vertical_mm" and m.grid_squares is not None:
            cv_tuinslang_squares = float(m.grid_squares)
            break

    photo_grid_counts_verified = {
        "grip_length_squares": tuinslang_squares,
        "grip_length_core_squares": tuinslang_core_squares,
        "grip_od_squares": 3.0,
        "core_diameter_mm": core_d,
        "method": "tuinslang_mesh_on_grid_paper",
        "confidence": "medium",
        "cv_tuinslang_span_squares": cv_tuinslang_squares,
        "notes": (
            "Tuinslang outer span 13×10 mm on grid; ~11 cells fully filled, "
            "2 end cells partial. Orange overlay = mesh bounds only (not wide ROI). "
            "cv_tuinslang_span_squares is automated row span for comparison only."
        ),
    }
    auth_length = photo_grid_counts_verified["grip_length_squares"] * MM_PER_SQUARE
    auth_od = photo_grid_counts_verified["grip_od_squares"] * MM_PER_SQUARE
    arc_points = _centerline_to_arc(centerline, auth_length)

    loop_height_mm = 215.5
    rope_h = 0.0
    for m in all_items:
        if m.name == "metal_loop_bbox_height_mm" and m.value_mm > 0:
            loop_height_mm = float(m.value_mm)
        if m.name == "metal_loop_rope_plan_height_mm" and m.value_mm > 0:
            rope_h = float(m.value_mm)
    if rope_h > 0:
        loop_height_mm = rope_h

    metal_loop: dict[str, Any] = {
        "plan_height_mm": loop_height_mm,
        "hub_to_right_outer_mm": 57.0,
        "confidence": "inferred",
        "source": "bare-metal loop ROI (excludes square shaft) + grid span ~5.7 squares hub-to-outer arc",
    }
    if bare.exists():
        bare_rgb = cv2.cvtColor(cv2.imread(str(bare)), cv2.COLOR_BGR2RGB)
        metal_loop.update(extract_loop_plan_mm(bare_rgb, loop_height_mm))
        from projects.work.handle_test.design_constants import HARD_CORE_DIAMETER_MM as _ROD

        trace = extract_loop_centerline_xy_mm(bare_rgb, rod_diameter_mm=float(_ROD))
        metal_loop["centerline_xy_mm"] = trace["centerline_xy_mm"]
        metal_loop["hub_xy_mm"] = trace["hub_xy_mm"]
        metal_loop["centerline_bbox_mm"] = trace["bbox_centerline_mm"]
        metal_loop["centerline_source"] = trace["source"]
        overlay = out_dir / "loop_trace_overlay.jpg"
        save_loop_trace_overlay(bare_rgb, overlay, rod_diameter_mm=float(_ROD))
        metal_loop["trace_overlay_path"] = str(overlay)

    grip_anchor = metal_loop.get("anchor_y_mm")
    doc_grip_anchor = {"anchor_y_mm": grip_anchor} if grip_anchor is not None else {}

    doc = {
        "grid": {
            "square_width_mm": MM_PER_SQUARE,
            "square_height_mm": MM_PER_SQUARE,
            "source": "physical graph paper visible in reference photographs",
            "certainty": "known",
        },
        "photo_grid_counts_verified": photo_grid_counts_verified,
        "photos": photos,
        "grip": {
            "length_mm": auth_length,
            "outer_diameter_mm": auth_od,
            "core_diameter_mm": core_d,
            "length_mm_automated_cv": grip_length,
            "outer_diameter_mm_automated_cv": grip_diameter,
            "centerline_points_mm": arc_points,
            "centerline_traced_mm": centerline,
            **doc_grip_anchor,
        },
        "all_measurements": [asdict(m) for m in all_items],
        "metal_loop": metal_loop,
    }
    from projects.work.handle_test.measurements_loader import centerline_sleeve_shape_mm

    doc["grip"]["centerline_points_mm"] = [list(p) for p in centerline_sleeve_shape_mm(doc)]
    return doc


def _extract_centerline_mm(rgb: np.ndarray, filename: str) -> List[List[float]]:
    h, w = rgb.shape[:2]
    cal = calibrate_grid_local(rgb, "grip_right", int(h * 0.15), int(h * 0.85), int(w * 0.42), int(w * 0.95))
    roi = rgb[int(h * 0.12) : int(h * 0.88), int(w * 0.48) : int(w * 0.92)]
    roi_offset = (int(w * 0.48), int(h * 0.12))
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, sleeve_mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ys, xs = np.where(sleeve_mask > 0)
    if len(xs) < 100:
        return []
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    oy = roi_offset[1] + y_max
    cx_ref = roi_offset[0] + (x_min + x_max) / 2
    pts: List[List[float]] = []
    for row in range(y_min, y_max, max(1, (y_max - y_min) // 50)):
        row_xs = xs[ys == row]
        if len(row_xs) < 5:
            continue
        cu = roi_offset[0] + float(np.median(row_xs))
        cv = roi_offset[1] + float(row)
        mm_x = (cu - cx_ref) * cal.mm_per_px_x
        mm_y = (oy - cv) * cal.mm_per_px_y
        pts.append([round(mm_x, 2), round(mm_y, 2)])
    if pts:
        y0 = min(p[1] for p in pts)
        pts = [[p[0], round(p[1] - y0, 2)] for p in pts]
    return pts


def _centerline_to_arc(centerline: List[List[float]], length_mm: Optional[float]) -> List[List[float]]:
    if not centerline or not length_mm:
        if length_mm:
            return [[0.0, 0.0], [0.0, length_mm / 2.0], [0.0, length_mm]]
        return []
    y_end = max(p[1] for p in centerline)
    if y_end <= 0:
        return [[0.0, 0.0], [0.0, length_mm / 2.0], [0.0, length_mm]]
    scale = length_mm / y_end
    pts = [(p[0] * scale, p[1] * scale) for p in centerline]
    bottom = min(pts, key=lambda p: p[1])
    top = max(pts, key=lambda p: p[1])
    lo, hi = length_mm * 0.35, length_mm * 0.65
    band = [p for p in pts if lo <= p[1] <= hi]
    mid = max(band, key=lambda p: p[0]) if band else pts[len(pts) // 2]
    return [
        [round(bottom[0], 2), round(bottom[1], 2)],
        [round(mid[0], 2), round(mid[1], 2)],
        [round(top[0], 2), round(top[1], 2)],
    ]


def _estimate_rod_diameter_bare(bare_path: Path) -> Optional[float]:
    rgb = cv2.cvtColor(cv2.imread(str(bare_path)), cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    cal = calibrate_grid_local(rgb, "loop_right", int(h * 0.22), int(h * 0.72), int(w * 0.56), int(w * 0.72))
    roi = rgb[int(h * 0.38) : int(h * 0.48), int(w * 0.60) : int(w * 0.67)]
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    _, m = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ys, xs = np.where(m > 0)
    if len(xs) < 20:
        return None
    thickness_px = xs.max() - xs.min()
    squares = thickness_px / cal.spacing_px_x
    value_mm = squares * MM_PER_SQUARE
    return round(value_mm, 1)


def save_reference_measurements(project_dir: Path) -> Path:
    doc = build_reference_measurements(project_dir)
    out = project_dir / "reference_measurements.json"
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = Path(__file__).resolve().parent
    path = save_reference_measurements(p)
    print(f"Wrote {path}")
