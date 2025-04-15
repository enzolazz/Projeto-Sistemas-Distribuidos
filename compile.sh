set -e

PYTHON="python3"
PROTOC="${PYTHON} -m grpc_tools.protoc"
REQUIREMENTS="./requirements.txt"

SRC_DIR="src"
VENV_DIR=".venv"
PROTO_DIR="${SRC_DIR}/gRPC/protos"
PACKAGES_DIR="${SRC_DIR}/packages"

source_venv() {
	. "${VENV_DIR}/bin/activate"
}

generate_gRPC() {
	printf "\nGenerating gRPC code...\n"

	mkdir -p "${PACKAGES_DIR}"
	echo "from . import gRPC" >"${PACKAGES_DIR}/__init__.py"

	GRPC_PACKAGE_DIR="${PACKAGES_DIR}/gRPC"
	mkdir -p "${GRPC_PACKAGE_DIR}"
	touch "${GRPC_PACKAGE_DIR}/__init__.py"

	for proto_file in "${PROTO_DIR}"/*.proto; do
		$PROTOC -I"${PROTO_DIR}" \
			--python_out="${GRPC_PACKAGE_DIR}" \
			--pyi_out="${GRPC_PACKAGE_DIR}" \
			--grpc_python_out="${GRPC_PACKAGE_DIR}" \
			"$proto_file"

		filename="$(basename "$proto_file")"
		basename="${filename%.*}"

		echo "from . import ${basename}_pb2" >>"${GRPC_PACKAGE_DIR}/__init__.py"
		echo "from . import ${basename}_pb2_grpc" >>"${GRPC_PACKAGE_DIR}/__init__.py"

	done
}

install_requirements() {
	printf "\nInstalling requirements...\n"
	$PYTHON -m pip install --upgrade pip
	$PYTHON -m pip install -r $REQUIREMENTS
}

build() {
	printf "\nBuilding...\n"
	install_requirements
	generate_gRPC
}

clean() {
	printf "\nCleaning...\n"
	# rm -rf "${VENV_DIR}"
	rm -rf "${PACKAGES_DIR}"
}

$PYTHON -m venv "${VENV_DIR}"
source_venv

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

case $1 in
"clean")
	clean
	exit
	;;
"build")
	build
	exit
	;;
"") ;;
*)
	printf "Argumento não reconhecido: %s\n" $1
	exit 1
	;;
esac
