## Vocabuilder
- Python script using PyQt6
- Build a vocabulary gradually and practice it
- Select a delay in days until a term should be practiced again
- Connect local database with firebase cloud database
- Use a separate script if you want to reset the firebase database to the current local database
- Extension to android is planned
- Incremental local backup of your database using git

## Synchronization with firebase

- If you use this script from serveral devices with the same firebase database,
    - Data is only synchronized (downloaded) with firebase database at app startup
      or when explicitly requested
- Data is uploaded continuously (each time something in the database is modified locally)

