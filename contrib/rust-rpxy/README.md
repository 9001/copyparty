# rust-rpxy for copyparty

Configuration and testing files for using rust-rpxy as a reverse proxy with copyparty.

## Files

- `rpxy.toml` - rust-rpxy sample configuration file
- `test_config.sh` - Script to validate and test the configuration

## Usage

### Quick Test

Run the validation script to check the rpxy configuration:

```bash
./test_config.sh
```

### Full Functional Test

To test the complete proxy functionality:

1. Start copyparty server:
   ```bash
   copyparty -p 3923
   ```

2. Start rust-rpxy with the configuration:
   ```bash
   podman run -d --name rpxy-test-container -p 127.0.0.1:8080:8080 -p 127.0.0.1:8443:8443 -v /RPXY_PATH/rpxy.toml:/etc/rpxy.toml:ro,z -v /CERTS_PATH/certs:/certs:ro,z -e LOG_TO_FILE=false -e HOST_USER=daemon -e HOST_UID=1 -e HOST_GID=1 ghcr.io/junkurihara/rust-rpxy:nightly-s2n
   ```

3. Access the service through the proxy (by default on port 8080):
   ```bash
   curl http://localhost:8080/
   ```

## TLS

Check the sources of `test_config.sh` to see how to generate test TLS certificates.

You enable TLS by uncommenting the `tls` section in `rpxy.toml`.
