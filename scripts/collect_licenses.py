from importlib import metadata
from pathlib import Path
import argparse


def collect(output: Path):
    blocks = []
    for distribution in sorted(metadata.distributions(), key=lambda d: d.metadata.get('Name', '').lower()):
        name = distribution.metadata.get('Name', 'Unknown')
        texts = []
        for item in distribution.files or []:
            if Path(str(item)).name.lower().startswith(('license', 'copying', 'notice')):
                try:
                    texts.append(f'[{item}]\n' + Path(distribution.locate_file(item)).read_text(encoding='utf-8', errors='replace'))
                except OSError:
                    continue
        if texts:
            blocks.append(f'{name} {distribution.version}\n' + '\n\n'.join(texts))
    output.write_text('\n\n'.join(blocks), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    collect(parser.parse_args().output)
