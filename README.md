# 🌐 Network Performance Monitor

A sleek and powerful network monitoring tool built with Python and Streamlit. This application provides real-time insights into your system's network interfaces, hardware details, and performance metrics.

---

## Project Status

This project is currently in a **stable beta** phase. It is fully functional on Windows, but has limitations when running in a Linux container.

For more details on the limitations and future development, please see the `KNOWN_ISSUES.md` file.

---

## Features

-   **Available Network Interfaces:** Lists all network interfaces on your machine, displaying their IPv4 and IPv6 addresses.
-   **Hardware Information:** Provides detailed hardware specifications for your network adapters, including MAC address, link speed, and driver details. *(Note: This feature is only available when running on a native Windows host).*
-   **Performance Metrics:** Delivers real-time performance data for each interface, including bytes sent/received, latency, and throughput.

---

## Getting Started

### Prerequisites

-   Python 3.8+
-   Docker (optional, for containerized deployment)

---

## ⚙️ How to Run

You can run this application in two ways: locally on a Windows machine for full functionality, or via Docker for a cross-platform, containerized deployment with some limitations.

### 🖥️ Locally on Windows (Full Functionality)

This is the recommended method for experiencing the application's full capabilities.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit application:**
    ```bash
    streamlit run appoptimized.py
    ```

4.  Open your web browser and navigate to `http://localhost:8501`.

### 🐳 Using Docker (Limited Functionality)

This method uses a Linux container, which makes the application portable but with some important trade-offs.

1.  **Build and run the container using Docker Compose:**
    ```bash
    docker compose up --build
    ```

2.  Open your web browser and navigate to `http://localhost:8501`.

---

## ⚠️ Functionality Limitations in Docker

The official Docker deployment uses a standard **Linux container**. Due to the isolated nature of containers and platform differences, there are key limitations when running the application this way:

-   **Limited Network Visibility:** The application can only see the container's own virtual network interfaces (e.g., `lo`, `eth0`). It **cannot** see the host machine's full list of physical or virtual network adapters (like `Wi-Fi` or `Ethernet`).
-   **Hardware Information Disabled:** The "Hardware Information" section is **not available**. This feature relies on Windows-specific libraries (`wmi`) that are not present in the Linux container.

> **Why?** The application was originally designed for Windows. The Docker version is a cross-platform compatibility layer that allows it to run on any system, at the cost of losing direct access to the host's hardware.

---

## 🤝 Contributing

Contributions are welcome! If you would like to contribute to this project, please see the `CONTRIBUTING.md` file for more information.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
