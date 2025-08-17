# 🔐 Parker PO Dashboard Security Configuration Guide

## 🛡️ Multi-Layer Security Implementation

Your dashboard now includes comprehensive security features to protect against hackers and bots when exposed to the internet.

### 🔒 Security Features Implemented

1. **Authentication System**
   - Username/password login required
   - Secure session management with auto-timeout
   - Bcrypt password hashing
   - Failed login attempt logging

2. **Rate Limiting**
   - 30 requests per minute per IP
   - 200 requests per hour per IP
   - 5 login attempts per minute
   - 2 container restarts per hour

3. **IP Whitelisting**
   - Optional IP address restrictions
   - Support for single IPs and CIDR ranges
   - Automatic blocking of unauthorized IPs

4. **HTTPS/SSL Support**
   - Self-signed certificates included
   - Encrypted data transmission
   - SSL certificate auto-generation

5. **Security Headers**
   - XSS protection
   - Clickjacking prevention
   - Content type sniffing protection
   - Strict transport security

6. **Comprehensive Logging**
   - All login attempts logged
   - IP blocking events recorded
   - Container restart tracking
   - Security event monitoring

### 🔧 Configuration Steps

#### 1. **Configure Authentication**
Edit `/volume1/Main/Main/ParkerPOsOCR/dashboard/.env`:

```bash
# Change default credentials immediately!
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=YourSecurePassword123!

# Generate a random secret key
SECRET_KEY=your-super-secret-random-key-here
```

#### 2. **Set Up IP Whitelisting (Recommended)**
Add your trusted IP addresses:

```bash
# Allow specific IPs (comma-separated)
ALLOWED_IPS=203.0.113.5,198.51.100.10

# Allow IP ranges using CIDR notation
ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8

# Leave empty to allow all IPs (less secure)
ALLOWED_IPS=
```

#### 3. **Enable HTTPS (Highly Recommended)**
Generate SSL certificates:

```bash
cd /volume1/Main/Main/ParkerPOsOCR/dashboard
./generate_ssl.sh
```

This will:
- Generate SSL certificates
- Update .env configuration automatically
- Enable HTTPS on port 5000

#### 4. **Start Secure Dashboard**
```bash
cd /volume1/Main/Main/ParkerPOsOCR/dashboard

# Stop the old dashboard first
./dashboard_service.sh stop

# Start the secure version
./dashboard_secure_service.sh start
```

### 🌐 Router Port Forwarding Setup

#### Option 1: HTTPS (Recommended)
- **Internal**: NAS_IP:5000
- **External**: YOUR_PUBLIC_IP:5000
- **Protocol**: TCP
- **Security**: SSL encrypted

#### Option 2: Custom Port (More Secure)
- **Internal**: NAS_IP:5000  
- **External**: YOUR_PUBLIC_IP:8443 (or any high port)
- **Protocol**: TCP
- **Benefit**: Hides service on non-standard port

### 🔍 Security Monitoring

#### Check Security Logs
```bash
./dashboard_secure_service.sh security
```

#### Monitor Failed Logins
```bash
tail -f /volume1/Main/Main/ParkerPOsOCR/dashboard/logs/security.log
```

#### Check Service Status
```bash
./dashboard_secure_service.sh status
```

### 🚨 Additional Security Recommendations

#### 1. **Change Default Credentials**
```bash
# Update .env file with strong credentials
ADMIN_USERNAME=parker_secure_admin
ADMIN_PASSWORD=ParkerPO2025!VerySecurePassword#123
```

#### 2. **Use Strong Secret Key**
Generate a random secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. **Regular Security Monitoring**
- Check security logs daily
- Monitor for failed login attempts
- Watch for unusual IP access patterns
- Review rate limiting triggers

#### 4. **Network-Level Protection**
- Use router firewall rules
- Consider VPN access instead of direct exposure
- Enable DDoS protection if available
- Use fail2ban for additional IP blocking

#### 5. **Keep Updated**
- Regularly update Python packages
- Monitor security advisories
- Update SSL certificates before expiry

### 🛠️ Service Management Commands

```bash
# Start secure dashboard
./dashboard_secure_service.sh start

# Stop secure dashboard  
./dashboard_secure_service.sh stop

# Restart secure dashboard
./dashboard_secure_service.sh restart

# Check status
./dashboard_secure_service.sh status

# View logs
./dashboard_secure_service.sh logs

# View security events
./dashboard_secure_service.sh security
```

### 🔗 Access URLs

#### Local Network
- **HTTP**: http://192.168.0.62:5000
- **HTTPS**: https://192.168.0.62:5000

#### Internet Access (after port forwarding)
- **HTTPS**: https://YOUR_PUBLIC_IP:5000
- **Custom Port**: https://YOUR_PUBLIC_IP:8443

### ⚠️ Important Security Notes

1. **Always use HTTPS** when accessing over the internet
2. **Change default credentials** immediately
3. **Use IP whitelisting** when possible
4. **Monitor security logs** regularly
5. **Consider VPN access** for maximum security
6. **Self-signed certificates** will show browser warnings (normal)
7. **Test thoroughly** before exposing to internet

### 🎯 Login Credentials (Default - CHANGE THESE!)

- **Username**: parker_admin
- **Password**: ParkerPO2025!SecurePass

**🚨 CRITICAL: Change these credentials in the .env file before exposing to the internet!**
