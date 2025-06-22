# 🐘 Mastodon Integration Guide

This guide explains how to set up and use the Mastodon integration feature in your Telegram Promo Bot.

## 🌟 Features

- **Direct Posting**: Post promotional content directly to your Mastodon account
- **Automatic Hashtags**: Automatically generates relevant hashtags for your products
- **Character Limit Handling**: Automatically truncates text to fit Mastodon's 500-character limit
- **Rate Limiting**: Built-in protection with 5 posts per 5 minutes limit
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Post History**: Track your Mastodon posting history
- **Security**: Input validation and secure API communication

## 🚀 Quick Setup

### 1. Get Your Mastodon Access Token

1. **Log in to your Mastodon account** (any instance like mastodon.social, mastodon.online, etc.)
2. **Go to Settings** → **Development** → **New Application**
3. **Create a new application**:
   - **Application name**: "Telegram Promo Bot" (or any name you prefer)
   - **Scopes**: Select `write:statuses` (this allows posting)
4. **Save the application**
5. **Copy the Access Token** from the application details

### 2. Configure Your Bot

1. **Edit your `.env` file**:
   ```env
   # Mastodon Configuration
   MASTODON_INSTANCE=https://mastodon.social
   MASTODON_ACCESS_TOKEN=your_access_token_here
   ```

2. **Replace the values**:
   - `MASTODON_INSTANCE`: Your Mastodon instance URL (include https://)
   - `MASTODON_ACCESS_TOKEN`: The token you copied from step 1

### 3. Test the Integration

Run the test script to verify everything is working:

```bash
python test_mastodon.py
```

You should see:
- ✅ Config module loaded successfully
- ✅ Mastodon configured: https://your-instance.com
- ✅ Access token is set
- ✅ Mastodon connection successful!

## 📱 How to Use

### Basic Usage

1. **Start the bot** and generate promotional text
2. **After generating text**, you'll see the "🐘 Post to Mastodon" button
3. **Click the button** to see a preview of your post
4. **Confirm** to post directly to your Mastodon account

### Post Preview

The bot will show you:
- **Instance**: Which Mastodon instance you're posting to
- **Product**: The product name
- **Preview**: How your post will look (with hashtags)

### Automatic Features

- **Hashtag Generation**: Automatically adds relevant hashtags based on your product
- **Character Limit**: Truncates long text to fit Mastodon's 500-character limit
- **Error Handling**: Shows clear error messages if posting fails

## 🔧 Advanced Configuration

### Multiple Instances

To use different Mastodon instances, simply change the `MASTODON_INSTANCE` in your `.env` file:

```env
# For different instances
MASTODON_INSTANCE=https://fosstodon.org
MASTODON_INSTANCE=https://mastodon.online
MASTODON_INSTANCE=https://mstdn.social
```

### Rate Limiting

The bot automatically limits Mastodon posts to:
- **5 posts per 5 minutes** to respect Mastodon's API limits
- **Automatic retry** with exponential backoff for temporary failures

### Security Features

- **Input Validation**: All text is sanitized before posting
- **URL Validation**: Mastodon instance URLs are validated
- **Token Security**: Access tokens are handled securely
- **Error Logging**: All errors are logged for debugging

## 🛠️ Troubleshooting

### Common Issues

#### "❌ Mastodon not configured"
- **Solution**: Add `MASTODON_INSTANCE` and `MASTODON_ACCESS_TOKEN` to your `.env` file

#### "❌ Invalid access token"
- **Solution**: Check your access token in Mastodon settings and update `.env`

#### "❌ Cannot connect to Mastodon instance"
- **Solution**: Verify the instance URL includes `https://` and is correct

#### "❌ HTTP Error 422"
- **Solution**: Your post might be too long or contain invalid characters

### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Testing Connection

Use the test script to diagnose issues:

```bash
python test_mastodon.py
```

## 📊 Post History

The bot tracks your Mastodon posting history including:
- **Product name**
- **Timestamp**
- **Success/failure status**
- **Error messages** (if any)
- **Text length**

Access this through the bot's interface or check the user data files.

## 🔒 Security Best Practices

1. **Keep your access token private** - never share it
2. **Use environment variables** - don't hardcode tokens in your code
3. **Regular token rotation** - periodically regenerate your access token
4. **Monitor usage** - check your Mastodon account for unexpected posts
5. **Backup your data** - the bot automatically backs up post history

## 🌐 Supported Instances

This integration works with **any Mastodon instance**, including:
- mastodon.social
- mastodon.online
- fosstodon.org
- mstdn.social
- mas.to
- And many others!

## 🤝 Contributing

Found a bug or want to improve the Mastodon integration? 
- **Report issues** in the GitHub repository
- **Submit pull requests** for improvements
- **Suggest features** for future updates

## 📝 API Reference

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MASTODON_INSTANCE` | Yes | Your Mastodon instance URL | `https://mastodon.social` |
| `MASTODON_ACCESS_TOKEN` | Yes | Your application access token | `abc123...` |

### Rate Limits

| Action | Limit | Window |
|--------|-------|--------|
| Post Status | 5 requests | 5 minutes |
| Connection Test | 1 request | 10 seconds |

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 401 | Invalid token | Check your access token |
| 422 | Invalid post content | Check text length and content |
| 429 | Rate limit exceeded | Wait before posting again |
| 500 | Server error | Try again later |

---

**Need help?** Check the main README.md or create an issue in the GitHub repository! 