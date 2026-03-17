import argparse
import json
import logging
import sys
import time

sys.path.insert(0, 'src')

from translation.bing_trans import BingBackend
from translation.sogou_trans import SogouBackend
from translation.youdao_trans import YoudaoBackend


def run_case(name, backend, text, src, tgt):
    t0 = time.time()
    try:
        result = backend.translate(text, target_lang=tgt, source_lang=src)
        ms = int((time.time() - t0) * 1000)
        if result and result.get('translated'):
            return {
                'backend': name,
                'ok': True,
                'latency_ms': ms,
                'translated': result.get('translated', ''),
            }
        return {
            'backend': name,
            'ok': False,
            'latency_ms': ms,
            'error': 'empty result',
        }
    except Exception as exc:
        ms = int((time.time() - t0) * 1000)
        return {
            'backend': name,
            'ok': False,
            'latency_ms': ms,
            'error': f'{type(exc).__name__}: {exc}',
        }


def main():
    parser = argparse.ArgumentParser(description='Quick translation backend regression checker')
    parser.add_argument('--text', default='hello world, this is a test.', help='Input text')
    parser.add_argument('--source', default='en', help='Source language code')
    parser.add_argument('--target', default='zh-CN', help='Target language code')
    parser.add_argument('--json', action='store_true', help='Output as JSON only')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    backends = [
        ('sogou', SogouBackend()),
        ('bing', BingBackend()),
        ('youdao', YoudaoBackend()),
    ]

    results = [
        run_case(name, backend, args.text, args.source, args.target)
        for name, backend in backends
    ]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for item in results:
        if item['ok']:
            print(f"[OK] {item['backend']:6} {item['latency_ms']:4}ms  {item['translated'][:120]}")
        else:
            print(f"[FAIL] {item['backend']:6} {item['latency_ms']:4}ms  {item.get('error', '')}")


if __name__ == '__main__':
    main()
