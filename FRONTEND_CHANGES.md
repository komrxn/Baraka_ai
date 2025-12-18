# Frontend Changes for Phone Authentication

## Overview
Backend auth system migrated from username/password to Telegram phone auth.

## API Changes

### Registration Endpoint: `POST /auth/register`

**Old:**
```typescript
{
  username: string,
  email: string,
  password: string
}
```

**New:**
```typescript
{
  telegram_id: number,
  phone_number: string,
  name: string
}
```

### Login Endpoint: `POST /auth/login`

**Old:**
```typescript
{
  username: string,
  password: string
}
```

**New:**
```typescript
{
  phone_number: string,
  telegram_id?: number  // optional
}
```

### User Response Schema

**Old:**
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  default_currency: string;
  created_at: string;
}
```

**New:**
```typescript
interface User {
  id: string;
  telegram_id: number;
  phone_number: string;
  name: string;
  default_currency: string;
  created_at: string;
}
```

## Implementation Notes

1. Registration form needs phone input instead of username/email/password
2. Login form needs phone input instead of username/password
3. Consider using Telegram WebApp SDK for seamless telegram_id retrieval
4. Update user profile displays to show name and phone instead of username/email

## Migration
All old users will need to re-register with phone number.
