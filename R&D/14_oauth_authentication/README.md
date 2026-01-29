# OAuth Authentication (Google/GitHub)

## What Is This?

Social login authentication using Google and GitHub OAuth 2.0 providers. Users can sign in with their existing accounts instead of creating new credentials.

## Status: **DONE** (2026-01-29)

## Why Implement This?

### Problems Solved

1. **No User Identity**: Conversations weren't tied to authenticated users
2. **No Profile Data**: No way to personalize experience with user info
3. **Security**: Open access without authentication

### Benefits

- One-click login with existing accounts
- User profile data (name, avatar) available
- Conversation history tied to authenticated users
- Audit trail for enterprise deployments

## Implementation

### OAuth Callback Handler

Location: `mindrian_chat.py:67-131`

```python
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_user: cl.User
) -> Optional[cl.User]:
    """Handle OAuth callback from Google or GitHub."""

    if provider_id == "google":
        return cl.User(
            identifier=raw_user_data.get("email"),
            metadata={
                "name": raw_user_data.get("name"),
                "image": raw_user_data.get("picture"),
                "provider": "google",
            }
        )

    elif provider_id == "github":
        return cl.User(
            identifier=raw_user_data.get("email") or raw_user_data.get("login"),
            metadata={
                "name": raw_user_data.get("name"),
                "image": raw_user_data.get("avatar_url"),
                "provider": "github",
            }
        )

    return default_user
```

## Setup Instructions

### 1. Generate Auth Secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add to `.env`:
```bash
CHAINLIT_AUTH_SECRET=your_generated_secret
```

### 2. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable "Google+ API" (or "People API")
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URI:
   - Development: `http://localhost:8000/auth/oauth/google/callback`
   - Production: `https://mindrian.onrender.com/auth/oauth/google/callback`
6. Copy Client ID and Client Secret

Add to `.env`:
```bash
OAUTH_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your_client_secret
```

### 3. Configure GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name: Mindrian
   - Homepage URL: `https://mindrian.onrender.com`
   - Authorization callback URL: `https://mindrian.onrender.com/auth/oauth/github/callback`
4. Copy Client ID and generate Client Secret

Add to `.env`:
```bash
OAUTH_GITHUB_CLIENT_ID=your_client_id
OAUTH_GITHUB_CLIENT_SECRET=your_client_secret
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CHAINLIT_AUTH_SECRET` | Yes | Secret for signing auth tokens |
| `OAUTH_GOOGLE_CLIENT_ID` | For Google | Google OAuth client ID |
| `OAUTH_GOOGLE_CLIENT_SECRET` | For Google | Google OAuth client secret |
| `OAUTH_GITHUB_CLIENT_ID` | For GitHub | GitHub OAuth client ID |
| `OAUTH_GITHUB_CLIENT_SECRET` | For GitHub | GitHub OAuth client secret |

## User Data Available

### Google Provider

```python
raw_user_data = {
    "sub": "123456789",          # Google user ID
    "name": "John Doe",          # Full name
    "given_name": "John",        # First name
    "family_name": "Doe",        # Last name
    "picture": "https://...",    # Profile picture URL
    "email": "john@gmail.com",   # Email address
    "email_verified": True       # Email verification status
}
```

### GitHub Provider

```python
raw_user_data = {
    "login": "johndoe",          # GitHub username
    "name": "John Doe",          # Display name
    "email": "john@example.com", # Primary email (may need API call)
    "avatar_url": "https://...", # Profile avatar URL
    "html_url": "https://...",   # Profile URL
    "company": "ACME Inc",       # Company (optional)
    "location": "San Francisco"  # Location (optional)
}
```

## Accessing User Data in Code

```python
# In any handler
user = cl.user_session.get("user")
if user:
    user_name = user.metadata.get("name", "User")
    user_image = user.metadata.get("image")
    provider = user.metadata.get("provider")

    await cl.Message(
        content=f"Welcome, {user_name}!"
    ).send()
```

## Flow Diagram

```
1. User clicks "Login with Google/GitHub"
           ↓
2. Redirect to provider's auth page
           ↓
3. User grants permission
           ↓
4. Provider redirects to callback URL
           ↓
5. oauth_callback() processes user data
           ↓
6. cl.User created with identifier + metadata
           ↓
7. Session established, user sees chat
```

## Testing

### Local Development

1. Set callback URLs to `http://localhost:8000/auth/oauth/{provider}/callback`
2. Run Chainlit: `chainlit run mindrian_chat.py`
3. Visit `http://localhost:8000`
4. Click login button
5. Complete OAuth flow

### Production

1. Update callback URLs to production domain
2. Deploy with environment variables set
3. Test login flow end-to-end

## Security Considerations

1. **Never commit secrets**: Keep `.env` in `.gitignore`
2. **Use HTTPS**: OAuth requires HTTPS in production
3. **Rotate secrets**: Change `CHAINLIT_AUTH_SECRET` periodically
4. **Scope limitations**: Only request necessary OAuth scopes

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "OAuth client not found" | Check client ID is correct |
| "Redirect URI mismatch" | Ensure callback URL matches exactly |
| "Invalid client secret" | Regenerate secret in provider console |
| Login button not showing | Check environment variables are set |

## Files Modified

| File | Changes |
|------|---------|
| `mindrian_chat.py` | Added `@cl.oauth_callback` handler |
| `.env.example` | Documented OAuth variables |

## Future Enhancements

- [ ] Add more providers (Microsoft, Discord, etc.)
- [ ] Role-based access control
- [ ] Admin dashboard for user management
- [ ] Session timeout configuration

---

*Implemented: 2026-01-29*
*Commit: f8f3909*
