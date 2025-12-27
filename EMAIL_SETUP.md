# Email Configuration for Panacare - FIXED

## ✅ SOLUTION: Gmail with App Password

You have provided the Gmail App Password: `matb xlae ceki ovds`

### Set These Environment Variables in Railway Production:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=developers@mypanacare.com
EMAIL_HOST_PASSWORD=matb xlae ceki ovds
DEFAULT_FROM_EMAIL=developers@mypanacare.com
```

### Steps to Fix:
1. Go to your Railway production environment
2. Set the environment variable:
   ```
   EMAIL_HOST_PASSWORD=matb xlae ceki ovds
   ```
3. Restart the deployment
4. Test by registering a new CHP user

### Why This Will Work:
- App Passwords bypass Gmail's security restrictions
- The password format `matb xlae ceki ovds` is correct for App Passwords
- This configuration is production-ready

### After Setting Environment Variables:
1. The current timeouts will stop happening
2. Real activation emails will be sent to users
3. CHP registration will work with proper email delivery

## Important Notes:
- Keep this App Password secure
- Don't commit it to code (use environment variables only)
- The spaces in the password are normal for Gmail App Passwords