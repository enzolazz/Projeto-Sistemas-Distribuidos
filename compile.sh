. ./environment.sh

set -e

generate_gRPC() {
	printf "\nGenerating gRPC code...\n"

	GRPC_PACKAGE_DIR="${PACKAGES_DIR}/gRPC"
	mkdir -p "${GRPC_PACKAGE_DIR}"
	touch "${GRPC_PACKAGE_DIR}/__init__.py"

	$PROTOC -I"${PROTO_DIR}" \
		--python_out="${GRPC_PACKAGE_DIR}" \
		--pyi_out="${GRPC_PACKAGE_DIR}" \
		--grpc_python_out="${GRPC_PACKAGE_DIR}" \
		"${PROTO_DIR}"/*.proto
}

install_requirements() {
	printf "\nInstalling requirements...\n"
	$PYTHON -m pip install --upgrade pip
	$PYTHON -m pip install -r $REQUIREMENTS
}

build() {
	printf "\nBuilding...\n"

	if [ ! -d "${VENV_DIR}" ]; then
		printf "\nCreating virtual environment...\n"
		$PYTHON -m venv "${VENV_DIR}"
	else
		printf "\nVirtual environment already exists.\n"
	fi

	mkdir -p "${PACKAGES_DIR}"
	touch "${PACKAGES_DIR}/__init__.py"

	source_venv

	install_requirements
	generate_gRPC
}

clean() {
	printf "\nCleaning...\n"
	# rm -rf "${VENV_DIR}"
	rm -rf "${PACKAGES_DIR}"
}

case $1 in
"clean")
	clean
	exit
	;;
"") ;;
*)
	printf "Not a valid argument: %s\n" $1
	exit 1
	;;
esac

build
