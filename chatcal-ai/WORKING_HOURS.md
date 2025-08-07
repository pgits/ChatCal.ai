# Working Hours Configuration

ChatCal.ai now supports configurable working hours to ensure meetings are only scheduled during your available business hours.

## Features

✅ **Configurable Business Hours**: Set different hours for weekdays and weekends  
✅ **Timezone-Aware**: Respects your configured timezone (EDT/EST)  
✅ **Automatic Validation**: Rejects bookings outside working hours with friendly messages  
✅ **Smart Suggestions**: Provides specific available time slots when no time is specified  
✅ **Environment-Based**: Easy configuration through `.env` file  

## Configuration

### Environment Variables

Add these settings to your `.env` file:

```bash
# Working Hours Configuration (EDT/EST timezone)
# Weekday working hours (Monday-Friday)  
WEEKDAY_START_TIME=07:30
WEEKDAY_END_TIME=18:30

# Weekend working hours (Saturday-Sunday)
WEEKEND_START_TIME=10:30  
WEEKEND_END_TIME=16:30

# Working hours timezone (should match DEFAULT_TIMEZONE)
WORKING_HOURS_TIMEZONE=America/New_York
```

### Default Configuration

If not specified, the system uses these defaults:
- **Weekdays**: 7:30 AM - 6:30 PM EDT
- **Weekends**: 10:30 AM - 4:30 PM EDT  
- **Timezone**: America/New_York (EDT/EST)

## How It Works

### 1. Booking Validation

When a user tries to book a meeting, the system:
1. Parses the requested date and time
2. Checks if it's within configured working hours
3. If outside working hours, returns a friendly message with your business hours
4. If within working hours, proceeds with availability checking and booking

### 2. User Experience

**Outside Working Hours Request:**
```
User: "Book a meeting with Pete tomorrow at 6:00 AM"
Bot: "My apologies for the inconvenience, but Pete's business hours are Monday through Friday from 7:30 AM - 6:30 PM EDT."
```

**Weekend Hours Request:**
```  
User: "Schedule a call Saturday at 9:00 AM"
Bot: "My apologies for the inconvenience, but Pete's business hours are Saturday and Sunday from 10:30 AM - 4:30 PM EDT."
```

### 3. Availability Checking

When checking availability, the system:
- Only shows time slots within working hours
- Provides context about working hours if no slots available
- Suggests specific times when user requests a date without time

**Example:**
```
User: "What's available this Saturday?"
Bot: "For Saturday, January 13, Pete is available between 10:30 AM and 4:30 PM EDT. Please suggest a specific time within this window."
```

## Implementation Details

### Core Components

1. **`WorkingHoursValidator`** (`app/core/working_hours.py`)
   - Main validation logic
   - Time parsing and timezone handling
   - User-friendly message generation

2. **Configuration Integration** (`app/config.py`)
   - Environment variable loading
   - Default values
   - Type validation

3. **Calendar Tools Integration** (`app/core/tools.py`)
   - Booking validation before calendar API calls
   - Availability filtering
   - Error message handling

### Time Format

Working hours use 24-hour format in configuration:
- `07:30` = 7:30 AM
- `18:30` = 6:30 PM  
- `10:30` = 10:30 AM
- `16:30` = 4:30 PM

### Timezone Handling

- All times are interpreted in the configured `WORKING_HOURS_TIMEZONE`
- Automatic conversion from user's timezone to working hours timezone
- Consistent display in EDT/EST format

## Testing

Run the working hours test suite:

```bash
cd chatcal-ai
python3 test_working_hours.py
```

Tests include:
- ✅ Weekday hour validation
- ✅ Weekend hour validation  
- ✅ Edge cases (exact start/end times)
- ✅ Integration with calendar tools
- ✅ Suggested times functionality

## Customization Examples

### Standard Business Hours
```bash
WEEKDAY_START_TIME=09:00
WEEKDAY_END_TIME=17:00
WEEKEND_START_TIME=10:00
WEEKEND_END_TIME=14:00
```

### Extended Hours
```bash
WEEKDAY_START_TIME=06:00
WEEKDAY_END_TIME=20:00  
WEEKEND_START_TIME=08:00
WEEKEND_END_TIME=18:00
```

### Weekdays Only
```bash
WEEKDAY_START_TIME=08:00
WEEKDAY_END_TIME=18:00
WEEKEND_START_TIME=08:00
WEEKEND_END_TIME=08:00  # Same start/end = no availability
```

## Benefits

🕐 **Automated Boundary Enforcement**: No more manual checking of inappropriate meeting times  
🎯 **Professional Communication**: Consistent, polite responses about availability  
⚙️ **Easy Configuration**: Change working hours without code modifications  
🌍 **Timezone Accurate**: Respects timezone differences and daylight saving time  
📅 **Calendar Integration**: Works seamlessly with existing booking flow  

## Future Enhancements

Potential additions:
- Holiday/vacation day exclusions
- Different hours per day of week
- Lunch break exclusions  
- Multiple timezone support
- Break time configurations

---

The working hours system ensures professional scheduling boundaries while maintaining the friendly, conversational experience users expect from ChatCal.ai.