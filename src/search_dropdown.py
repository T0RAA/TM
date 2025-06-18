import tkinter as tk
from tkinter import ttk
import threading
import time

class SpotifySearchDropdown:
    def __init__(self, parent, search_function, placeholder="Search...", width=40):
        self.parent = parent
        self.search_function = search_function
        self.placeholder = placeholder
        self.width = width
        self.search_results = []
        self.search_thread = None
        self.last_search_time = 0
        self.search_delay = 0.5  # Delay in seconds before searching
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Entry field
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self.frame, textvariable=self.entry_var, width=self.width)
        self.entry.pack(side=tk.LEFT, fill='x', expand=True)
        
        # Bind events
        self.entry.bind('<KeyRelease>', self.on_key_release)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        
        # Dropdown listbox
        self.dropdown_frame = ttk.Frame(self.parent)
        self.listbox = tk.Listbox(self.dropdown_frame, height=6, width=self.width)
        self.scrollbar = ttk.Scrollbar(self.dropdown_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill='y')
        
        # Bind listbox events
        self.listbox.bind('<Double-Button-1>', self.on_select)
        self.listbox.bind('<Return>', self.on_select)
        
        # Initially hide dropdown
        self.dropdown_frame.pack_forget()
        
    def on_key_release(self, event):
        """Handle key release events for search"""
        query = self.entry_var.get().strip()
        
        # Cancel previous search if still running
        if self.search_thread and self.search_thread.is_alive():
            self.last_search_time = time.time()
            return
            
        # Schedule new search
        self.last_search_time = time.time()
        self.search_thread = threading.Thread(target=self.delayed_search, args=(query,))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def delayed_search(self, query):
        """Perform search with delay to avoid too many API calls"""
        time.sleep(self.search_delay)
        
        # Check if this is still the most recent search
        if time.time() - self.last_search_time < self.search_delay:
            return
            
        if len(query) < 2:  # Don't search for very short queries
            self.parent.after(0, self.hide_dropdown)
            return
            
        try:
            # Perform the search
            print(f"Searching for: '{query}'")
            results = self.search_function(query)
            print(f"Search results: {len(results) if results else 0} items")
            self.parent.after(0, lambda: self.update_results(results))
        except Exception as e:
            print(f"Search error: {e}")
            self.parent.after(0, lambda: self.update_results([]))
            self.parent.after(0, self.hide_dropdown)
            
    def update_results(self, results):
        """Update the dropdown with search results"""
        self.search_results = results
        self.listbox.delete(0, tk.END)
        
        if not results:
            self.listbox.insert(tk.END, "No results found")
        else:
            for result in results:
                if isinstance(result, dict):
                    # Handle different result types
                    if 'name' in result and 'artist' in result:
                        # Track or album
                        display_text = f"{result['name']} - {result['artist']}"
                    elif 'name' in result:
                        # Artist
                        display_text = result['name']
                    else:
                        display_text = str(result)
                else:
                    # String (genre)
                    display_text = str(result)
                    
                self.listbox.insert(tk.END, display_text)
        
        if results:
            self.show_dropdown()
        else:
            self.hide_dropdown()
            
    def on_select(self, event):
        """Handle selection from dropdown"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.search_results):
                selected_item = self.search_results[index]
                self.entry_var.set(self.format_selection(selected_item))
                self.hide_dropdown()
                
    def format_selection(self, item):
        """Format the selected item for display in entry"""
        if isinstance(item, dict):
            if 'name' in item and 'artist' in item:
                return f"{item['name']} - {item['artist']}"
            elif 'name' in item:
                return item['name']
        return str(item)
        
    def on_focus_in(self, event):
        """Show dropdown when entry gets focus"""
        if self.search_results:
            self.show_dropdown()
            
    def on_focus_out(self, event):
        """Hide dropdown when entry loses focus"""
        # Use after to allow for selection clicks
        self.parent.after(150, self.hide_dropdown)
        
    def show_dropdown(self):
        """Show the dropdown listbox"""
        self.dropdown_frame.pack(fill='x', expand=True)
        
    def hide_dropdown(self):
        """Hide the dropdown listbox"""
        self.dropdown_frame.pack_forget()
        
    def get_value(self):
        """Get the current value from the entry"""
        return self.entry_var.get().strip()
        
    def set_value(self, value):
        """Set the value in the entry"""
        self.entry_var.set(value)
        
    def clear(self):
        """Clear the entry and hide dropdown"""
        self.entry_var.set("")
        self.hide_dropdown()
        self.search_results = [] 