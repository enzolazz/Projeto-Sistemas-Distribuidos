PYTHON="python3"
PROTOC="${PYTHON} -m grpc_tools.protoc"
REQUIREMENTS="./requirements.txt"

SRC_DIR="$(pwd)/src"
VENV_DIR=".venv"
PROTO_DIR="${SRC_DIR}/gRPC/protos"
PACKAGES_DIR="${SRC_DIR}/packages"

source_venv() {
	. "${VENV_DIR}/bin/activate"
}

export PYTHONPATH="$PWD/src"
