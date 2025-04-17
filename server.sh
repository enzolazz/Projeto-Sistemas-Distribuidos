source ./environment.sh

source_venv

$PYTHON "$SRC_DIR/server.py" "$@"
