PYTHON="python3"
PROTOC="${PYTHON} -m grpc_tools.protoc"
REQUIREMENTS="./requirements.txt"

SRC_DIR="src"
VENV_DIR=".venv"
PROTO_DIR="${SRC_DIR}/gRPC/protos"

manage_venv() {
	$PYTHON -m venv "${VENV_DIR}"
	."${VENV_DIR}/bin/activate"
}

generate_gRPC() {
	$PROTOC -l "${PROTO_DIR}" --python-out="${SRC_DIR}" --pyi_out="${SRC_DIR}" --grpc_python_out="${SRC_DIR}""${PROTO_DIR}"/*.proto
}

install_requirements() {
	$PYTHON -m pip install --upgrade pip
	$PYTHON -m pip install -r $REQUIREMENTS
}

manage_venv

install_requirements
