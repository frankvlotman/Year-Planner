import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import json
import os
from PIL import Image
from datetime import datetime, date
import webbrowser
import tempfile

# Constants
APP_NAME = "Year_Planner"  # Name of your application
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", APP_NAME)
TASKS_FILE = os.path.join(APP_DATA_DIR, "tasks.json")
ICON_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "blank.ico")  # Update this path if necessary

# Function to create a blank (transparent) ICO file if it doesn't exist
def create_blank_ico(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory for icon at {directory}")
    if not os.path.exists(path):
        size = (16, 16)  # Size of the icon
        image = Image.new("RGBA", size, (255, 255, 255, 0))  # Transparent image
        image.save(path, format="ICO")
        print(f"Created blank icon at {path}")

create_blank_ico(ICON_PATH)

# Initialize tasks data structure
tasks_data = {}

def inputError(task):
    """Validate that the task input is not empty."""
    if task.strip() == "":
        messagebox.showerror("Input Error", "Please enter a task.")
        return False
    return True

def validate_tasks_data(data):
    """Validate the structure of tasks_data."""
    if not isinstance(data, dict):
        return False
    for year, months in data.items():
        if not isinstance(year, str) or not year.isdigit():
            return False
        if not isinstance(months, dict):
            return False
        for month, days in months.items():
            if not isinstance(month, str) or not month.isdigit():
                return False
            if not isinstance(days, dict):
                return False
            for day, tasks in days.items():
                if not isinstance(day, str) or not day.isdigit():
                    return False
                if not isinstance(tasks, list):
                    return False
                for task in tasks:
                    if not isinstance(task, str):
                        return False
    return True

def load_tasks():
    """Load tasks_data from the JSON file with validation and backup."""
    global tasks_data
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                loaded_data = json.load(f)
                print("Type of loaded_data:", type(loaded_data))  # Debugging line
                print("Content of loaded_data:", loaded_data)     # Debugging line
                if validate_tasks_data(loaded_data):
                    tasks_data = loaded_data
                    print("tasks.json loaded successfully.")
                else:
                    raise ValueError("tasks.json has an invalid structure.")
        except Exception as e:
            # Backup the corrupted file
            backup_path = TASKS_FILE + ".backup"
            try:
                os.rename(TASKS_FILE, backup_path)
                print(f"Corrupted tasks.json backed up as {backup_path}")
            except Exception as rename_error:
                print(f"Failed to backup corrupted tasks.json: {rename_error}")
            messagebox.showerror(
                "Load Error",
                f"tasks.json is corrupted or invalid.\nA backup has been created at {backup_path}.\nResetting tasks."
            )
            tasks_data = {}
    else:
        tasks_data = {}
        print("tasks.json does not exist. Starting with an empty tasks_data.")
    print("Loaded tasks_data:", json.dumps(tasks_data, indent=4))  # Debugging line

def save_tasks():
    """Save the tasks_data to the JSON file atomically."""
    try:
        # Ensure the application data directory exists
        if not os.path.exists(APP_DATA_DIR):
            os.makedirs(APP_DATA_DIR)
            print(f"Created application data directory at {APP_DATA_DIR}")
        
        temp_file = TASKS_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(tasks_data, f, indent=4)
        os.replace(temp_file, TASKS_FILE)  # Atomic operation
        print(f"tasks.json saved successfully at {TASKS_FILE}")
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred while saving tasks:\n{e}")
        print(f"Error saving tasks.json: {e}")

def highlight_dates():
    """
    Highlight dates in the calendar that have tasks.
    """
    for cal in calendar_tabs.values():
        year = cal['year']
        month = cal['month']
        cal_widget = cal['widget']
        
        # Remove existing 'task' tags to prevent duplication
        cal_widget.calevent_remove('task', date=None)  # Remove all 'task' events
        
        # Collect dates with tasks
        dates_with_tasks = []
        if str(year) in tasks_data and str(month) in tasks_data[str(year)]:
            dates_with_tasks = [int(day) for day in tasks_data[str(year)][str(month)]]
        
        # Apply tags
        for day in dates_with_tasks:
            try:
                date_obj = date(year, month, day)  # Ensure it's a datetime.date instance
                cal_widget.calevent_create(date_obj, 'Task', 'task')  # Pass date_obj directly
                print(f"Highlighting date: {date_obj}")  # Debugging line
            except Exception as e:
                print(f"Error highlighting date {year}-{month}-{day}: {e}")
        
        # Configure the 'task' tag to have a different background color
        cal_widget.tag_config('task', background='lightblue', foreground='black')
        
        # Refresh the calendar to display changes
        cal_widget.update_idletasks()

def on_date_click(event, cal_widget, selected_date_var):
    """
    Handle date selection and display tasks.
    """
    try:
        selected_date = cal_widget.selection_get()
        selected_date_var.set(selected_date.strftime("%Y-%m-%d"))
        display_tasks_for_selected_date(selected_date)
    except Exception as e:
        messagebox.showerror("Date Selection Error", f"An error occurred while selecting the date:\n{e}")

def display_tasks_for_selected_date(selected_date):
    """
    Display tasks for the selected date in the TextArea.
    """
    TextArea.config(state=tk.NORMAL)
    TextArea.delete(1.0, tk.END)
    date_str = selected_date.strftime("%Y-%m-%d")
    year = str(selected_date.year)
    month = str(selected_date.month)
    day = str(selected_date.day)
    if year in tasks_data and month in tasks_data[year] and day in tasks_data[year][month]:
        for idx, task in enumerate(tasks_data[year][month][day], start=1):
            TextArea.insert(tk.END, f"[ {idx} ] {task}\n", "task")
    else:
        TextArea.insert(tk.END, "No tasks for this date.", "no_task")
    TextArea.config(state=tk.DISABLED)

def add_task():
    """
    Add a task to the selected date.
    """
    task = enterTaskField.get().strip()
    if not inputError(task):
        return
    date_str = selected_date_var.get()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messagebox.showerror("Date Error", "Selected date is invalid. Please select a valid date.")
        return
    year = str(selected_date.year)
    month = str(selected_date.month)
    day = str(selected_date.day)
    
    # Initialize nested dictionaries if necessary
    if year not in tasks_data:
        tasks_data[year] = {}
    if month not in tasks_data[year]:
        tasks_data[year][month] = {}
    if day not in tasks_data[year][month]:
        tasks_data[year][month][day] = []
    
    tasks_data[year][month][day].append(task)
    save_tasks()
    highlight_dates()
    display_tasks_for_selected_date(selected_date)
    enterTaskField.delete(0, tk.END)
    print(f"Added task '{task}' on {selected_date}")

def delete_task():
    """
    Delete a task from the selected date based on task number.
    """
    task_no_str = taskNumberField.get("1.0", tk.END).strip()
    if not task_no_str.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid task number.")
        return
    task_no = int(task_no_str)
    date_str = selected_date_var.get()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messagebox.showerror("Date Error", "Selected date is invalid. Please select a valid date.")
        return
    year = str(selected_date.year)
    month = str(selected_date.month)
    day = str(selected_date.day)
    
    if year in tasks_data and month in tasks_data[year] and day in tasks_data[year][month]:
        if 1 <= task_no <= len(tasks_data[year][month][day]):
            removed_task = tasks_data[year][month][day].pop(task_no - 1)
            if not tasks_data[year][month][day]:
                del tasks_data[year][month][day]
            save_tasks()
            highlight_dates()
            display_tasks_for_selected_date(selected_date)
            taskNumberField.delete("1.0", tk.END)
            messagebox.showinfo("Task Deleted", f"Task '{removed_task}' has been deleted successfully.")
            print(f"Deleted task '{removed_task}' from {selected_date}")
        else:
            messagebox.showerror("Invalid Task Number", "Please enter a valid task number.")
    else:
        messagebox.showerror("No Task", "There are no tasks to delete for the selected date.")

def clear_all_tasks():
    """
    Clear all tasks for the selected date.
    """
    date_str = selected_date_var.get()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messagebox.showerror("Date Error", "Selected date is invalid. Please select a valid date.")
        return
    year = str(selected_date.year)
    month = str(selected_date.month)
    day = str(selected_date.day)
    
    if year in tasks_data and month in tasks_data[year] and day in tasks_data[year][month]:
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all tasks for this date?"):
            del tasks_data[year][month][day]
            save_tasks()
            highlight_dates()
            display_tasks_for_selected_date(selected_date)
            messagebox.showinfo("Tasks Cleared", "All tasks for the selected date have been deleted.")
            print(f"Cleared all tasks from {selected_date}")
    else:
        messagebox.showinfo("No Tasks", "There are no tasks to clear for the selected date.")

def exit_and_restart():
    """Exit the application."""
    save_tasks()
    gui.quit()

def show_tasks_html():
    """
    Generate an HTML file listing all tasks with interactive buttons by year and month
    and open it in the default web browser.
    """
    # Start building the HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tasks Overview</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }
            h1 { color: #333; text-align: center; }
            .nav-bar { text-align: center; margin-bottom: 20px; }
            .nav-bar button {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 10px 20px;
                margin: 5px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                cursor: pointer;
                border-radius: 4px;
                transition: background-color 0.3s;
            }
            .nav-bar button:hover {
                background-color: #45a049;
            }
            .date-section { margin-bottom: 20px; display: none; }
            .date-title { font-size: 1.2em; color: #555; margin-bottom: 10px; }
            ul { list-style-type: disc; margin-left: 20px; }
            li { margin-bottom: 5px; }
            #allTasksBtn { background-color: #008CBA; } /* Blue */
            #allTasksBtn:hover { background-color: #007bb5; }
            /* Year Buttons */
            .year-section { margin-bottom: 30px; }
            .year-title { font-size: 1.5em; color: #333; margin-top: 20px; }
            .month-buttons { text-align: center; margin-bottom: 10px; }
        </style>
        <script>
            var selectedYear = null;

            function showAllTasks() {
                // Hide all date sections
                var sections = document.getElementsByClassName('date-section');
                for (var i = 0; i < sections.length; i++) {
                    sections[i].style.display = 'none';
                }
                // Show all tasks
                var allSections = document.getElementsByClassName('date-section-all');
                for (var i = 0; i < allSections.length; i++) {
                    allSections[i].style.display = 'block';
                }
                // Reset selectedYear
                selectedYear = null;
            }

            function setYear(year) {
                selectedYear = year;
                // Hide all date sections
                var sections = document.getElementsByClassName('date-section');
                for (var i = 0; i < sections.length; i++) {
                    sections[i].style.display = 'none';
                }
                // Show date sections for the selected year
                var yearSections = document.getElementsByClassName('year-' + year);
                for (var i = 0; i < yearSections.length; i++) {
                    yearSections[i].style.display = 'block';
                }
            }

            function toggleMonth(year, month) {
                // Show or hide tasks for a specific month in a specific year
                var sectionId = 'section-' + year + '-' + month;
                var section = document.getElementById(sectionId);
                if (section.style.display === 'block') {
                    section.style.display = 'none';
                } else {
                    // Hide other sections for the same year
                    var yearSections = document.getElementsByClassName('month-section-' + year);
                    for (var i = 0; i < yearSections.length; i++) {
                        if (yearSections[i].id !== sectionId) {
                            yearSections[i].style.display = 'none';
                        }
                    }
                    section.style.display = 'block';
                }
            }
        </script>
    </head>
    <body>
        <h1>All Tasks</h1>
        <div class="nav-bar">
            <button id="allTasksBtn" onclick="showAllTasks()">All Tasks</button>
    """

    # Extract all unique years from tasks_data
    unique_years = sorted([int(year) for year in tasks_data.keys()])

    # Add buttons for each unique year
    for year in unique_years:
        html_content += f'            <button onclick="setYear({year})">{year}</button>\n'

    html_content += """
        </div>
    """

    # Iterate through tasks_data to populate the HTML
    for year in sorted(tasks_data.keys()):
        html_content += f'        <div class="year-section year-{year}">\n'
        html_content += f'            <div class="year-title">{year}</div>\n'
        # Create month buttons for the year
        months_in_year = sorted([int(month) for month in tasks_data[year].keys()])
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        html_content += '            <div class="month-buttons">\n'
        for month in months_in_year:
            month_name = month_names[month - 1]
            html_content += f'                <button onclick="toggleMonth({year}, {month})">{month_name}</button>\n'
        html_content += '            </div>\n'

        # Add task sections for each month
        for month in sorted(tasks_data[year].keys(), key=lambda x: int(x)):
            month_name = month_names[int(month) - 1]
            section_id = f'section-{year}-{month}'
            html_content += f'            <div class="date-section month-section-{year}" id="{section_id}">\n'
            for day in sorted(tasks_data[year][month].keys(), key=lambda x: int(x)):
                tasks = tasks_data[year][month][day]
                date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    formatted_date = date_obj.strftime("%B %d, %Y")
                except ValueError:
                    formatted_date = date_str  # Fallback if date parsing fails

                html_content += f'                <div class="date-title">{formatted_date}</div>\n'
                html_content += '                <ul>\n'
                for task in tasks:
                    html_content += f'                    <li>{task}</li>\n'
                html_content += '                </ul>\n'
            html_content += '            </div>\n'
        html_content += '        </div>\n'

    # Close the HTML tags
    html_content += """
    </body>
    </html>
    """

    # Create a temporary HTML file
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as tmp_file:
            tmp_file.write(html_content)
            tmp_file_path = tmp_file.name
        print(f"Generated tasks HTML at {tmp_file_path}")
    except Exception as e:
        messagebox.showerror("HTML Generation Error", f"An error occurred while generating the tasks HTML:\n{e}")
        print(f"Error generating tasks HTML: {e}")
        return

    # Open the HTML file in the default web browser
    try:
        webbrowser.open(f'file://{tmp_file_path}')
        print("Opened tasks HTML in the default web browser.")
    except Exception as e:
        messagebox.showerror("Browser Error", f"An error occurred while opening the tasks HTML in the browser:\n{e}")
        print(f"Error opening browser: {e}")

def setup_calendar_tabs():
    """
    Create a tab for each month and add a Calendar widget.
    """
    for month in range(1, 13):
        month_name = datetime(current_year, month, 1).strftime('%B')
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=month_name)
        
        # Determine the day to select
        if month == default_selected_date.month and current_year == default_selected_date.year:
            day = default_selected_date.day
        else:
            day = 1
        
        # Create a Calendar widget for the month with the appropriate day selected
        cal = Calendar(
            tab, 
            selectmode='day', 
            year=start_year, 
            month=month, 
            day=day,
            date_pattern='y-mm-dd'
        )
        cal.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Bind the date click event using default arguments to capture current cal
        cal.bind("<<CalendarSelected>>", lambda event, cal=cal: on_date_click(event, cal, selected_date_var))
        
        # Store calendar info for highlighting
        calendar_tabs[month] = {
            'year': start_year,  # Starting from current year
            'month': month,
            'widget': cal
        }

def update_calendar_year(new_year):
    """
    Update all calendar widgets to the selected year.
    Also, reset the selected_date_var to a default date in the new year.
    """
    for month, cal_info in calendar_tabs.items():
        cal_widget = cal_info['widget']
        cal_widget.calevent_remove('task', date=None)  # Clear existing events
        cal_widget.config(year=new_year)
        cal_info['year'] = new_year  # Update the year in the dictionary
    highlight_dates()
    
    # Reset selected_date_var to January 1st of the new year if it was outside the new year
    try:
        current_selected_date = datetime.strptime(selected_date_var.get(), "%Y-%m-%d").date()
        if current_selected_date.year != new_year:
            default_date = date(new_year, 1, 1)
            selected_date_var.set(default_date.strftime("%Y-%m-%d"))
            display_tasks_for_selected_date(default_date)
            print(f"Selected date reset to {default_date} due to year change.")
    except ValueError:
        # If the current selected_date_var is invalid, reset to January 1st
        default_date = date(new_year, 1, 1)
        selected_date_var.set(default_date.strftime("%Y-%m-%d"))
        display_tasks_for_selected_date(default_date)
        print(f"Selected date reset to {default_date} due to invalid date format.")

def on_year_change(event):
    """
    Handle year change and update calendars accordingly.
    """
    try:
        selected_year = int(year_var.get())
        update_calendar_year(selected_year)
        print(f"Year changed to {selected_year}. Calendars updated.")
    except ValueError:
        messagebox.showerror("Input Error", "Please select a valid year.")
        print("Invalid year selection attempted.")

# Initialize the main GUI
if __name__ == "__main__":
    gui = tk.Tk()
    gui.title("Year Planner")
    gui.geometry("720x720")  # Adjust as needed
    gui.configure(bg="#f0f0f0")

    # Initialize ttk.Style
    style = ttk.Style()
    style.theme_use("clam")  # Use 'clam' theme for better customization

    # Define custom style for buttons
    style.configure("Custom.TButton",
                    background="#d0e8f1",
                    foreground="black",
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=5)  # Reduced padding for compactness

    # Define style map for hover (active) state
    style.map("Custom.TButton",
              background=[('active', '#87CEFA')],
              foreground=[('active', 'black')])

    # Define widget styles to avoid conflict with ttk.Style
    widget_style = {"background": "#f0f0f0", "foreground": "#333333", "font": ("Arial", 10)}  # Adjust as needed

    # Load tasks from file
    load_tasks()

    # Create a Scrollable Canvas
    main_canvas = tk.Canvas(gui, bg="#f0f0f0")
    main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a vertical scrollbar to the Canvas
    scrollbar = ttk.Scrollbar(gui, orient=tk.VERTICAL, command=main_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the Canvas to work with the scrollbar
    main_canvas.configure(yscrollcommand=scrollbar.set)
    main_canvas.bind('<Configure>', lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

    # Create a Frame inside the Canvas to hold all other widgets
    scrollable_frame = tk.Frame(main_canvas, bg="#f0f0f0")
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

    # Create a Notebook (tabbed interface) inside the scrollable_frame
    notebook = ttk.Notebook(scrollable_frame)
    notebook.pack(pady=5, padx=5, fill='both', expand=True)  # Adjust as needed

    # Dictionary to store calendar widgets
    calendar_tabs = {}

    # Set the starting year to the current year
    start_year = datetime.now().year
    current_year = start_year

    # Initialize the current date
    default_selected_date = datetime.now().date()

    # Setup calendar tabs for the starting year
    setup_calendar_tabs()

    # Set the notebook to the current month tab
    current_month = datetime.now().month
    notebook.select(current_month - 1)
    print(f"Calendar set to current month: {current_month}.")

    # Year selection
    control_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
    control_frame.pack(pady=2, padx=5, fill='x')  # Adjust as needed

    year_label = tk.Label(control_frame, text="Select Year:", **widget_style)
    year_label.pack(side=tk.LEFT, padx=(0,5))

    years = list(range(start_year, start_year + 10))  # Next 10 years
    year_var = tk.StringVar()
    year_dropdown = ttk.Combobox(control_frame, values=years, state="readonly", width=5, textvariable=year_var, font=("Arial", 10))
    current_year = datetime.now().year
    if current_year < start_year:
        year_dropdown.current(0)
    elif current_year > start_year + 9:
        year_dropdown.current(0)
    else:
        year_dropdown.current(current_year - start_year)
    year_dropdown.pack(side=tk.LEFT, padx=(0,10))
    year_dropdown.bind("<<ComboboxSelected>>", on_year_change)
    print(f"Year dropdown initialized to {year_var.get()}.")

    # Initialize selected_date_var to today's date
    selected_date_var = tk.StringVar()
    selected_date_var.set(default_selected_date.strftime("%Y-%m-%d"))

    selected_date_label = tk.Label(scrollable_frame, text="Selected Date:", **widget_style)
    selected_date_label.pack(pady=(5,0), padx=5, anchor='w')

    selected_date_entry = tk.Entry(scrollable_frame, textvariable=selected_date_var, state='readonly', width=15, font=("Arial", 10))  # Adjust as needed
    selected_date_entry.pack(padx=5, anchor='w')

    # Task Entry
    enterTaskLabel = tk.Label(scrollable_frame, text="Enter Your Task:", **widget_style)
    enterTaskLabel.pack(pady=(5, 2), padx=5, anchor='w')

    # Create a Frame for Task Entry
    task_entry_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
    task_entry_frame.pack(pady=2, padx=5, fill='x')

    enterTaskField = tk.Entry(task_entry_frame, width=60, font=("Arial", 10))  # Adjust as needed
    enterTaskField.pack(side=tk.LEFT, fill='x', expand=True)

    submitButton = ttk.Button(scrollable_frame, text="Add Task", style="Custom.TButton", command=add_task)
    submitButton.pack(pady=2, padx=5, anchor='w')  # Adjust as needed

    # Tasks display area with Scrollbar
    task_display_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
    task_display_frame.pack(pady=5, padx=5, fill='both', expand=True)

    # Create TextArea
    TextArea = tk.Text(task_display_frame, height=8, width=70, bg="white", fg="black", font=("Arial", 10))  # Adjust as needed
    TextArea.pack(side=tk.LEFT, fill='both', expand=True)

    # Create Vertical Scrollbar for TextArea
    text_scrollbar = ttk.Scrollbar(task_display_frame, orient='vertical', command=TextArea.yview)
    text_scrollbar.pack(side=tk.RIGHT, fill='y')

    # Configure TextArea to use the scrollbar
    TextArea.config(yscrollcommand=text_scrollbar.set)

    TextArea.config(state=tk.DISABLED)

    # Configure tags for styling text in TextArea
    TextArea.tag_configure("task", font=("Calibri", 10), foreground="black")  # Adjust as needed
    TextArea.tag_configure("no_task", font=("Calibri", 10), foreground="gray")  # Adjust as needed

    # Delete Task Number
    taskNumberLabel = tk.Label(scrollable_frame, text="Delete Task Number:", **widget_style)
    taskNumberLabel.pack(pady=(5, 2), padx=5, anchor='w')

    # Create a Frame for Delete Task Number
    delete_task_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
    delete_task_frame.pack(pady=2, padx=5, fill='x')

    taskNumberField = tk.Text(delete_task_frame, height=1, width=5, bg="white", fg="black", font=("Arial", 10))  # Adjust as needed
    taskNumberField.pack(side=tk.LEFT, padx=(0,5))

    deleteButton = ttk.Button(scrollable_frame, text="Delete Task", style="Custom.TButton", command=delete_task)
    deleteButton.pack(pady=2, padx=5, anchor='w')  # Adjust as needed

    # Clear All Tasks Button
    clearAllButton = ttk.Button(scrollable_frame, text="Clear All Tasks for Selected Date", style="Custom.TButton", command=clear_all_tasks)
    clearAllButton.pack(pady=2, padx=5, anchor='w')  # Adjust as needed

    # Frame for bottom buttons
    button_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
    button_frame.pack(pady=5, padx=5, fill='x')  # Adjust as needed

    # Configure button frame to expand (using two columns now)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    # Exit button
    exitButton = ttk.Button(button_frame, text="Exit", style="Custom.TButton", command=exit_and_restart)
    exitButton.grid(row=0, column=0, padx=2, sticky=tk.EW)

    # Tasks button
    tasksButton = ttk.Button(button_frame, text="Tasks", style="Custom.TButton", command=show_tasks_html)
    tasksButton.grid(row=0, column=1, padx=2, sticky=tk.EW)

    # Set the blank icon to the Tkinter window
    try:
        gui.iconbitmap(ICON_PATH)
        print(f"Icon set successfully from {ICON_PATH}.")
    except Exception as e:
        print(f"Error setting icon: {e}")

    # Update tasks display based on the initially selected date
    try:
        selected_date = datetime.strptime(selected_date_var.get(), "%Y-%m-%d").date()
    except:
        selected_date = default_selected_date
    display_tasks_for_selected_date(selected_date)

    # Highlight dates with tasks
    highlight_dates()

    # Start the GUI main loop
    try:
        gui.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user.")
    finally:
        # Ensure the application closes properly
        gui.destroy()
        print("Application closed.")
