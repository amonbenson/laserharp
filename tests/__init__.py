from pathlib import Path

# setup the output directory for test results (e. g. images)
OUTPUT_DIRECTORY = Path(__file__).parent / 'output'
if not OUTPUT_DIRECTORY.exists():
    OUTPUT_DIRECTORY.mkdir()
