# Dragon Guild

A Flask and SQLite application for managing a weekly fantasy guild program.

Website: https://mokeshmiri.pythonanywhere.com/

## Run locally

```bash
pip install -r requirements.txt
flask --app app run
```

Open http://127.0.0.1:5000. The database is `db/guild.db`.

## Test accounts

| Role | Email | Password |
| --- | --- | --- |
| Guild Master | `master@gmail.com` | `master123` |
| Adventurer | `aria@gmail.com` | `pass123` |
| Adventurer | `marco@gmail.com` | `pass123` |
| Adventurer | `mo@gmail.com` | `pass123` |
| Adventurer | `nicola@gmail.com` | `pass123` |

## Testing

The target device is desktop. The simulated current time is Monday at 10:00.

- Monday 12:00 has a fully booked Warrior role and locked participations.
- Friday 10:00 has no participants, so the Guild Master can edit or cancel it.
- The sample data includes all three roles and two sessions for every day.
