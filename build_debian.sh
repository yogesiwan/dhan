#!/bin/bash

# Create debian package structure
PACKAGE_NAME="financial-dashboard"
VERSION="1.0.0"
ARCH="amd64"
PACKAGE_DIR="$PACKAGE_NAME-$VERSION"

# Create directory structure
mkdir -p $PACKAGE_DIR/DEBIAN
mkdir -p $PACKAGE_DIR/usr/local/bin/financial-dashboard
mkdir -p $PACKAGE_DIR/usr/share/applications

# Copy control file
cp debian.control $PACKAGE_DIR/DEBIAN/control

# Copy application files
cp -r dist/FinancialDashboard/* $PACKAGE_DIR/usr/local/bin/financial-dashboard/

# Copy .desktop file
cp dist/FinancialDashboard/FinancialDashboard.desktop $PACKAGE_DIR/usr/share/applications/

# Set permissions
chmod 755 $PACKAGE_DIR/DEBIAN/control
chmod -R 755 $PACKAGE_DIR/usr/local/bin/financial-dashboard

# Build the package
dpkg-deb --build $PACKAGE_DIR

# Clean up
rm -rf $PACKAGE_DIR 