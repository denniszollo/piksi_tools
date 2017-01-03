sudo tee /etc/udev/rules.d/99-piksi.rules <<EOF
ATTRS{idProduct}=="6014", ATTRS{idVendor}=="0403", MODE="666", GROUP="plugdev"
ATTRS{idProduct}=="8398", ATTRS{idVendor}=="0403", MODE="666", GROUP="plugdev"
ATTRS{idProduct}=="A4A7", ATTRS{idVendor}=="0525", MODE="666", GROUP="plugdev"
EOF
