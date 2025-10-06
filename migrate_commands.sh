# Run these commands from your project root

# 1. Generate a new migration (edit message as needed)
flask db migrate -m "Update measure fields, step ordering, assignment dates, add company/measures CRUD"

# 2. (Optional) Edit the generated migration file in 'migrations/versions/' to:
#    - Rename columns (e.g. description -> measure_detail, order_index -> step)
#    - Add/remove columns (start_date, end_date, final_remarks, etc.)

# 3. Apply the migration to your database
flask db upgrade

# 4. (Optional) Check migration status
flask db history
