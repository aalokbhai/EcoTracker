# EcoTrack - Smart Waste Management

Citizens report waste / request pickups -> the **MC (Municipal Corporation) office** reviews them ->
an approved **garbage collector** cleans the place (with Google Maps directions) and uploads a photo ->
the MC office **verifies** the cleaning.

## Roles

| Role | How the account is created | What they can do |
|------|---------------------------|------------------|
| Citizen | Register page ("I am a: Citizen") | Report complaints, request pickups, track status, see rejection reasons and before/after photos |
| Garbage Collector | Register page ("I am a: Garbage Collector"), then **approved by the MC office** | See approved tasks, tap the address to open Google Maps directions, accept a task, upload the cleaned photo, see cleaned / not-cleaned counts |
| MC Officer | `python manage.py create_officer <username> <password>` (or `createsuperuser`) | Approve / reject (with reason) every complaint and pickup, assign collectors, verify or send back cleaning, approve collector accounts |

## Workflow

```
Citizen submits  -> pending
MC office        -> approved (optionally assigned to a collector)   or   rejected (reason is mandatory)
Collector        -> accepts (in_progress) -> uploads "after" photo -> cleaned (awaiting verification)
MC office        -> resolved (counts in collector's "Cleaned")      or   sent back (reason) -> in_progress
```

The same flow is used for **complaints** and **pickup requests**.
Every address is stored as street + area + city + state + pincode; clicking it opens
Google Maps driving directions to that full address.

## Setup

```bash
pip install -r requirements.txt -r requirements-train.txt   # (torch is only needed for training / local fallback)
python manage.py migrate            # upgrades the old db.sqlite3 too (old statuses are converted)
python manage.py create_officer mc_officer StrongPass123 --name "MC Officer" --city Kanpur
python manage.py runserver
```

Quick demo data (one officer, two collectors, one citizen - password `Eco@12345`):

```bash
python manage.py seed_demo
```

Run the tests: `python manage.py test complaints`

## Existing data

* Existing accounts get a profile automatically (staff -> MC officer, others -> citizen).
* Old pickup statuses: `scheduled` -> `approved`, `completed` -> `resolved`.
* Old complaints that were "in progress" go back to `approved` so collectors can pick them up.
* Old records have no city/state/pincode; new requests require them.


## Deploy (free)

See [DEPLOY.md](DEPLOY.md) - Render free web service, CNN served with ONNX Runtime (`ml_model/waste_model.onnx`).
