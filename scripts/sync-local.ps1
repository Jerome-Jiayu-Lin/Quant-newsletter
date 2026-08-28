$ErrorActionPreference = 'Stop'

git pull --ff-only
python -m quantbrief.archive --database storage/archive/quant-brief.sqlite3
