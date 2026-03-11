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


def _horizontal_overlap(left_rect, right_rect):
    left = max(left_rect['x'], right_rect['x'])
    right = min(_rect_right(left_rect), _rect_right(right_rect))
    return max(0, right - left)


def _can_merge_rows(previous_rect, current_rect):
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0

    height_threshold = max(8, int(min(previous_rect['height'], current_rect['height']) * 0.8))
    if vertical_gap > height_threshold:
        return False

    overlap = _horizontal_overlap(previous_rect, current_rect)
    min_width = max(1, min(previous_rect['width'], current_rect['width']))
    return overlap >= int(min_width * 0.25)


def group_rows_into_paragraphs(rows):
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

    paragraphs = []
    current = None
    previous_row = None
    for row in normalized:
        if current is None or not _can_merge_rows(previous_row['rect'], row['rect']):
            current = {
                'text': row['text'],
                'rows': [row],
                'rect': dict(row['rect']),
            }
            paragraphs.append(current)
        else:
            current['text'] = f"{current['text']}\n{row['text']}"
            current['rows'].append(row)
            rect = current['rect']
            right = max(_rect_right(rect), _rect_right(row['rect']))
            bottom = max(_rect_bottom(rect), _rect_bottom(row['rect']))
            rect['x'] = min(rect['x'], row['rect']['x'])
            rect['y'] = min(rect['y'], row['rect']['y'])
            rect['width'] = right - rect['x']
            rect['height'] = bottom - rect['y']
        previous_row = row

    return paragraphs
