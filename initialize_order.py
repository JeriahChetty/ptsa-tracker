from app import create_app, db
import sqlalchemy as sa
from sqlalchemy.sql import text

def initialize_order_values():
    """Initialize order values for measures and steps using direct SQL."""
    app = create_app()
    
    with app.app_context():
        connection = db.engine.connect()
        
        try:
            print("Initializing measure order...")
            # Check if measures table has the order column
            inspector = sa.inspect(db.engine)
            measure_columns = [c['name'] for c in inspector.get_columns('measures')]
            
            if 'order' in measure_columns:
                # Set order values for measures
                measures = connection.execute(text("SELECT id FROM measures ORDER BY created_at ASC")).fetchall()
                for i, measure in enumerate(measures):
                    connection.execute(
                        text("UPDATE measures SET \"order\" = :order WHERE id = :id"),
                        {"order": i, "id": measure[0]}
                    )
                print(f"Set order for {len(measures)} measures")
            else:
                print("The 'order' column does not exist in measures table.")
            
            # Determine the correct steps table name
            if 'steps' in inspector.get_table_names():
                steps_table = 'steps'
                measure_id_col = 'measure_id'
            elif 'measure_steps' in inspector.get_table_names():
                steps_table = 'measure_steps'
                measure_id_col = 'measure_id'
            else:
                print("Could not find a steps table.")
                return
            
            # Check if steps table has the order column
            step_columns = [c['name'] for c in inspector.get_columns(steps_table)]
            if 'order' in step_columns:
                print(f"Initializing step order for table {steps_table}...")
                
                # Get all measures
                measures = connection.execute(text("SELECT id FROM measures")).fetchall()
                
                # For each measure, set the order of its steps
                for measure in measures:
                    measure_id = measure[0]
                    steps = connection.execute(
                        text(f"SELECT id FROM {steps_table} WHERE {measure_id_col} = :measure_id ORDER BY created_at ASC"),
                        {"measure_id": measure_id}
                    ).fetchall()
                    
                    for i, step in enumerate(steps):
                        connection.execute(
                            text(f"UPDATE {steps_table} SET \"order\" = :order WHERE id = :id"),
                            {"order": i, "id": step[0]}
                        )
                    
                    if steps:
                        print(f"Set order for {len(steps)} steps for measure ID {measure_id}")
            else:
                print(f"The 'order' column does not exist in {steps_table} table.")
            
            print("Order initialization completed successfully!")
            
        except Exception as e:
            print(f"Error initializing order values: {str(e)}")
        finally:
            connection.close()

if __name__ == "__main__":
    initialize_order_values()
