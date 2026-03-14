def _rect_from_box(box):
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    left = min(xs)
    top = min(ys)
    right = max(xs)
    bottom = max(ys)
    return {
        'x': left,
        'y': top,
        'width': max(0, right - left),
        'height': max(0, bottom - top),
    }


def _rect_bottom(rect):
    return rect['y'] + rect['height']


def _rect_right(rect):
    return rect['x'] + rect['width']


def _rect_center_y(rect):
    return rect['y'] + (rect['height'] / 2.0)


def _horizontal_overlap(left_rect, right_rect):
    left = max(left_rect['x'], right_rect['x'])
    right = min(_rect_right(left_rect), _rect_right(right_rect))
    return max(0, right - left)


def _vertical_overlap(upper_rect, lower_rect):
    top = max(upper_rect['y'], lower_rect['y'])
    bottom = min(_rect_bottom(upper_rect), _rect_bottom(lower_rect))
    return max(0, bottom - top)


def _horizontal_gap(left_rect, right_rect):
    gap = right_rect['x'] - _rect_right(left_rect)
    return max(0, gap)


def _expand_rect(target_rect, source_rect):
    right = max(_rect_right(target_rect), _rect_right(source_rect))
    bottom = max(_rect_bottom(target_rect), _rect_bottom(source_rect))
    target_rect['x'] = min(target_rect['x'], source_rect['x'])
    target_rect['y'] = min(target_rect['y'], source_rect['y'])
    target_rect['width'] = right - target_rect['x']
    target_rect['height'] = bottom - target_rect['y']


def _can_merge_rows_into_line(previous_rect, current_rect):
    min_height = max(1, min(previous_rect['height'], current_rect['height']))
    overlap = _vertical_overlap(previous_rect, current_rect)
    center_delta = abs(_rect_center_y(previous_rect) - _rect_center_y(current_rect))
    same_line_band = max(6, int(max(previous_rect['height'], current_rect['height']) * 0.65))
    if overlap < int(min_height * 0.45) and center_delta > same_line_band:
        return False

    gap_threshold = max(12, int(max(previous_rect['height'], current_rect['height']) * 2.0))
    return _horizontal_gap(previous_rect, current_rect) <= gap_threshold


def _can_merge_lines(previous_rect, current_rect, gap_ratio: float = 0.0):
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0

    height_threshold = max(12, int(max(previous_rect['height'], current_rect['height']) * 1.6 * (1 + gap_ratio)))
    if vertical_gap > height_threshold:
        return False

    overlap = _horizontal_overlap(previous_rect, current_rect)
    min_width = max(1, min(previous_rect['width'], current_rect['width']))
    if overlap >= int(min_width * 0.15):
        return True

    indent_threshold = max(18, int(max(previous_rect['height'], current_rect['height']) * 2.5))
    return abs(previous_rect['x'] - current_rect['x']) <= indent_threshold


def _group_rows_into_lines(rows):
    lines = []
    current = None
    previous_row = None
    for row in rows:
        if current is None or not _can_merge_rows_into_line(previous_row['rect'], row['rect']):
            current = {
                'text': row['text'],
                'rows': [row],
                'rect': dict(row['rect']),
            }
            lines.append(current)
        else:
            current['text'] = f"{current['text']} {row['text']}".strip()
            current['rows'].append(row)
            _expand_rect(current['rect'], row['rect'])
        previous_row = row
    return lines


def group_rows_into_paragraphs(rows, gap_ratio: float = 0.0):
    normalized = []
    for row in rows or []:
        text = str(row.get('text', '')).strip()
        box = row.get('box') or []
        if not text or len(box) < 4:
            continue
        normalized.append({
            'text': text,
            'box': box,
            'rect': _rect_from_box(box),
        })

    normalized.sort(key=lambda row: (row['rect']['y'], row['rect']['x']))
    if not normalized:
        return []

    lines = _group_rows_into_lines(normalized)
    paragraphs = []
    current = None
    previous_line = None
    for line in lines:
        if current is None or not _can_merge_lines(previous_line['rect'], line['rect'], gap_ratio):
            current = {
                'text': line['text'],
                'rows': list(line['rows']),
                'rect': dict(line['rect']),
            }
            paragraphs.append(current)
        else:
            current['text'] = f"{current['text']}\n{line['text']}"
            current['rows'].extend(line['rows'])
            _expand_rect(current['rect'], line['rect'])
        previous_line = line

    return paragraphs
