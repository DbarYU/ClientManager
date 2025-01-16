import json
import os
import shutil
import webbrowser
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText

# If you have modules in a package:
from util.data_getter import get_prev_update
from sec_cik_mapper import StockMapper


class CRMApp:
    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title("Client Relationship Manager")
        self.root.geometry("800x500")

        # Data storage (list of dictionaries)
        self.clients = []
        self.data_file = "clients.json"

        # Load existing data
        self.load_clients()

        # Create an executor for background tasks
        self.executor = ThreadPoolExecutor()

        # If you have a StockMapper that maps CIK -> Ticker
        mapper = StockMapper()
        self.cik_to_ticker = mapper.cik_to_tickers

        # Build the UI
        self.setup_ui()

        # Save data when the app is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Optional: Scan all clients at startup
        self.scan_all_clients()

    def setup_ui(self):
        # Title
        title_label = ttk.Label(
            master=self.root,
            text="Client Relationship Manager",
            font="-size 18 -weight bold"
        )
        title_label.pack(pady=(10, 0))

        # Frame for the input form (Ticker/CIK entry)
        form_frame = ttk.Frame(self.root, padding=10)
        form_frame.pack(fill=ttk.X, padx=20, pady=(10, 5))

        ticker_label = ttk.Label(form_frame, text="Ticker/CIK:", font="-size 11")
        ticker_label.grid(row=0, column=0, sticky=ttk.W, padx=5, pady=5)

        self.ticker_entry = ttk.Entry(form_frame, font="-size 11")
        self.ticker_entry.grid(row=0, column=1, sticky=ttk.W, padx=5, pady=5)

        # Button Frame
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=ttk.X, padx=20, pady=5)

        add_button = ttk.Button(button_frame, text="Add Client", bootstyle=SUCCESS, command=self.start_add_client)
        add_button.grid(row=0, column=0, padx=5, pady=5)

        delete_button = ttk.Button(button_frame, text="Delete Client", command=self.delete_client)
        delete_button.grid(row=0, column=1, padx=5, pady=5)

        search_button = ttk.Button(button_frame, text="Search Client", command=self.search_client)
        search_button.grid(row=0, column=2, padx=5, pady=5)

        show_all_button = ttk.Button(button_frame, text="Show All Clients", command=self.show_all_clients)
        show_all_button.grid(row=0, column=3, padx=5, pady=5)

        scan_all_button = ttk.Button(button_frame, text="Scan for Updates", command=self.scan_all_clients)
        scan_all_button.grid(row=0, column=4, padx=5, pady=5)

        # Treeview Frame
        tree_frame = ttk.Frame(self.root, padding=10)
        tree_frame.pack(fill=ttk.BOTH, expand=True, padx=20, pady=10)

        columns = ("ticker", "company_name", "prev_update_date", "contents", "press_release_links")
        self.tree = ttk.Treeview(
            master=tree_frame,
            columns=columns,
            show="headings",
            bootstyle=INFO,  # Just for a different style effect
            height=12
        )
        self.tree.heading("ticker", text="Ticker/CIK")
        self.tree.heading("company_name", text="Company Name")
        self.tree.heading("prev_update_date", text="Previous Update Date")
        self.tree.heading("contents", text="Contents")
        self.tree.heading("press_release_links", text="Press Release Links")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=ttk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=ttk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack Treeview and Scrollbars
        self.tree.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)
        vsb.pack(side=ttk.LEFT, fill=ttk.Y)
        hsb.pack(side=ttk.BOTTOM, fill=ttk.X)

        # Bind double-click event for showing full contents or opening a link
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Configure a tag for updated rows (yellow background)
        self.tree.tag_configure("updated", background="yellow")

        # Populate treeview with existing clients
        self.show_all_clients()

    def start_add_client(self):
        """Trigger the add_client in the background."""
        self.add_client()

    def add_client(self, ticker=None):
        """Add a client (ticker/cik) to the list and fetch background data."""
        if ticker is None:
            ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            Messagebox.show_error("Must insert Ticker/CIK", "Error")
            return

        if ticker.isdigit():
            # Attempt to map CIK -> Ticker
            try:
                ticker = self.cik_to_ticker.get(ticker)
            except ValueError:
                Messagebox.show_error("Ticker/CIK is not valid", "Error")
                return

        co = yf.Ticker(ticker)
        company_name = co.info.get("longName", "Unknown Company")

        # Check if client already exists
        for client in self.clients:
            if client["ticker"] == ticker:
                Messagebox.show_error(f"Client {ticker} already exists", "Error")
                return

        # Insert a temporary row in the tree with "loading" placeholders
        temp_row_id = self.tree.insert(
            "", "end",
            values=(ticker, company_name, "Getting data...", "Getting data...", "Getting data...")
        )

        # Fetch data in background
        self.executor.submit(self.fetch_data_and_update_tree, ticker, company_name, temp_row_id)

    def fetch_data_and_update_tree(self, ticker, company_name, row_id):
        """Fetch data (summary, date, press_release_links) from a blocking function in background."""
        try:
            summary, date, pr_link, accession_number = get_prev_update(ticker)

            # Update the tree row from main GUI thread
            self.root.after(0, self.update_tree_row, row_id, ticker, company_name, date, summary, pr_link)

            # Mark this as a new client with `has_updates=True`
            self.clients.append({
                "ticker": ticker,
                "company_name": company_name,
                "prev_update_date": date,
                "contents": summary,
                "press_release_links": pr_link,
                "accession_number": accession_number,
                "has_updates": True  # new client => highlight
            })
            self.save_clients()

        except Exception as e:
            self.root.after(0, self.handle_add_client_error, row_id, str(e))

    def handle_add_client_error(self, row_id, error_message):
        self.tree.delete(row_id)
        Messagebox.show_error(f"Failed to add client: {error_message}", "Error")

    def update_tree_row(self, row_id, ticker, company_name, prev_update_date, contents, press_release_links):
        """Update a row in the Treeview with the final fetched data."""
        self.tree.item(
            row_id,
            values=(ticker, company_name, prev_update_date, contents, press_release_links)
        )

    def scan_all_clients(self):
        """Trigger background fetch for each client."""
        for client in self.clients:
            self.executor.submit(self.update_tree_scan, client)
        self.show_all_clients()

    def update_tree_scan(self, client):
        """Refresh data for a single client in the background."""
        ticker = client.get("ticker")
        update = get_prev_update(ticker)
        if not update:
            return
        try:
            summary, date, pr_link, accession_number = update

            old_date = client.get("prev_update_date")
            # Check if anything changed
            something_changed = False
            if date != old_date:
                something_changed = True

            # Update fields
            client["contents"] = summary
            client["prev_update_date"] = date
            client["press_release_links"] = pr_link
            client["accession_number"] = accession_number

            # If changed, set has_updates to True, else False
            client["has_updates"] = something_changed
            self.save_clients()

        except Exception as e:
            print(f"Failed to get data for {client.get('ticker')}: {e}")
            return

    def delete_client(self):
        """Delete selected client(s) from the tree and from the list."""
        selected_item = self.tree.selection()
        if not selected_item:
            Messagebox.show_error("No client selected!", "Error")
            return

        for item in selected_item:
            values = self.tree.item(item)["values"]
            self.clients = [c for c in self.clients if c["ticker"] != values[0]]
            self.tree.delete(item)

        self.save_clients()

    def search_client(self):
        """Search for a client by ticker or company name."""
        search_term = self.ticker_entry.get().strip().lower()
        if not search_term:
            Messagebox.show_error("Enter a ticker or company name to search!", "Error")
            return

        matching = [
            c for c in self.clients
            if search_term in c["ticker"].lower() or search_term in c["company_name"].lower()
        ]

        self.tree.delete(*self.tree.get_children())
        for client in matching:
            self.insert_tree_row(client)

        if not matching:
            Messagebox.show_info("No clients found with that name!", "No Results")

    def show_all_clients(self):
        """Show all clients in the tree, highlighting the ones that have_updates."""
        self.tree.delete(*self.tree.get_children())
        for client in self.clients:
            self.insert_tree_row(client)

    def insert_tree_row(self, client):
        """
        Helper to insert a single client row into the Treeview,
        applying the 'updated' tag if has_updates == True.
        """
        tags = ()
        if client.get("has_updates"):
            tags = ("updated",)

        self.tree.insert(
            "", "end",
            values=(
                client["ticker"],
                client["company_name"],
                client["prev_update_date"],
                client["contents"],
                client["press_release_links"],
            ),
            tags=tags
        )

    def on_tree_double_click(self, event):
        """
        1) If double-click on 'contents' column (#4), show a pop-up with the full contents.
        2) If double-click on 'press_release_links' column (#5), open the URL in browser.
        """
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not item_id:
            return

        values = self.tree.item(item_id, "values")

        # 'Contents' column is #4, 'Press Release Links' is #5
        if column_id == "#4":
            contents = values[3]
            date = values[2]# index 3 in values
            self.show_full_contents_popup(contents,date)
        elif column_id == "#5":
            link = values[4]
            if link.startswith("http"):
                webbrowser.open(link)
            else:
                Messagebox.show_error(f"'{link}' is not a valid URL.", "Invalid Link")

    def show_full_contents_popup(self, contents,date):
        """Open a pop-up window to display the full contents in a scrolled text box."""
        popup = ttk.Toplevel(self.root)
        popup.title(f"Last Press Release Summary from {date}")
        popup.geometry("600x400")

        # A scrolled text widget for comfortable reading
        text_area = ScrolledText(popup, padding=10, autohide=True, bootstyle=INFO)
        text_area.pack(fill=ttk.BOTH, expand=True)

        # Insert the contents, then disable editing
        text_area.insert("1.0", contents)
        text_area.text.configure(state="disabled")
        for client in self.clients:
            if client["contents"] == contents:  # Match the content
                client["has_updates"] = False  # Reset the update flag
                self.save_clients()  # Save updated state
                self.show_all_clients()  # Refresh the Treeview to remove highlight
                break

    def load_clients(self):
        """Load client data from a JSON file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as file:
                self.clients = json.load(file)
        else:
            self.clients = []

    def save_clients(self):
        """Save client data to a JSON file."""
        with open(self.data_file, "w") as file:
            json.dump(self.clients, file, indent=4)

    def on_close(self):
        """Cleanup and exit."""
        # Cleanup the tmp_storage dir if needed
        for client in self.clients:
            client['has_updates'] = False

        self.save_clients()
        self.executor.shutdown(wait=False)
        self.root.destroy()


def main():
    # Create a ttkbootstrap window with a chosen modern theme.
    app_window = ttk.Window(themename="flatly")
    CRMApp(app_window)
    app_window.mainloop()


if __name__ == "__main__":
    main()
