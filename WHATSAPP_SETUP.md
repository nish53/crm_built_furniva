# WhatsApp Business API Setup Guide

## Prerequisites

1. **WhatsApp Business Account** - Create at business.facebook.com
2. **Meta Business Manager** - Set up at business.facebook.com
3. **Phone Number** - A dedicated phone number for WhatsApp Business

## Setup Steps

### 1. Create WhatsApp Business Account
- Go to Meta Business Suite (business.facebook.com)
- Navigate to Business Settings → Accounts → WhatsApp Business Accounts
- Click "Add" and follow the setup wizard
- Verify your business phone number

### 2. Get API Credentials
After setting up your WhatsApp Business Account, you'll need:

- **WhatsApp API Token**: Found in App Dashboard → WhatsApp → API Setup
- **Phone Number ID**: Your WhatsApp Business phone number ID
- **Business Account ID**: Your WhatsApp Business Account ID
- **Webhook Verify Token**: Create a custom secure token (e.g., `mySecureToken123`)

### 3. Update Environment Variables

Edit `/app/backend/.env` file with your credentials:

```bash
WHATSAPP_API_TOKEN=your_actual_api_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_verify_token_here
```

### 4. Configure Webhook

1. Go to your Meta App Dashboard → WhatsApp → Configuration
2. Click "Edit" next to Webhook
3. Set Callback URL: `https://your-domain.com/api/whatsapp/webhook`
4. Set Verify Token: (same as WHATSAPP_WEBHOOK_VERIFY_TOKEN in .env)
5. Subscribe to webhook fields:
   - `messages`
   - `message_status`

### 5. Create Message Templates

WhatsApp Business API requires pre-approved templates for initiating conversations:

1. Go to WhatsApp Manager → Message Templates
2. Create templates for:
   - Order Confirmation
   - Dispatch Notification
   - Delivery Confirmation
   - Installation Inquiry
   - Follow-up Request

Example Template (Dispatch Notification):
```
Name: dispatch_notification
Category: SHIPPING_UPDATE
Language: English
Body: Hi {{1}}, your order {{2}} has been dispatched via {{3}}. Tracking: {{4}}. Expected delivery in 2-3 days.
```

### 6. Test the Integration

1. Send a test message to your WhatsApp Business number
2. Check the WhatsApp CRM page - you should see the conversation appear
3. Reply from the CRM interface
4. Verify the message is delivered to customer's WhatsApp

## Features Available

### AI-Powered Messaging
- **Claude Sonnet 4.5** integration for smart message suggestions
- Context-aware responses based on order details
- Pre-configured message types:
  - Delivery confirmations
  - Installation inquiries
  - Follow-up messages
  - General customer service

### Message Types Supported
- ✅ Text messages
- ✅ Images
- ✅ Videos
- ✅ Documents
- ✅ Template messages

### Real-time Features
- Message delivery status (sent, delivered, read)
- Automatic message history
- Conversation management
- Customer information integration

## API Endpoints

### Send Messages
```bash
POST /api/whatsapp/messages/send
Parameters:
- to: Phone number (with country code, e.g., 919876543210)
- message: Text content
- order_id: (optional) Link to order
```

### Send Media
```bash
POST /api/whatsapp/messages/send-media
Parameters:
- to: Phone number
- media_type: image|video|document
- media_url: Public URL of media file
- caption: (optional) Media caption
```

### AI Suggestion
```bash
POST /api/whatsapp/ai/suggest-message
Parameters:
- context: Additional context
- message_type: delivery_confirmation|installation_inquiry|follow_up|general
- order_id: (optional) Order ID for context
- phone: (optional) Customer phone for conversation history
```

## Troubleshooting

### Webhook Not Receiving Messages
1. Verify webhook URL is publicly accessible (HTTPS required)
2. Check webhook verification was successful
3. Ensure correct subscription fields are enabled
4. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`

### Messages Not Sending
1. Verify API token is valid and not expired
2. Check phone number ID is correct
3. For template messages, ensure template is approved
4. Check customer phone number format (must include country code, no + or spaces)

### AI Suggestions Not Working
1. Verify EMERGENT_LLM_KEY is set in backend/.env
2. Check backend logs for any AI service errors
3. Ensure emergentintegrations library is installed

## Cost Considerations

- WhatsApp Business API charges per conversation
- Template-initiated conversations: ~$0.005-0.01 per message
- User-initiated (customer replies): Free for 24 hours
- AI suggestions use Emergent LLM credits (check your balance)

## Best Practices

1. **Use Templates Wisely**: Templates are for initiating conversations
2. **Respond Quickly**: Maximize 24-hour free messaging window
3. **Leverage AI**: Use AI suggestions for consistent, professional messaging
4. **Track Conversations**: Link conversations to orders for better context
5. **Monitor Status**: Check message delivery status to ensure customer received it

## Next Steps

Once configured, you can:
- Send automated dispatch notifications from Order Detail page
- Use AI to generate contextual customer messages
- Track all customer conversations in one place
- Integrate WhatsApp notifications into your order workflow
