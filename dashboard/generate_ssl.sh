#!/bin/bash

# SSL Certificate Generator for Parker PO Dashboard
# This script creates self-signed SSL certificates for HTTPS

echo "🔐 Parker PO Dashboard - SSL Certificate Generator"
echo "=================================================="

# Create SSL directory
mkdir -p /volume1/Main/Main/ParkerPOsOCR/dashboard/ssl

# Navigate to SSL directory
cd /volume1/Main/Main/ParkerPOsOCR/dashboard/ssl

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out dashboard.key 2048

# Generate certificate signing request
echo "📋 Creating certificate signing request..."
openssl req -new -key dashboard.key -out dashboard.csr -subj "/C=US/ST=State/L=City/O=Parker/OU=IT/CN=parker-po-dashboard"

# Generate self-signed certificate (valid for 1 year)
echo "🎫 Generating self-signed certificate..."
openssl x509 -req -days 365 -in dashboard.csr -signkey dashboard.key -out dashboard.crt

# Set proper permissions
chmod 600 dashboard.key
chmod 644 dashboard.crt

# Clean up CSR file
rm dashboard.csr

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "📁 Files created:"
echo "   - dashboard.key (private key)"
echo "   - dashboard.crt (certificate)"
echo ""
echo "🔧 To enable HTTPS, update your .env file:"
echo "   USE_HTTPS=true"
echo "   SSL_CERT_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.crt"
echo "   SSL_KEY_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.key"
echo ""
echo "⚠️  Note: This is a self-signed certificate. Browsers will show a security warning."
echo "   For production use, consider getting a certificate from Let's Encrypt or a CA."
echo ""

# Update .env file automatically
ENV_FILE="/volume1/Main/Main/ParkerPOsOCR/dashboard/.env"
if [ -f "$ENV_FILE" ]; then
    echo "🔄 Updating .env file with SSL configuration..."
    
    # Update or add SSL settings
    sed -i 's/USE_HTTPS=false/USE_HTTPS=true/' "$ENV_FILE"
    
    # Add SSL paths if they don't exist
    if ! grep -q "SSL_CERT_PATH=" "$ENV_FILE"; then
        echo "SSL_CERT_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.crt" >> "$ENV_FILE"
    else
        sed -i 's|SSL_CERT_PATH=.*|SSL_CERT_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.crt|' "$ENV_FILE"
    fi
    
    if ! grep -q "SSL_KEY_PATH=" "$ENV_FILE"; then
        echo "SSL_KEY_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.key" >> "$ENV_FILE"
    else
        sed -i 's|SSL_KEY_PATH=.*|SSL_KEY_PATH=/volume1/Main/Main/ParkerPOsOCR/dashboard/ssl/dashboard.key|' "$ENV_FILE"
    fi
    
    echo "✅ .env file updated!"
fi

echo ""
echo "🚀 Ready to start secure dashboard!"
echo "   - HTTP:  http://your-nas-ip:5000"
echo "   - HTTPS: https://your-nas-ip:5000"
