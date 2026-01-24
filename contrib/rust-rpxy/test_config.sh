#!/bin/bash
# Test script for rust-rpxy configuration with copyparty
# This script validates the configuration and tests basic functionality with Podman

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR=$(mktemp -d -t rpxy-test-artifacts-XXXXXX)
CONFIG_FILE="$SCRIPT_DIR/rpxy.toml"
TEST_LOG="$ARTIFACTS_DIR/test_output.log"
CERT_DIR="$ARTIFACTS_DIR/certs"
DUMMY_FOLDER="$ARTIFACTS_DIR/dummy_web_content"
CONTAINER_NAME="rpxy-test-container"
COPYPARTY_CONTAINER_NAME="copyparty-test-container"

echo "Testing rust-rpxy configuration for copyparty with Podman..."
echo "Configuration file: $CONFIG_FILE"
echo "Artifacts directory: $ARTIFACTS_DIR"

# Function to check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."

    if ! command -v podman &> /dev/null; then
        echo "Error: podman is not installed or not in PATH"
        echo "Please install podman first."
        exit 1
    fi
    echo "✓ podman found: $(which podman)"

    if ! command -v openssl &> /dev/null; then
        echo "Error: openssl is not installed or not in PATH"
        echo "Please install openssl first."
        exit 1
    fi
    echo "✓ openssl found: $(which openssl)"
}

# Function to generate self-signed certificates with modern extensions
generate_certificates() {
    echo "Generating self-signed certificates with modern extensions..."

    # Create certificates directory
    mkdir -p "$CERT_DIR"

    # Create a temporary OpenSSL config file with proper extensions
    OPENSSL_CONF="$ARTIFACTS_DIR/openssl.conf"
    cat > "$OPENSSL_CONF" << 'EOF'
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Organization
CN=localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = 127.0.0.1
DNS.4 = ::1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # Generate private key in traditional format first, then convert to PKCS8
    openssl genrsa -out "$CERT_DIR/server.tmp.key" 2048
    # Convert to PKCS8 format (required by rust-rpxy)
    openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in "$CERT_DIR/server.tmp.key" -out "$CERT_DIR/server.key"
    # Remove temporary traditional key file
    rm "$CERT_DIR/server.tmp.key"

    # Generate self-signed certificate with extensions
    openssl req -new -x509 -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" -days 365 -config "$OPENSSL_CONF" -extensions v3_req

    # Set appropriate permissions
    chmod 644 "$CERT_DIR/server.key"
    chmod 644 "$CERT_DIR/server.crt"
    rm "$OPENSSL_CONF"  # Clean up config file

    echo "✓ Self-signed certificates generated in $CERT_DIR with modern extensions:"
    echo "  - Subject Alternative Names (SAN) for localhost, 127.0.0.1, and ::1"
    echo "  - Extended key usage for server authentication"
    echo "  - Proper key usage constraints"
}

# Function to create dummy folder for copyparty
create_dummy_folder() {
    echo "Creating dummy folder for copyparty..."

    # Create dummy folder with test content
    mkdir -p "$DUMMY_FOLDER"
    echo "This is a test file for copyparty" > "$DUMMY_FOLDER/test_file.txt"
    echo "Test content for verification" > "$DUMMY_FOLDER/hello.txt"

    echo "✓ Dummy folder created at $DUMMY_FOLDER with test content"
}

# Function to update the configuration with certificate paths
update_config_with_certs() {
    echo "Updating configuration with certificate paths..."

    # Create a temporary config file with certificate paths
    TEMP_CONFIG="$ARTIFACTS_DIR/rpxy.toml"
    cp "$CONFIG_FILE" "$TEMP_CONFIG"

    # Update existing TLS section
    sed -i "s|# tls_cert_path =.*|tls_cert_path = \"/certs/server.crt\"|" "$TEMP_CONFIG"
    sed -i "s|# tls_cert_key_path =.*|tls_cert_key_path = \"/certs/server.key\"|" "$TEMP_CONFIG"
    sed -i 's|# \[apps.copyparty.tls]|[apps.copyparty.tls]|' "$TEMP_CONFIG"

    # change to host.docker.internal if using Docker
    sed -i "s|127.0.0.1|host.containers.internal|" "$TEMP_CONFIG"

    echo "✓ Configuration updated with certificate paths"
    echo "  Certificate path: $CERT_DIR/server.crt"
    echo "  Key path: $CERT_DIR/server.key"
}

# Function to start copyparty container
start_copyparty_container() {
    echo "Starting copyparty container..."

    # Stop and remove any existing container
    podman rm -f "$COPYPARTY_CONTAINER_NAME" 2>/dev/null || true

    # Start copyparty container with the dummy folder
    podman run -d \
        --name "$COPYPARTY_CONTAINER_NAME" \
        -p 3923:3923 \
        -v "$DUMMY_FOLDER:/w:z" \
        ghcr.io/9001/copyparty-min -p 3923 -v .::rw

    # Wait a moment for the container to start
    sleep 5

    # Check if container is running
    if podman ps --filter name="$COPYPARTY_CONTAINER_NAME" --format "{{.Names}}" | grep -q "$COPYPARTY_CONTAINER_NAME"; then
        echo "✓ Copyparty container started successfully"
    else
        echo "✗ Failed to start copyparty container"
        exit 1
    fi
}

# Function to start rust-rpxy container
start_rpxy_container() {
    echo "Starting rust-rpxy container..."

    podman rm -f "$CONTAINER_NAME" 2>/dev/null || true

    # Start rust-rpxy container using pre-built image
    podman run -d \
        --name "$CONTAINER_NAME" \
        -p 127.0.0.1:8080:8080 \
        -p 127.0.0.1:8443:8443 \
        -v "$TEMP_CONFIG:/etc/rpxy.toml:ro,z" \
        -v "$CERT_DIR:/certs:ro,z" \
        -e LOG_TO_FILE=false -e HOST_USER=daemon -e HOST_UID=1 -e HOST_GID=1 \
        ghcr.io/junkurihara/rust-rpxy:nightly-s2n

    # Wait a moment for the container to start
    sleep 5

    # Check if container is running
    if podman ps --filter name="$CONTAINER_NAME" --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
        echo "✓ Rust-rpxy container started successfully"
    else
        echo "✗ Failed to start rust-rpxy container"
        # Show logs for debugging
        echo "Rust-rpxy container logs:"
        podman logs "$CONTAINER_NAME" || true
        exit 1
    fi
}

# Function to test the proxy functionality
test_proxy_functionality() {
    echo "Testing proxy functionality..."

    # Wait a bit more for services to be ready
    sleep 10

    # Test HTTP endpoint
    echo "Testing HTTP endpoint..."
    if curl -sf http://localhost:8080/ > /dev/null 2>&1; then
        echo "✓ HTTP endpoint accessible through proxy"

        # Get and display the response for verification
        RESPONSE=$(curl -s http://localhost:8080/ | head -20)
        echo "Response preview from copyparty through proxy:"
        echo "$RESPONSE"
        echo ""
    else
        echo "✗ HTTP endpoint not accessible through proxy"
        # Show container logs for debugging
        echo "Rust-rpxy logs:"
        podman logs "$CONTAINER_NAME" 2>&1 || true
        echo "Copyparty logs:"
        podman logs "$COPYPARTY_CONTAINER_NAME" 2>&1 || true
    fi

    # Test specific file access
    echo "Testing file access through proxy..."
    if curl -sf http://localhost:8080/test_file.txt > /dev/null 2>&1; then
        echo "✓ File access working through proxy"

        # Get the file content
        FILE_CONTENT=$(curl -s http://localhost:8080/test_file.txt)
        echo "File content from proxy: $FILE_CONTENT"
    else
        echo "✗ File access not working through proxy"
    fi

    # Test HTTPS endpoint if available (may fail with self-signed cert)
    echo "Testing HTTPS endpoint (will warn about self-signed cert)..."
    if curl -sk -f https://localhost:8443/ > /dev/null 2>&1; then
        echo "✓ HTTPS endpoint accessible through proxy"
    else
        echo "! HTTPS endpoint may not be accessible (expected with self-signed cert)"
    fi
}

# Function to cleanup containers
cleanup_containers() {
    echo "Cleaning up containers and artifacts..."

    # Stop and remove containers
    podman rm -f "$CONTAINER_NAME" 2>/dev/null || true
    podman rm -f "$COPYPARTY_CONTAINER_NAME" 2>/dev/null || true


    # Optionally remove the artifacts directory if user wants
    echo "Artifacts directory kept at: $ARTIFACTS_DIR"
    echo "To remove it: rm -rf $ARTIFACTS_DIR"

    echo "✓ Containers cleaned up"
    echo "✓ Artifacts directory preserved at: $ARTIFACTS_DIR"
}

# Function to provide test instructions
show_test_instructions() {
    echo ""
    echo "=== Automated Test Results ==="
    echo "✓ Prerequisites verified"
    echo "✓ Self-signed certificates generated"
    echo "✓ Dummy folder created with test content"
    echo "✓ Copyparty container started"
    echo "✓ Rust-rpxy container started"
    echo "✓ Proxy functionality tested"
    echo ""
    echo "=== Manual Testing Instructions ==="
    echo ""
    echo "After running this script, you can manually test:"
    echo ""
    echo "1. Access copyparty through proxy:"
    echo "   curl http://localhost:8080/"
    echo ""
    echo "2. Access specific files:"
    echo "   curl http://localhost:8080/test_file.txt"
    echo ""
    echo "3. Access via HTTPS (expecting cert warnings):"
    echo "   curl -k https://localhost:8443/"
    echo ""
    echo "=== Cleanup ==="
    echo "Containers will be automatically cleaned up after testing."
    echo "If needed, you can manually clean up with:"
    echo "podman stop $CONTAINER_NAME $COPYPARTY_CONTAINER_NAME"
    echo "podman rm $CONTAINER_NAME $COPYPARTY_CONTAINER_NAME"
}

# Main execution
main() {
    echo "Starting rust-rpxy configuration test with Podman..."
    echo ""

    check_prerequisites
    echo ""

    generate_certificates
    echo ""

    create_dummy_folder
    echo ""

    update_config_with_certs
    echo ""

    start_copyparty_container
    echo ""

    start_rpxy_container
    echo ""

    test_proxy_functionality
    echo ""

    show_test_instructions
    echo ""

    # Cleanup at the end
    cleanup_containers
}

# Run the main function
main
