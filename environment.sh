export PYTHON="python3"
export PROTOC="${PYTHON} -m grpc_tools.protoc"
export REQUIREMENTS="./requirements.txt"

export SRC_DIR="$(pwd)/src"
export VENV_DIR=".venv"
export PROTO_DIR="${SRC_DIR}/gRPC/protos"
export PACKAGES_DIR="${SRC_DIR}/packages"

source_venv() {
	. "${VENV_DIR}/bin/activate"
}

export PYTHONPATH="$PWD/src"
