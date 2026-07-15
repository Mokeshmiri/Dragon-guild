# Dragon Guild

Small Flask and SQLite exam project for managing a fantasy adventure guild.

## Run locally

```bash
pip3.12 install -r requirements.txt
flask --app app run
```

Then open `http://127.0.0.1:5000`.

The ready SQLite database is `db/guild.db`. It was created with DB Browser for SQLite, as in Lab 8.

## Test accounts

| Role | Email | Password |
| --- | --- | --- |
| Guild Master | `guildmaster@dragonguild.com` | `guildpass` |
| Adventurer | `aria@dragonguild.com` | `adventurer1` |
| Adventurer | `borin@dragonguild.com` | `adventurer1` |
| Adventurer | `cira@dragonguild.com` | `adventurer1` |
| Adventurer | `darin@dragonguild.com` | `adventurer1` |
| Adventurer | `moka@dragonguild.com` | `zf@2uy8SUj` |

## Testing

Target device: desktop.

Simulated current time: Monday 10:00.

Participations for sessions starting within 8 simulated hours are locked. Later participations can still be modified or cancelled.

- Monday 12:00 has a fully booked Warrior role and locked participations.
- Monday 20:00 has no participants, so the Guild Master can edit or cancel it.
- Existing sample data includes all three roles and at least two sessions per day.

## PythonAnywhere

Upload the project to PythonAnywhere and set the WSGI file to import `app` from `app.py`.

Deployment URL: add the final PythonAnywhere URL here after uploading.
