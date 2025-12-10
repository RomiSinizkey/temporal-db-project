# Bi-Temporal Medical Database Project

This project implements a **bi-temporal medical database** system in Python.  
It supports full separation between:

- **Valid Time** – when the medical measurement was actually taken.
- **Transaction Time** – when the record was inserted, updated, or logically deleted in the system.

The system allows querying historical and current data correctly according to temporal database principles.

---

## ✅ Features

- Load medical data from Excel (`project_db_2025.xlsx`)
- Load LOINC mapping from CSV (`Loinc.csv`)
- Single value retrieval with valid-time and transaction-time logic
- Bi-temporal **history queries**
- **Logical delete** using `system_to` (no physical deletions)
- **Updates** create new versions with the same valid time
- System perspective time control
- Back (`b`) and Menu (`m`) navigation inside the CLI
- Full offline operation (no external services)

---

## 🗂 Project Structure

temporal-db-project/
├── main.py
├── temporal_db.py
├── project_db_2025.xlsx
├── Loinc.csv
├── .gitignore
└── README.md


---

## ▶️ How to Run

1. Install dependencies:
```bash
pip install pandas openpyxl
```

2. Run the program:

```bash
python main.py
```

3. Load data:
```bash
- Choose option 1

- Press Enter for both default file paths:

-   project_db_2025.xlsx

- Loinc.csv

You should see:
Data loaded successfully.
System current time is: ...

```
-------------------------
## 🧠 Supported Queries
### 1️⃣ Retrieve Single Measurement

- By exact date & time

- Or by date only → returns the latest alive measurement of that day

### 2️⃣ History Query

- Shows all historical versions of a measurement within a valid-time range.

### 3️⃣ Update

- Creates a new version with:

- Same valid time

- New transaction time

### 4️⃣ Logical Delete

- Closes the record using system_to
→ The record still exists historically.

### 5️⃣ Change System Time

- Simulate queries from any historical point in time.

-------------------

## 🧪 Bi-Temporal Logic Explanation

- If date + time is provided → an exact valid-time match is required.

- If only date is provided → the system returns the latest alive measurement of that day.

- If multiple versions exist at the same valid time → the latest transaction version is selected.

- Deletion is implemented as a logical deletion using system_to only.

- Older versions always remain preserved for historical queries.

------------------
## 🔐 Offline Guarantee

- This project runs 100% offline:

- No APIs

- No ChatGPT

- No external network calls

- All logic is implemented locally in Python
- -----

## 👨‍🎓 Author

Developed by:
[Romi Sinizkey]
Computer Science Student – Temporal Databases Project

---------
## 📌 Notes for Evaluation

- The project follows bi-temporal database theory

- All deletions are logical

- Historical states are preserved

- All required project queries return correct answers

- The system supports full temporal reconstruction
- ---

