set -e

PYTHON="python3"
PROTOC="${PYTHON} -m grpc_tools.protoc"
REQUIREMENTS="./requirements.txt"

SRC_DIR="src"
VENV_DIR=".venv"
PROTO_DIR="${SRC_DIR}/gRPC/protos"

source_venv() {
	. "${VENV_DIR}/bin/activate"
}

generate_gRPC() {
	printf "\nGenerating gRPC code...\n"
	$PROTOC -l "${PROTO_DIR}" --python-out="${SRC_DIR}" --pyi_out="${SRC_DIR}" --grpc_python_out="${SRC_DIR}""${PROTO_DIR}"/*.proto
}

install_requirements() {
	printf "\nInstalling requirements...\n"
	$PYTHON -m pip install --upgrade pip
	$PYTHON -m pip install -r $REQUIREMENTS
}

$PYTHON -m venv "${VENV_DIR}"
source_venv

install_requirements
generate_gRPC