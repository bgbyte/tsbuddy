from .extract_ts_tar import main as extract_all_cwd
from .extract_ts_tar import extract_tar_archive, decompress_gz_file, extract_archives

# from .legacy.extracttar import (
#     extract_tar_files, 
#     extract_gz_files, 
#     main
# )
__all__ = [
    'extract_tar_archive', 
    'decompress_gz_file', 
    'extract_archives',
    'extract_all_cwd',
]
