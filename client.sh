source ./environment.sh

source_venv

$PYTHON "$SRC_DIR/gRPC/client.py" "$@"
