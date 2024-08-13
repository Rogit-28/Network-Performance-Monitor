# TODO

## Future Updates

### Cross-Platform Network Interface Detection

- **Current Limitation:** The current Docker deployment uses a Linux container. As a result, the application can only see the container's own isolated network interfaces (`lo`, `eth0`) and not the full list of the host machine's network adapters. This significantly limits the application's primary network monitoring functionality. The "Hardware Information" section is also disabled.

- **Required Update:** To achieve full functionality in a cross-platform manner, the application needs to be refactored to use a different, platform-agnostic method for discovering and reporting on host network interfaces. This may involve exploring libraries that can abstract away the OS-specific details or finding alternative ways to pass host network information into the container.

- **Alternative:** For immediate full functionality, the application can be run in a Windows container. The `docker-deployment` branch contains a previous commit with a working Windows container implementation that can be used as a reference.
