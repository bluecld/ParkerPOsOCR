# Notification System for PO Processing
import smtplib
import requests
import json
import os
from datetime import datetime
import logging

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, config_file=None):
        # Use the correct config file path for NAS/host
        if config_file is None:
            config_file = "/volume1/Main/Main/ParkerPOsOCR/dashboard/logs/notification_config.json"
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load notification configuration"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "to_addresses": []
            },
            "webhook": {
                "enabled": False,
                "urls": []
            },
            "pushover": {
                "enabled": False,
                "user_key": "",
                "api_token": ""
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save notification configuration"""
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def send_email_notification(self, subject, message):
        """Send email notification"""
        if not self.config["email"]["enabled"] or not EMAIL_AVAILABLE:
            return False
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config["email"]["username"]
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            
            for to_addr in self.config["email"]["to_addresses"]:
                msg['To'] = to_addr
                server.send_message(msg)
                logger.info(f"Email sent to {to_addr}")
            
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False
    
    def send_webhook_notification(self, title, message, po_number=None):
        """Send webhook notification"""
        if not self.config["webhook"]["enabled"]:
            return False
        
        payload = {
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "po_number": po_number
        }
        
        success = True
        for url in self.config["webhook"]["urls"]:
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Webhook sent to {url}")
                else:
                    logger.error(f"Webhook failed for {url}: {response.status_code}")
                    success = False
            except Exception as e:
                logger.error(f"Webhook error for {url}: {e}")
                success = False
        
        return success
    
    def send_pushover_notification(self, title, message):
        """Send Pushover notification"""
        if not self.config["pushover"]["enabled"]:
            return False
        
        try:
            response = requests.post("https://api.pushover.net/1/messages.json", data={
                "token": self.config["pushover"]["api_token"],
                "user": self.config["pushover"]["user_key"],
                "title": title,
                "message": message,
                "priority": 1,
                "sound": "pushover"
            }, timeout=10)
            
            if response.status_code == 200:
                logger.info("Pushover notification sent")
                return True
            else:
                logger.error(f"Pushover failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Pushover error: {e}")
            return False
    
    def send_telegram_notification(self, title, message):
        """Send Telegram notification"""
        if not self.config["telegram"]["enabled"]:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.config["telegram"]["chat_id"],
                "text": f"*{title}*\n\n{message}",
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent")
                return True
            else:
                logger.error(f"Telegram failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def send_notification(self, title, message, po_number=None, notification_type="info"):
        """Send notification through all enabled channels"""
        results = {}
        
        # Email
        if self.config["email"]["enabled"] and EMAIL_AVAILABLE:
            results["email"] = self.send_email_notification(title, message)
        
        # Webhook
        if self.config["webhook"]["enabled"]:
            results["webhook"] = self.send_webhook_notification(title, message, po_number)
        
        # Pushover
        if self.config["pushover"]["enabled"]:
            results["pushover"] = self.send_pushover_notification(title, message)
        
        # Telegram
        if self.config["telegram"]["enabled"]:
            results["telegram"] = self.send_telegram_notification(title, message)
        
        return results
    
    def notify_po_processed(self, po_number, filename):
        """Send notification when PO is successfully processed"""
        title = f"✅ PO {po_number} Processed"
        message = f"Purchase Order {po_number} has been successfully processed.\n\nOriginal file: {filename}\nProcessed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(title, message, po_number, "success")
    
    def notify_po_error(self, filename, error_message):
        """Send notification when PO processing fails"""
        title = f"❌ PO Processing Failed"
        message = f"Failed to process PDF file: {filename}\n\nError: {error_message}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(title, message, None, "error")
    
    def notify_system_status(self, status, message):
        """Send system status notification"""
        title = f"🔧 System Status: {status}"
        full_message = f"{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(title, full_message, None, "warning")

# Global notification manager instance
notification_manager = NotificationManager()
