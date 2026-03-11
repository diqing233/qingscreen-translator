import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_run_rapidocr_returns_text_and_rows(monkeypatch):
    import ocr.engine
    from ocr.ocr_worker import OCRWorker

    worker = OCRWorker(None)

    monkeypatch.setattr(
        ocr.engine,
        'get_engine',
        lambda: lambda img: (
            [
                [[[0, 0], [30, 0], [30, 10], [0, 10]], 'First line', 0.99],
                [[[0, 18], [30, 18], [30, 28], [0, 28]], 'Second line', 0.98],
            ],
            0.01,
        ),
    )

    payload = worker._run_rapidocr(object())

    assert payload['text'] == 'First line Second line'
    assert payload['rows'] == [
        {
            'text': 'First line',
            'box': [[0, 0], [30, 0], [30, 10], [0, 10]],
        },
        {
            'text': 'Second line',
            'box': [[0, 18], [30, 18], [30, 28], [0, 28]],
        },
    ]


def test_run_rapidocr_scales_boxes_back_to_original_size(monkeypatch):
    import ocr.engine
    from ocr.ocr_worker import OCRWorker

    worker = OCRWorker(None)

    monkeypatch.setattr(
        ocr.engine,
        'get_engine',
        lambda: lambda img: (
            [
                [[[0, 0], [60, 0], [60, 20], [0, 20]], 'Scaled line', 0.99],
            ],
            0.01,
        ),
    )

    payload = worker._run_rapidocr(object(), scale=2)

    assert payload['rows'] == [
        {
            'text': 'Scaled line',
            'box': [[0, 0], [30, 0], [30, 10], [0, 10]],
        }
    ]
