from datetime import datetime
from typing import Optional

from temporal_db import TemporalDB

DATE_FMT = "%d/%m/%Y"
DATETIME_FMT = "%d/%m/%Y %H:%M"
TIME_FMT = "%H:%M"


class GoBack(Exception):
    pass


class GoMenu(Exception):
    pass


def smart_input(prompt: str) -> str:
    """
    Wrapper around input that supports:
    b = back (throw GoBack)
    m = menu (throw GoMenu)
    """
    val = input(prompt + "  [b = back, m = menu]: ").strip()
    if val.lower() == "b":
        raise GoBack()
    if val.lower() == "m":
        raise GoMenu()
    return val


def read_date(prompt: str) -> datetime:
    while True:
        try:
            s = smart_input(f"{prompt} (format {DATE_FMT})")
            return datetime.strptime(s.strip(), DATE_FMT)
        except GoBack:
            # נעביר את האות למעלה כדי שהקריאה תדע לחזור אחורה
            raise
        except GoMenu:
            raise
        except ValueError:
            print("Invalid date format, please try again.")


def read_optional_time(prompt: str) -> Optional[datetime.time]:
    """
    Time is optional: empty string means None.
    Also supports b/m via smart_input.
    """
    try:
        s = smart_input(f"{prompt} (format {TIME_FMT}, or empty)")
        if s == "":
            return None
        return datetime.strptime(s, TIME_FMT).time()
    except GoBack:
        raise
    except GoMenu:
        raise
    except ValueError:
        print("Invalid time format, ignoring time.")
        return None


def read_datetime(prompt: str) -> datetime:
    while True:
        try:
            s = smart_input(f"{prompt} (format {DATETIME_FMT})")
            return datetime.strptime(s.strip(), DATETIME_FMT)
        except GoBack:
            raise
        except GoMenu:
            raise
        except ValueError:
            print("Invalid datetime format, please try again.")


def show_menu():
    print("\n============== MAIN MENU ==============")
    print("1. Load data files (Excel + LOINC)")
    print("2. Retrieve single value")
    print("3. History query")
    print("4. Update value")
    print("5. Logical delete")
    print("6. Change system current time")
    print("7. Help")
    print("0. Exit")
    print("=======================================")


def show_help():
    print("\n============= HELP =============")
    print("1. Load data files:")
    print("   Load the project Excel file and the LOINC CSV file.")
    print("2. Retrieve single value:")
    print("   Get a test value (LOINC) for a patient at a specific date/time.")
    print("3. History query:")
    print("   Show all versions of a test in a valid-time range.")
    print("4. Update value:")
    print("   Logically update a measurement (same valid time, new value).")
    print("5. Logical delete:")
    print("   Logically delete a measurement.")
    print("6. Change system current time:")
    print("   Set the default perspective time of the system.")
    print("7. Help:")
    print("   Show this help screen.")
    print("0. Exit:")
    print("   Quit the program.")
    print("================================\n")


def main():
    db: Optional[TemporalDB] = None

    print("Temporal Database Project (Bi-temporal DB)")
    print("==========================================")

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        elif choice == "1":
            print("\n--- Load data files ---")
            excel_path = input("Enter Excel file path (default: project_db_2025.xlsx): ").strip()
            if excel_path == "":
                excel_path = "project_db_2025.xlsx"

            loinc_path = input("Enter LOINC CSV path (default: Loinc.csv): ").strip()
            if loinc_path == "":
                loinc_path = "Loinc.csv"

            try:
                db = TemporalDB(excel_path, loinc_path)
                print("Data loaded successfully.")
                print(f"System current time is: {db.current_time}")
            except Exception as e:
                print("Error loading data files:", e)
                db = None

        elif choice in {"2", "3", "4", "5", "6"}:
            if db is None:
                print("You must load data files first (option 1).")
                continue

            # --------- option 2: single value ----------
            if choice == "2":
                try:
                    print("\n--- Retrieve single value ---")
                    first_name = smart_input("Patient first name:")
                    last_name = smart_input("Patient last name:")
                    loinc_num = smart_input("LOINC code:")

                    date = read_date("Measurement date")
                    time = read_optional_time("Measurement time (optional)")

                    use_persp = smart_input("Set perspective time? (y/n):").lower()
                    if use_persp == "y":
                        perspective_time = read_datetime("Perspective datetime")
                    else:
                        perspective_time = None

                    result = db.query_value(
                        first_name=first_name,
                        last_name=last_name,
                        loinc_num=loinc_num,
                        date=date,
                        time=time,
                        perspective_time=perspective_time,
                    )

                    if result is None:
                        print("No measurement found for the given criteria.")
                    else:
                        print("\nResult:")
                        print(f"Patient: {result['first_name']} {result['last_name']}")
                        print(f"LOINC: {result['loinc']} ({result['long_common_name']})")
                        unit = result['unit']
                        if unit is None or str(unit).lower() == "nan":
                            print(f"Value: {result['value']}")
                        else:
                            print(f"Value: {result['value']} {unit}")

                        print(f"Valid time: {result['valid_time']}")
                        print(f"System from: {result['system_from']}")
                        print(f"System to: {result['system_to']}")

                except GoBack:
                    print("↩ Returning to previous step...\n")
                    # אין ממש "שלב קודם" ברמת ה-loop, אז פשוט חוזרים לתפריט הבא
                except GoMenu:
                    print("↩ Returning to main menu...\n")
                    continue

            # --------- option 3: history ----------
            elif choice == "3":
                try:
                    print("\n--- History query ---")
                    first_name = smart_input("Patient first name:")
                    last_name = smart_input("Patient last name:")
                    loinc_num = smart_input("LOINC code:")

                    valid_from = read_date("Valid-time FROM date")
                    valid_to = read_date("Valid-time TO date")

                    history = db.query_history(
                        first_name=first_name,
                        last_name=last_name,
                        loinc_num=loinc_num,
                        valid_from=valid_from,
                        valid_to=valid_to
                    )

                    if not history:
                        print("No history records found in this range.")
                    else:
                        print(f"\nFound {len(history)} records:")
                        for rec in history:
                            print("--------------------------------")
                            print(f"Valid time: {rec['valid_time']}")
                            print(f"Value: {rec['value']} {rec['unit']}")
                            print(f"System from: {rec['system_from']}")
                            print(f"System to: {rec['system_to']}")
                            print(f"Test: {rec['long_common_name']}")
                except GoBack:
                    print("↩ Returning to previous step...\n")
                except GoMenu:
                    print("↩ Returning to main menu...\n")
                    continue

            # --------- option 4: update ----------
            elif choice == "4":
                try:
                    print("\n--- Update value ---")
                    first_name = smart_input("Patient first name:")
                    last_name = smart_input("Patient last name:")
                    loinc_num = smart_input("LOINC code:")

                    valid_dt = read_datetime("Measurement valid datetime")
                    new_value = smart_input("New value:")

                    db.update_value(
                        first_name=first_name,
                        last_name=last_name,
                        loinc_num=loinc_num,
                        valid_time=valid_dt,
                        new_value=new_value,
                    )
                except GoBack:
                    print("↩ Returning to previous step...\n")
                except GoMenu:
                    print("↩ Returning to main menu...\n")
                    continue

            # --------- option 5: delete ----------
            elif choice == "5":
                try:
                    print("\n--- Logical delete ---")
                    first_name = smart_input("Patient first name:")
                    last_name = smart_input("Patient last name:")
                    loinc_num = smart_input("LOINC code:")

                    date = read_date("Measurement date (valid date)")
                    time = read_optional_time("Measurement time (optional)")

                    db.delete_value(
                        first_name=first_name,
                        last_name=last_name,
                        loinc_num=loinc_num,
                        date=date,
                        time=time,
                    )
                except GoBack:
                    print("↩ Returning to previous step...\n")
                except GoMenu:
                    print("↩ Returning to main menu...\n")
                    continue

            # --------- option 6: change current time ----------
            elif choice == "6":
                try:
                    print("\n--- Change system current time ---")
                    new_now = read_datetime("New system current datetime")
                    db.set_current_time(new_now)
                    print(f"System current time updated to: {db.current_time}")
                except GoBack:
                    print("↩ Returning to previous step...\n")
                except GoMenu:
                    print("↩ Returning to main menu...\n")
                    continue

        elif choice == "7":
            show_help()

        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
