# Automated Customer Journey - Complete Documentation

## Overview

The platform now includes **fully automated WhatsApp messaging** triggered at each stage of the order lifecycle, creating a hands-free customer communication flow.

## Automated Customer Journey Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ORDER LIFECYCLE                          │
└─────────────────────────────────────────────────────────────┘

1. ORDER CREATED (Pending)
   └─> Nothing sent yet (awaiting confirmation)

2. ORDER CONFIRMED
   ├─> ✅ Immediate: Order Confirmation Message
   │   "Hi [Name]! Your order [#] for [Product] is confirmed..."
   │
   └─> ⏰ Scheduled (+24h): Dispatch Call Reminder (DC1)
       "Hi [Name], we'll call you today to confirm delivery timing..."

3. ORDER DISPATCHED
   ├─> ✅ Immediate: Dispatch Notification with Tracking
   │   "Great news! Order [#] dispatched via [Courier]
   │    Tracking: [XXX]. Expected in 2-3 days..."
   │
   └─> ⏰ Scheduled (+24h): Installation Inquiry
       "Hi! For assembly, would you prefer DIY or paid help?"

4. ORDER DELIVERED
   ├─> ✅ Immediate: Delivery Confirmation & Thank You
   │   "Your order [#] is delivered! Need assembly help?
   │    Reply ASSEMBLY. Happy? Share your review!"
   │
   └─> ⏰ Scheduled (+72h): Review Request
       "Hope you're loving your [Product]! We'd appreciate
        your honest review..."

5. DNP (Did Not Pick) Flow
   ├─> Day 1: First Follow-up (if customer doesn't pick call)
   ├─> Day 2: Second Follow-up
   └─> Day 3: Final Warning (order will be cancelled)
```

## Automation Features

### 1. Automatic Triggers
Every order status change automatically triggers appropriate WhatsApp messages:

- **pending → confirmed**: Order confirmation + DC1 scheduled
- **confirmed → dispatched**: Dispatch notification + Installation inquiry scheduled
- **dispatched → delivered**: Delivery confirmation + Review request scheduled

### 2. AI-Powered Messages
All automated messages use **Claude Sonnet 4.5** to generate:
- Contextual, personalized content
- Order-specific details (number, product, tracking)
- Professional, friendly tone
- Concise, actionable messages

### 3. Manual Triggers
From Order Detail page, you can manually trigger any automation:
- Order Confirmation
- Dispatch Call Reminder
- Dispatch Notification
- Installation Inquiry
- Delivery Confirmation
- Review Request

### 4. Scheduled Automations
System automatically:
- Queues messages for future delivery
- Processes scheduled messages every 5 minutes
- Tracks execution status (pending/completed/failed)

### 5. Automation Logging
Complete audit trail of all automations:
- Automation type
- Message content
- Status (sent/failed)
- Timestamp
- Order linkage

## Backend Components

### 1. Automation Service (`/app/backend/automation_service.py`)

Core automation engine with methods:

```python
# Status change handler
await automation_service.process_order_status_change(
    order_id, old_status, new_status, db
)

# Individual triggers
await automation_service.trigger_order_confirmation(order, db)
await automation_service.trigger_dispatch_notification(order, db)
await automation_service.trigger_installation_inquiry(order, db)
await automation_service.trigger_delivery_confirmation(order, db)
await automation_service.trigger_review_request(order, db)
await automation_service.trigger_dnp_followup(order, attempt, db)

# Scheduling
await automation_service.schedule_automation(
    order_id, "review_request", hours=72, db
)

# Process scheduled
await automation_service.process_scheduled_automations(db)
```

### 2. Automation Routes (`/api/automation/`)

```bash
# Manual trigger
POST /api/automation/trigger/{order_id}
  ?automation_type=dispatch_notification

# Get logs for order
GET /api/automation/logs/{order_id}

# Get scheduled automations
GET /api/automation/schedule?status=pending

# Process scheduled (manual)
POST /api/automation/process-scheduled

# Get statistics
GET /api/automation/stats
```

### 3. Background Processor

Runs every 5 minutes to process scheduled automations:
- Checks for pending automations past scheduled time
- Executes appropriate automation
- Updates status (completed/failed)
- Logs execution

### 4. Database Collections

**automation_logs**
```json
{
  "id": "timestamp_id",
  "order_id": "order-uuid",
  "order_number": "ORD-123",
  "customer_phone": "919876543210",
  "automation_type": "dispatch_notification",
  "message": "Message content...",
  "status": "sent",
  "created_at": "2024-02-25T10:00:00Z"
}
```

**automation_schedule**
```json
{
  "id": "schedule_id",
  "order_id": "order-uuid",
  "automation_type": "review_request",
  "scheduled_time": "2024-02-28T10:00:00Z",
  "status": "pending",
  "created_at": "2024-02-25T10:00:00Z",
  "executed_at": null
}
```

## Frontend Components

### 1. Automation Panel (`/app/frontend/src/components/AutomationPanel.js`)

Displays in Order Detail page:
- **Quick Automations**: One-click buttons to trigger any automation
- **Automation History**: Timeline of all triggered automations with status

Features:
- Real-time status indicators (sent/failed)
- Message preview
- Timestamps
- Status badges

### 2. Integration with Order Workflow

When you change order status:
1. Status update API called
2. Backend detects status change
3. Triggers appropriate automation(s) in background
4. Schedules future automations
5. Logs all activities

## Usage Examples

### Example 1: Order Confirmation Flow

```bash
# Order created with status "pending"
POST /api/orders
{
  "order_number": "WA-001",
  "status": "pending",
  ...
}

# Admin confirms order
PATCH /api/orders/{id}
{
  "status": "confirmed"
}

# Automatically triggers:
# 1. Immediate WhatsApp: "Hi [Name], your order WA-001 is confirmed..."
# 2. Schedules DC1 for next day
```

### Example 2: Dispatch Notification

```bash
# Admin marks as dispatched with tracking
PATCH /api/orders/{id}
{
  "status": "dispatched",
  "tracking_number": "TR123456",
  "courier_partner": "Delhivery"
}

# Automatically triggers:
# 1. Immediate WhatsApp: "Order dispatched via Delhivery. Tracking: TR123456..."
# 2. Schedules installation inquiry for next day
```

### Example 3: Manual Trigger

From UI:
1. Go to Order Detail page
2. Scroll to "Quick Automations" panel
3. Click "Dispatch Notification" button
4. Message sent immediately
5. Shows in Automation History

## Configuration

### Enable/Disable Automation

Edit `/app/backend/automation_service.py`:
```python
class AutomationService:
    def __init__(self):
        self.enabled = True  # Set to False to disable
```

### Customize Message Templates

AI-generated messages can be customized by modifying prompts in `ai_service.py`:

```python
# For dispatch confirmations
if message_type == "dispatch_confirmation":
    prompt_parts.append("Generate a dispatch confirmation message")
    # Add your custom instructions here
```

### Adjust Scheduling Delays

In `automation_service.py`:
```python
# After confirmation -> DC1 in 24 hours
await self.schedule_automation(order_id, "dispatch_call_reminder", hours=24, db)

# After dispatch -> Installation inquiry in 24 hours  
await self.schedule_automation(order_id, "installation_inquiry", hours=24, db)

# After delivery -> Review request in 72 hours
await self.schedule_automation(order_id, "review_request", hours=72, db)
```

### Change Processing Interval

In `/app/backend/server.py`:
```python
await asyncio.sleep(300)  # 5 minutes (300 seconds)
# Change to process more/less frequently
```

## Monitoring & Analytics

### View Automation Statistics

```bash
GET /api/automation/stats

Response:
{
  "total_automations": 150,
  "successful": 142,
  "failed": 8,
  "pending_scheduled": 23,
  "success_rate": 94.67
}
```

### Check Scheduled Automations

```bash
GET /api/automation/schedule?status=pending

Response: [
  {
    "order_id": "uuid",
    "automation_type": "review_request",
    "scheduled_time": "2024-02-28T10:00:00Z",
    "status": "pending"
  }
]
```

### View Order Automation History

```bash
GET /api/automation/logs/{order_id}

Response: [
  {
    "automation_type": "order_confirmation",
    "message": "Hi Rahul! Your order...",
    "status": "sent",
    "created_at": "2024-02-25T10:00:00Z"
  }
]
```

## Troubleshooting

### Automations Not Triggering

1. Check if automation is enabled:
   ```python
   automation_service.enabled = True
   ```

2. Verify order status actually changed:
   ```bash
   # Backend logs
   tail -f /var/log/supervisor/backend.err.log
   ```

3. Check WhatsApp credentials in `.env`

### Scheduled Messages Not Sending

1. Verify background processor is running:
   ```bash
   # Should see logs every 5 minutes
   grep "Processed.*scheduled" /var/log/supervisor/backend.err.log
   ```

2. Check scheduled automations:
   ```bash
   GET /api/automation/schedule?status=pending
   ```

3. Manually trigger processing:
   ```bash
   POST /api/automation/process-scheduled
   ```

### AI Messages Failing

1. Verify EMERGENT_LLM_KEY in backend/.env
2. Check AI service logs for errors
3. Fallback messages will be used if AI fails

## Best Practices

1. **Test with Real Numbers**: Use actual WhatsApp numbers for testing
2. **Monitor First Week**: Check automation logs daily initially
3. **Customer Feedback**: Ask customers about message timing and frequency
4. **Adjust Delays**: Tune scheduling based on your delivery times
5. **Template Approval**: Get WhatsApp templates approved for better delivery
6. **DNP Management**: Monitor DNP follow-ups to reduce cancellations
7. **Review Timing**: Optimize review request timing based on product type

## Advanced Customization

### Add New Automation Type

1. Add method to `automation_service.py`:
```python
async def trigger_custom_notification(self, order, db):
    message = "Your custom message"
    await whatsapp_service.send_text_message(order['phone'], message)
    await self._log_automation(db, order, 'custom_notification', message, 'sent')
```

2. Add trigger in status change handler:
```python
elif new_status == "custom_status":
    await self.trigger_custom_notification(order, db)
```

3. Add UI button in AutomationPanel

### Integrate with External Systems

```python
# After successful automation
await self.notify_external_system(order_id, automation_type)

# Or trigger from external webhook
@router.post("/automation/webhook")
async def external_trigger(order_id: str, event: str):
    # Process external event
    await automation_service.trigger_appropriate_automation(order_id, event, db)
```

## Future Enhancements

1. **Rich Media Support**: Send product images, installation videos
2. **Interactive Buttons**: WhatsApp quick reply buttons
3. **Customer Preferences**: Let customers choose notification preferences
4. **Smart Scheduling**: ML-based optimal message timing
5. **Multi-language**: Automatic language detection and translation
6. **A/B Testing**: Test different message templates
7. **Analytics Dashboard**: Visual automation performance metrics
8. **Bulk Operations**: Mass trigger automations for multiple orders

## Summary

The automated customer journey system provides:
- ✅ Zero manual intervention for customer communication
- ✅ Consistent, professional messaging
- ✅ Perfect timing at each order stage
- ✅ AI-powered personalization
- ✅ Complete audit trail
- ✅ Flexible customization
- ✅ Background processing for reliability
- ✅ Manual override when needed

Your customers now receive timely, relevant WhatsApp messages automatically throughout their entire order journey!
