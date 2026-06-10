# user-theo

Family folder for the brother's deployment at `brudersauto.alti2.de`.

**Current state:** stub. Awaiting `family.md` from Theo.

## To start the buildout

1. Theo fills in `family.md` using `vehicle-app/briefs/family_brief_template.md`
2. Read `docs/new_family_playbook.md` end-to-end
3. Execute the playbook (intake → criteria → cohort → TCO → images → deploy)
4. Provision a Railway service:
   - `VEHICLE_DATA_DIR=user-theo`
   - `VEHICLE_DB_PATH=/data/cache.db`
   - Volume mount at `/data`
5. CNAME `brudersauto.alti2.de` to the Railway-provided host
