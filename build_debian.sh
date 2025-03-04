#!/bin/bash

# Exit on error
set -e

# Create debian package structure
PACKAGE_NAME="financial-dashboard"
VERSION="1.0.0"
ARCH="armhf"
PACKAGE_DIR="${PACKAGE_NAME}_${VERSION}_${ARCH}"

echo "Building Debian package for $PACKAGE_NAME version $VERSION"

# Check if PyInstaller build exists
if [ ! -d "dist/FinancialDashboard" ]; then
    echo "Error: dist/FinancialDashboard directory not found!"
    echo "Please run 'pyinstaller dashboard.spec' first"
    exit 1
fi

# Create directory structure
echo "Creating package directory structure..."
mkdir -p $PACKAGE_DIR/DEBIAN
mkdir -p $PACKAGE_DIR/usr/local/bin/financial-dashboard
mkdir -p $PACKAGE_DIR/usr/share/applications

# Copy control file
echo "Copying control file..."
cp debian.control $PACKAGE_DIR/DEBIAN/control

# Copy application files
echo "Copying application files..."
cp -r dist/FinancialDashboard/* $PACKAGE_DIR/usr/local/bin/financial-dashboard/

# Copy .desktop file
echo "Creating .desktop file..."
cat > $PACKAGE_DIR/usr/share/applications/financial-dashboard.desktop << EOF
[Desktop Entry]
Name=Financial Dashboard
Comment=A Financial Dashboard Application
Exec=/usr/local/bin/financial-dashboard/FinancialDashboard
Icon=/usr/local/bin/financial-dashboard/icon.png
Terminal=false
Type=Application
Categories=Finance;
EOF

# Set permissions
echo "Setting permissions..."
chmod 755 $PACKAGE_DIR/DEBIAN/control
chmod -R 755 $PACKAGE_DIR/usr/local/bin/financial-dashboard
chmod 644 $PACKAGE_DIR/usr/share/applications/financial-dashboard.desktop

# Create postinst script
echo "Creating postinst script..."
cat > $PACKAGE_DIR/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e
# Update desktop database
update-desktop-database
EOF

chmod 755 $PACKAGE_DIR/DEBIAN/postinst

# Verify package structure
echo "Verifying package structure..."
if ! dpkg-deb --build $PACKAGE_DIR; then
    echo "Error: Package build failed!"
    exit 1
fi

# Verify the built package
echo "Verifying the built package..."
if ! dpkg-deb -I ${PACKAGE_DIR}.deb; then
    echo "Error: Package verification failed!"
    exit 1
fi

echo "Package built successfully: ${PACKAGE_DIR}.deb"
echo "You can install it using: sudo dpkg -i ${PACKAGE_DIR}.deb"

# Clean up
echo "Cleaning up build directory..."
rm -rf $PACKAGE_DIR 