$ErrorActionPreference = 'Stop'

git pull --ff-only
python -m quantbrief.archive
